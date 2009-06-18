# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
import weakref
import pychan
import horizons.main
from tabinterface import TabInterface
from horizons.i18n import load_xml_translated
from horizons.gui.tradewidget import TradeWidget

class BuildTab(TabInterface):
	def __init__(self, tabindex = 0, events = {}):
		super(BuildTab, self).__init__(widget = 'build_menu/hud_build_tab' + str(tabindex) + '.xml')
		self.widget.mapEvents(events)
		self.widget.stylize('menu_black')
		self.widget.findChild(name='headline').stylize('headline') # style definition for headline

	def refresh(self):
		pass

	def show(self):
		super(BuildTab, self).show()

	def hide(self):
		super(BuildTab, self).hide()