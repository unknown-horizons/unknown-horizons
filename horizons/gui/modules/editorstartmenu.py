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

import horizons.main

from horizons.gui.util import load_uh_widget
from horizons.savegamemanager import SavegameManager

class EditorStartMenu(object):
	def __init__(self, parent, from_main_menu):
		self._from_main_menu = from_main_menu
		self.parent = parent
		self._gui = load_uh_widget('editor_start_menu.xml')
		self._right_side = EditorSelectMapWidget(self, self._gui.findChild(name='right_side'))
		self._old_on_escape = None

	def show(self):
		self._right_side.show()
		self._gui.show()

		events = {}
		events['okay/mouseClicked'] = self.act
		events['cancel/mouseClicked'] = self.cancel
		self._gui.mapEvents(events)
		
		self._old_current_widget = self.parent.current
		self._old_on_escape = self.parent.on_escape 
		self.parent.on_escape = self.cancel

	def cancel(self):
		self.hide()
		if self._from_main_menu:
			self.parent.show_main()
		else:
			self.parent.on_escape()

	def hide(self):
		self._right_side.hide()
		self._gui.hide()
		self.parent.current = self._old_current_widget
		self.parent.on_escape = self._old_on_escape

	def act(self):
		self._right_side.act()

	def findChild(self, **kwargs):
		return self._gui.findChild(**kwargs)


class EditorSelectMapWidget(object):
	def __init__(self, parent, parent_widget):
		self.parent = parent
		self._parent_widget = parent_widget
		self._gui = load_uh_widget('editor_select_map.xml')
		self._map_data = None

	def show(self):
		self._map_data = SavegameManager.get_maps()
		self._gui.distributeInitialData({'map_list': self._map_data[1]})
		self._parent_widget.addChild(self._gui)

	def hide(self):
		self._parent_widget.removeAllChildren()

	def act(self):
		selected_map_index = self._gui.collectData('map_list')
		if selected_map_index == -1:
			# No map selected yet => select first available one
			self._gui.distributeData({'map_list': 0})

		self.parent.hide()
		self.parent.parent.show_loading_screen()
		horizons.main.edit_map(self._map_data[0][selected_map_index])
