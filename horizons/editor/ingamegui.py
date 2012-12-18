# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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
from horizons.editor.gui import SettingsTab
from horizons.ext.dummy import Dummy
from horizons.gui.tabs import TabWidget
from horizons.gui.util import LazyWidgetsDict
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.gui.widgets.minimap import Minimap
from horizons.util.python.callback import Callback


class IngameGui(object):

	def __init__(self, session, main_gui):
		self.session = session
		self.main_gui = main_gui

		# Mocks needed to act like the real IngameGui
		self.message_widget = Dummy
		self.display_game_speed = Dummy
		self.show_menu = Dummy
		self.hide_menu = Dummy

		self.widgets = LazyWidgetsDict({})
		minimap = self.widgets['minimap']
		minimap.position_technique = "right+0:top+0"

		icon = minimap.findChild(name="minimap")
		self.minimap = Minimap(icon,
		                       targetrenderer=horizons.globals.fife.targetrenderer,
		                       imagemanager=horizons.globals.fife.imagemanager,
		                       session=self.session,
		                       view=self.session.view)

		minimap.mapEvents({
			'zoomIn': self.session.view.zoom_in,
			'zoomOut': self.session.view.zoom_out,
			'rotateRight': Callback.ChainedCallbacks(self.session.view.rotate_right, self.minimap.rotate_right),
			'rotateLeft': Callback.ChainedCallbacks(self.session.view.rotate_left, self.minimap.rotate_left),
			'build': self._toggle_settings,
			'gameMenuButton' : self.main_gui.toggle_pause,
		})

		minimap.show()

		# Hide unnecessary buttons in hud
		for widget in ("speedUp", "speedDown", "destroy_tool", "diplomacyButton", "logbook"):
			self.widgets['minimap'].findChild(name=widget).hide()

		self._settings_visible = False

	def load(self, savegame):
		self.minimap.draw()

	def setup(self):
		"""Called after the world editor was initialized."""
		self._settings_tab = TabWidget(self, tabs=[SettingsTab(self.session.world_editor, self.session)])
		self._toggle_settings()

	def _toggle_settings(self):
		"""Display settings widget to change brush size and select tiles."""
		if self._settings_visible:
			self._settings_tab.hide()
		else:
			self._settings_tab.show()
			
		self._settings_visible = not self._settings_visible

	def minimap_to_front(self):
		"""Make sure the full right top gui is visible and not covered by some dialog"""
		self.widgets['minimap'].hide()
		self.widgets['minimap'].show()

	def show_save_map_dialog(self):
		"""Shows a dialog where the user can set the name of the saved map."""
		events = {
			OkButton.DEFAULT_NAME: self.save_map,
			CancelButton.DEFAULT_NAME: self._hide_save_map_dialog
		}
		self.main_gui.on_escape = self._hide_save_map_dialog
		dialog = self.widgets['save_map']
		name = dialog.findChild(name='map_name')
		name.text = u''
		dialog.mapEvents(events)
		name.capture(Callback(self.save_map))
		dialog.show()
		name.requestFocus()

	def _hide_save_map_dialog(self):
		"""Closes the map saving dialog."""
		self.main_gui.on_escape = self.main_gui.toggle_pause
		self.widgets['save_map'].hide()

	def save_map(self):
		"""Saves the map and hides the dialog."""
		name = self.widgets['save_map'].collectData('map_name')
		if re.match('^[a-zA-Z0-9_-]+$', name):
			self.session.save_map(name)
			self._hide_save_map_dialog()
		else:
			#xgettext:python-format
			message = _('Valid map names are in the following form: {expression}').format(expression='[a-zA-Z0-9_-]+')
			#xgettext:python-format
			advice = _('Try a name that only contains letters and numbers.')
			self.main_gui.show_error_popup(_('Error'), message, advice)

	def on_escape(self):
		pass

	def handle_key_press(self, action, evt):
		pass
