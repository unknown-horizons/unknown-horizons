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

from fife.extensions import pychan

from tabinterface import TabInterface
from horizons.gui.widgets.tradewidget import TradeWidget

class InventoryTab(TabInterface):

	def __init__(self, instance = None, widget = 'island_inventory.xml', \
	             icon_path='content/gui/icons/tabwidget/common/inventory_%s.png'):
		super(InventoryTab, self).__init__(widget = widget)
		self.instance = instance
		self.init_values()
		self.button_up_image = icon_path % 'u'
		self.button_active_image = icon_path % 'a'
		self.button_down_image = icon_path % 'd'
		self.button_hover_image = icon_path % 'h'
		self.tooltip = _("Inventory")
		self.widget.child_finder('inventory').init(self.instance.session.db, \
		                                           self.instance.inventory)

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self.widget.child_finder('inventory').update()

	def show(self):
		if not self.instance.inventory.has_change_listener(self.refresh):
			self.instance.inventory.add_change_listener(self.refresh)
		super(InventoryTab, self).show()

	def hide(self):
		if self.instance.inventory.has_change_listener(self.refresh):
			self.instance.inventory.remove_change_listener(self.refresh)
		super(InventoryTab, self).hide()

class ShipInventoryTab(InventoryTab):

	def __init__(self, instance = None):
		super(ShipInventoryTab, self).__init__(
			widget = 'ship_inventory.xml',
			icon_path='content/gui/icons/tabwidget/common/inventory_%s.png',
			instance = instance
		)
#		self.button_up_image = 'content/gui/icons/tabwidget/common/inventory_u.png'
	#	self.button_active_image = 'content/gui/icons/tabwidget/common/inventory_a.png'
		#self.button_down_image = 'content/gui/icons/tabwidget/common/inventory_d.png'
#		self.button_hover_image = 'content/gui/icons/tabwidget/common/inventory_h.png'
		self.tooltip = _("Ship inventory")

	def refresh(self):
		branches = self.instance.session.world.get_branch_offices(self.instance.position, self.instance.radius, self.instance.owner)
		if len(branches) > 0:
			events = { 'trade': pychan.tools.callbackWithArguments(self.instance.session.ingame_gui.show_menu, TradeWidget(self.instance)) }
			self.widget.mapEvents(events)
			self.widget.findChild(name='bg_button').set_active()
			self.widget.findChild(name='trade').set_active()
		else:
			events = { 'trade': None }
			self.widget.mapEvents(events)
			self.widget.findChild(name='bg_button').set_inactive()
			self.widget.findChild(name='trade').set_inactive()
		super(ShipInventoryTab, self).refresh()

	def show(self):
		if not self.instance.has_change_listener(self.refresh):
			self.instance.add_change_listener(self.refresh)
		super(ShipInventoryTab, self).show()

	def hide(self):
		if self.instance.has_change_listener(self.refresh):
			self.instance.remove_change_listener(self.refresh)
		super(ShipInventoryTab, self).hide()
