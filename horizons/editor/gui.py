
# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from unittest import mock

import horizons.globals
from horizons.constants import EDITOR, GROUND, VIEW
from horizons.gui.keylisteners import IngameKeyListener, KeyConfig
from horizons.gui.modules import HelpDialog, PauseMenu, SelectSavegameDialog
from horizons.gui.mousetools import SelectionTool, TileLayingTool
from horizons.gui.tabs import TabWidget
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.messagewidget import MessageWidget
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.windows import WindowManager
from horizons.messaging import ZoomChanged
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.util.living import LivingObject, livingProperty
from horizons.util.loaders.tilesetloader import TileSetLoader
from horizons.util.python.callback import Callback


class IngameGui(LivingObject):
	minimap = livingProperty()
	keylistener = livingProperty()
	message_widget = livingProperty()

	def __init__(self, session):
		self.session = session

		self.which = None
		self.cursor = None
		self.coordinates_tooltip = None
		self.keylistener = IngameKeyListener(self.session)
		# used by NavigationTool
		LastActivePlayerSettlementManager.create_instance(self.session)

		# Mocks needed to act like the real IngameGui
		self.show_menu = mock.Mock()
		self.hide_menu = mock.Mock()
		# this is necessary for message_widget to work
		self.logbook = mock.Mock()

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
			'rotateRight': Callback.ChainedCallbacks(self.session.view.rotate_right, self.minimap.update_rotation),
			'rotateLeft': Callback.ChainedCallbacks(self.session.view.rotate_left, self.minimap.update_rotation),
			'gameMenuButton': self.toggle_pause,
		})

		self.mainhud.show()
		ZoomChanged.subscribe(self._update_zoom)

		# Hide unnecessary buttons in hud
		for widget in ("build", "speedUp", "speedDown", "destroy_tool", "diplomacyButton", "logbook"):
			self.mainhud.findChild(name=widget).hide()

		self.windows = WindowManager()
		self.message_widget = MessageWidget(self.session)
		self.pausemenu = PauseMenu(self.session, self, self.windows, in_editor_mode=True)
		self.help_dialog = HelpDialog(self.windows)

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
		ZoomChanged.unsubscribe(self._update_zoom)

		if self.cursor:
			self.cursor.remove()
			self.cursor.end()
			self.cursor = None

		super().end()

	def handle_selection_group(self, num, ctrl_pressed):
		# Someday, maybe cool stuff will be possible here.
		# That day is not today, I'm afraid.
		pass

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
		window = SelectSavegameDialog('editor-save', self.windows)
		savegamename = self.windows.open(window)
		if savegamename is None:
			return False # user aborted dialog
		success = self.session.save(savegamename)
		if success:
				self.message_widget.add('SAVED_GAME')

	def on_escape(self):
		pass

	def on_key_press(self, action, evt):
		_Actions = KeyConfig._Actions
		if action == _Actions.QUICKSAVE:
			self.session.quicksave()
		if action == _Actions.ESCAPE:
			if self.windows.visible:
				self.windows.on_escape()
			elif hasattr(self.cursor, 'on_escape'):
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
		self.which = which

	def _update_zoom(self, message):
		"""Enable/disable zoom buttons"""
		in_icon = self.mainhud.findChild(name='zoomIn')
		out_icon = self.mainhud.findChild(name='zoomOut')
		if message.zoom == VIEW.ZOOM_MIN:
			out_icon.set_inactive()
		else:
			out_icon.set_active()
		if message.zoom == VIEW.ZOOM_MAX:
			in_icon.set_inactive()
		else:
			in_icon.set_active()


class SettingsTab(TabInterface):
	widget = 'editor_settings.xml'
	# SettingsTab needs access widget upon init, thus disable lazy_loading
	lazy_loading = False

	def __init__(self, world_editor, ingame_gui):
		super().__init__(widget=self.widget)

		self._world_editor = world_editor
		self._current_tile = 'sand'
		self._ingame_gui = ingame_gui
		self._tile_selected = 0

		# Brush size
		for i in range(EDITOR.MIN_BRUSH_SIZE, EDITOR.MAX_BRUSH_SIZE + 1):
			b = self.widget.findChild(name='size_{:d}'.format(i))
			b.capture(Callback(self._change_brush_size, i))

		# Activate radio button for default brush size
		self._change_brush_size(self._world_editor.brush_size)

		# Tile selection
		for tile_type in ('default_land', 'sand', 'shallow_water', 'water'):
			image = self.widget.findChild(name=tile_type)
			tile = getattr(GROUND, tile_type.upper())
			image.up_image = self._get_tile_image(tile)
			image.size = image.min_size = image.max_size = (64, 32)
			image.capture(Callback(self._set_cursor_tile, tile))

		self.widget.mapEvents({
			self.widget.name + '/mouseEntered/cursor': self._cursor_inside,
			self.widget.name + '/mouseExited/cursor': self._cursor_outside,
		})

		self._ingame_gui.mainhud.mapEvents({
			self._ingame_gui.mainhud.name + '/mouseEntered/cursor': self._cursor_inside,
			self._ingame_gui.mainhud.name + '/mouseExited/cursor': self._cursor_outside,
		})

	def _set_cursor_tile(self, tile):
		self._tile_selected = 1
		self._current_tile = tile
		self._ingame_gui.set_cursor('tile_layer', self._current_tile)

	def _cursor_inside(self):
		horizons.globals.fife.set_cursor_image('default')

	def _cursor_outside(self):
		if (self._tile_selected == 1 or self._ingame_gui.which == 'tile_layer'):
			self._tile_selected = 0
			self._ingame_gui.set_cursor('tile_layer', self._current_tile)
		else:
			self._ingame_gui.set_cursor('default')

	def _get_tile_image(self, tile):
		# TODO TileLayingTool does almost the same thing, perhaps put this in a better place
		tile_sets = TileSetLoader.get_sets()

		ground_id, action_id, rotation = tile
		set_id = horizons.globals.db.get_random_tile_set(ground_id)
		return list(tile_sets[set_id][action_id][rotation].keys())[0]

	def _change_brush_size(self, size):
		"""Change the brush size and update the gui."""
		images = {
		  'box_highlighted': 'content/gui/icons/ship/smallbutton_a.png',
		  'box': 'content/gui/icons/ship/smallbutton.png',
		}

		b = self.widget.findChild(name='size_{:d}'.format(self._world_editor.brush_size))
		b.up_image = images['box']

		self._world_editor.brush_size = size
		b = self.widget.findChild(name='size_{:d}'.format(self._world_editor.brush_size))
		b.up_image = images['box_highlighted']
