# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

from tabinterface import TabInterface
from horizons.util.python.roman_numerals import int_to_roman

class BuildTab(TabInterface):
	last_active_build_tab = None
	def __init__(self, tabindex = 0, events = {}):
		super(BuildTab, self).__init__(widget = 'buildtab_increment' + str(tabindex) + '.xml')
		self.init_values()
		icon_path = 'content/gui/icons/tabwidget/buildmenu/level%s_%s.png'
		self.widget.mapEvents(events)
		self.button_up_image = icon_path % (tabindex,'u')
		self.button_active_image = icon_path % (tabindex,'a')
		self.button_down_image = icon_path % (tabindex,'d')
		self.button_hover_image = icon_path % (tabindex,'h')
		self.tooltip = unicode(_("Increment")+" "+int_to_roman(tabindex+1))
		self.tabindex = tabindex

	def refresh(self):
		pass

	def show(self):
		self.__class__.last_active_build_tab = self.tabindex
		super(BuildTab, self).show()

	def hide(self):
		super(BuildTab, self).hide()
