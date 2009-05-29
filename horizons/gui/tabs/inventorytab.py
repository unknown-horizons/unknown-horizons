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

class InventoryTab(TabInterface):

	def __init__(self, instance = None, widget = 'tab_widget/tab_stock.xml'):
		super(InventoryTab, self).__init__(widget = load_xml_translated(widget))
		self.instance = instance
		self.init_values()

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		print "Refresh..."
		if hasattr(self.instance, 'inventory'):
			self.widget.findChild(name='inventory').inventory = self.instance.inventory

	def show(self):
		self.instance.inventory.addChangeListener(self.refresh)
		super(InventoryTab, self).show()

	def hide(self):
		self.instance.inventory.removeChangeListener(self.refresh)
		super(InventoryTab, self).hide()

class ShipInventoryTab(InventoryTab):

	def __init__(self, instance = None):
		super(ShipInventoryTab, self).__init__(
			widget = 'tab_widget/tab_stock_ship.xml',
			instance = instance
		)
		events = {
			'trade': pychan.tools.callbackWithArguments(horizons.main.session.ingame_gui.show_menu, TradeWidget(instance))
		}
		self.widget.mapEvents(events)