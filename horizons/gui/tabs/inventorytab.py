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

from tabinterface import TabInterface
from horizons.i18n import load_xml_translated

class InventoryTab(TabInterface):

	def __init__(self, instance = None):
		super(InventoryTab, self).__init__()
		self.widget = load_xml_translated('tab_widget/tab_stock.xml')
		self.instance = instance
		self.init_values()

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		if hasattr(self.instance, 'inventory'):
			self.widget.findChild(name='inventory').inventory = self.instance.inventory