# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import re

import horizons.globals
from horizons.constants import GROUND, VIEW
from horizons.ext.dummy import Dummy
from horizons.gui.keylisteners import IngameKeyListener, KeyConfig
from horizons.gui.modules import PauseMenu, HelpDialog
from horizons.gui.mousetools import SelectionTool, TileLayingTool
from horizons.gui.tabs import TabWidget
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.gui.widgets.messagewidget import MessageWidget
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.windows import WindowManager, Window
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.util.living import LivingObject, livingProperty
from horizons.util.loaders.tilesetloader import TileSetLoader
from horizons.util.python.callback import Callback


class IngameGui(LivingObject):
	minimap = livingProperty()
	keylistener = livingProperty()
	message_widget = livingProperty()

	def __init__(self, session, main_gui):
		self.session = session
		self.main_gui = main_gui

		self.cursor = None
		self.coordinates_tooltip = None
		self.keylistener = IngameKeyListener(self.session)
		# used by NavigationTool
		LastActivePlayerSettlementManager.create_instance(self.session)

		# Mocks needed to act like the real IngameGui
		self.show_menu = Dummy
		self.hide_menu = Dummy
		# a logbook Dummy is necessary for message_widget to work
		self.logbook = Dummy

		self.mainhud = load_uh_widget('minimap.xml')
		self.mainhud.position_technique = "right+0:top+0"

		icon = self.mainhud.findChild(name="minimap")
		self.minimap = Minimap(icon,
		                       targetrenderer=horizons.globals.fife.targetrenderer,
		                       imagemanager=horizons.globals.fife.imagemanager,
		                       session=self.session,
		                       view=self.session.view)

		self.mainhud.mapEvents({
			'zoomIn': self.session.view.zoom_in,
			'zoomOut': self.session.view.zoom_out,
			'rotateRight': Callback.ChainedCallbacks(self.session.view.rotate_right, self.minimap.rotate_right),
			'rotateLeft': Callback.ChainedCallbacks(self.session.view.rotate_left, self.minimap.rotate_left),
			'gameMenuButton': self.toggle_pause,
		})

		self.mainhud.show()
		self.session.view.add_change_listener(self._update_zoom)

		# Hide unnecessary buttons in hud
		for widget in ("build", "speedUp", "speedDown", "destroy_tool", "diplomacyButton", "logbook"):
			self.mainhud.findChild(name=widget).hide()

		self.windows = WindowManager()
		self.message_widget = MessageWidget(self.session)
		self.save_map_dialog = SaveMapDialog(self.session, self.windows)
		self.pausemenu = PauseMenu(self.session, self, self.windows, in_editor_mode=True)
		self.help_dialog = HelpDialog(self.windows, session=self.session)

	def end(self):
		self.mainhud.mapEvents({
			'zoomIn': None,
			'zoomOut': None,
			'rotateRight': None,
			'rotateLeft': None,
			'gameMenuButton': None
		})
		self.mainhud.hide()
		self.mainhud = None
		self._settings_tab.hide()
		self._settings_tab = None

		self.windows.close_all()
		self.minimap = None
		self.keylistener = None
		LastActivePlayerSettlementManager().remove()
		LastActivePlayerSettlementManager.destroy_instance()
		self.session.view.remove_change_listener(self._update_zoom)

		if self.cursor:
			self.cursor.remove()
			self.cursor.end()
			self.cursor = None

		super(IngameGui, self).end()

	def toggle_pause(self):
		self.windows.toggle(self.pausemenu)

	def toggle_help(self):
		self.windows.toggle(self.help_dialog)

	def load(self, savegame):
		self.minimap.draw()

		self.cursor = SelectionTool(self.session)

	def setup(self):
		"""Called after the world editor was initialized."""
		self._settings_tab = TabWidget(self, tabs=[SettingsTab(self.session.world_editor, self)])
		self._settings_tab.show()

	def minimap_to_front(self):
		"""Make sure the full right top gui is visible and not covered by some dialog"""
		self.mainhud.hide()
		self.mainhud.show()

	def show_save_map_dialog(self):
		"""Shows a dialog where the user can set the name of the saved map."""
		self.windows.show(self.save_map_dialog)

	def on_escape(self):
		pass

	def on_key_press(self, action, evt):
		_Actions = KeyConfig._Actions
		if action == _Actions.QUICKSAVE:
			self.session.quicksave()
		if action == _Actions.ESCAPE:
			if self.windows.visible:
				self.windows.on_escape()
			elif not isinstance(self.cursor, SelectionTool):
				self.cursor.on_escape()
			else:
				self.toggle_pause()
		elif action == _Actions.HELP:
			self.toggle_help()
		else:
			return False
		return True

	def set_cursor(self, which='default', *args, **kwargs):
		"""Sets the mousetool (i.e. cursor).
		This is done here for encapsulation and control over destructors.
		Further arguments are passed to the mouse tool constructor.
		"""
		self.cursor.remove()
		klass = {
			'default': SelectionTool,
			'tile_layer': TileLayingTool
		}[which]
		self.cursor = klass(self.session, *args, **kwargs)

	def _update_zoom(self):
		"""Enable/disable zoom buttons"""
		zoom = self.session.view.get_zoom()
		in_icon = self.mainhud.findChild(name='zoomIn')
		out_icon = self.mainhud.findChild(name='zoomOut')
		if zoom == VIEW.ZOOM_MIN:
			out_icon.set_inactive()
		else:
			out_icon.set_active()
		if zoom == VIEW.ZOOM_MAX:
			in_icon.set_inactive()
		else:
			in_icon.set_active()


class SettingsTab(TabInterface):
	widget = 'editor_settings.xml'

	def __init__(self, world_editor, ingame_gui):
		super(SettingsTab, self).__init__(widget=self.widget)

		self._world_editor = world_editor

		# Brush size
		for i in range(1, 4):
			b = self.widget.findChild(name='size_%d' % i)
			b.capture(Callback(self._change_brush_size, i))

		# Activate radio button for default brush size
		self._change_brush_size(self._world_editor.brush_size)

		# Tile selection
		for tile_type in ('default_land', 'sand', 'shallow_water', 'water'):
			image = self.widget.findChild(name=tile_type)
			tile = getattr(GROUND, tile_type.upper())
			image.up_image = self._get_tile_image(tile)
			image.size = image.min_size = image.max_size = (64, 32)
			image.capture(Callback(ingame_gui.set_cursor, 'tile_layer', tile))

	def _get_tile_image(self, tile):
		# TODO TileLayingTool does almost the same thing, perhaps put this in a better place
		tile_sets = TileSetLoader.get_sets()

		ground_id, action_id, rotation = tile
		set_id = horizons.globals.db.get_random_tile_set(ground_id)
		return tile_sets[set_id][action_id][rotation].keys()[0]

	def _change_brush_size(self, size):
		"""Change the brush size and update the gui."""
		images = {
		  'box_highlighted': 'content/gui/icons/ship/smallbutton_a.png',
		  'box': 'content/gui/icons/ship/smallbutton.png',
		}

		b = self.widget.findChild(name='size_%d' % self._world_editor.brush_size)
		b.up_image = images['box']

		self._world_editor.brush_size = size
		b = self.widget.findChild(name='size_%d' % self._world_editor.brush_size)
		b.up_image = images['box_highlighted']


class SaveMapDialog(Window):
	"""Shows a dialog where the user can set the name of the saved map."""

	def __init__(self, session, windows):
		super(SaveMapDialog, self).__init__(windows)

		self._session = session
		self._widget = load_uh_widget('save_map.xml')

		name = self._widget.findChild(name='map_name')
		name.text = u''
		name.capture(self._do_save)

		events = {
			OkButton.DEFAULT_NAME: self._do_save,
			CancelButton.DEFAULT_NAME: self._windows.close,
		}
		self._widget.mapEvents(events)

	def show(self):
		self._widget.show()
		self._widget.findChild(name='map_name').requestFocus()

	def hide(self):
		self._widget.hide()

	def _do_save(self):
		name = self._widget.collectData('map_name')
		regex = r'[a-zA-Z0-9_-]+'
		if re.match('^' + regex + '$', name):
			self._session.save(name)
			self._windows.close()
		else:
			#xgettext:python-format
			message = _('Valid map names are in the following form: {expression}').format(expression=regex)
			advice = _('Try a name that only contains letters and numbers.')
			self._windows.show_error_popup(_('Invalid name'), message, advice)
