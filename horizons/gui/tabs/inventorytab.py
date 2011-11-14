# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.gui.tabs.tabinterface import TabInterface
from horizons.gui.widgets.tradewidget import TradeWidget
from horizons.gui.widgets.internationaltradewidget import InternationalTradeWidget
from horizons.gui.widgets.routeconfig import RouteConfig
from horizons.util import Callback
from horizons.scheduler import Scheduler
from horizons.constants import WEAPONS
from horizons.command.uioptions import EquipWeaponFromInventory, UnequipWeaponToInventory

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
		self.tooltip = _("Settlement inventory")
		self.widget.child_finder('inventory').init(self.instance.session.db, \
		                                           self.instance.inventory)

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self.widget.child_finder('inventory').update()

	def show(self):
		Scheduler().add_new_object(self.refresh, self, run_in=1, loops=-1, loop_interval=16)
		super(InventoryTab, self).show()

	def hide(self):
		Scheduler().rem_call(self, self.refresh)
		super(InventoryTab, self).hide()

class ShipInventoryTab(InventoryTab):

	def __init__(self, instance = None, widget = 'ship_inventory.xml',
			icon_path = 'content/gui/icons/tabwidget/common/inventory_%s.png'):
		#if no other widget or icon path are passed via inheritance, use default ones
		super(ShipInventoryTab, self).__init__(instance, widget, icon_path)
		self.tooltip = _("Ship inventory")

	def configure_route(self):
		self.route_menu = RouteConfig(self.instance)
		self.route_menu.toggle_visibility()

	def refresh(self):
		session = self.instance.session
		branches = session.world.get_branch_offices(self.instance.position, \
			self.instance.radius, self.instance.owner, True)
		events = {}

		events['configure_route/mouseClicked'] = Callback(self.configure_route)

		# TODO: use a better way to decide which label should be shown
		if len(branches) > 0:
			if branches[0].owner is self.instance.owner:
				wdg = TradeWidget(self.instance)
				text = _('Load/Unload:')
			else:
				wdg = InternationalTradeWidget(self.instance)
				text = _('Buy/Sell:')
			events['trade'] = Callback(session.ingame_gui.show_menu, wdg)
			self.widget.findChild(name='load_unload_label').text = text
			self.widget.findChild(name='bg_button').set_active()
			self.widget.findChild(name='trade').set_active()
		else:
			events['trade'] = None
			self.widget.findChild(name='bg_button').set_inactive()
			self.widget.findChild(name='trade').set_inactive()

		self._refresh_combat()

		self.widget.mapEvents(events)
		super(ShipInventoryTab, self).refresh()

	def _refresh_combat(self): # no combat
		def click_on_cannons(button):
			button.button.capture(Callback(
			  self.instance.session.gui.show_popup,
			  _("Cannot equip trade ship with weapons"),
			  _("It is not possible to equip a trade ship with weapons.")
			))
		self.widget.findChild(name='inventory').apply_to_buttons(click_on_cannons, lambda b: b.res_id == WEAPONS.CANNON)


	def show(self):
		if not self.instance.has_change_listener(self.refresh):
			self.instance.add_change_listener(self.refresh)
		super(ShipInventoryTab, self).show()

	def hide(self):
		if self.instance.has_change_listener(self.refresh):
			self.instance.remove_change_listener(self.refresh)
		super(ShipInventoryTab, self).hide()

class FightingShipInventoryTab(ShipInventoryTab):

	def __init__(self, instance = None):
		widget = 'fighting_ship_inventory.xml'
		super(FightingShipInventoryTab, self).__init__(instance, widget)
		#create weapon inventory, needed only in gui for inventory widget
		self.weapon_inventory = self.instance.get_weapon_storage()
		self.widget.findChild(name='weapon_inventory').init(self.instance.session.db, \
			self.weapon_inventory)

	def _refresh_combat(self):
		#TODO system for getting equipable weapons
		def apply_equip(button):
			button.button.tooltip = _("Equip weapon")
			button.button.capture(Callback(self.equip_weapon, button.res_id))
		def apply_unequip(button):
			button.button.tooltip = _("Unequip weapon")
			button.button.capture(Callback(self.unequip_weapon, button.res_id))
		self.widget.findChild(name='weapon_inventory').apply_to_buttons(apply_unequip, lambda b: b.res_id == WEAPONS.CANNON)
		self.widget.findChild(name='inventory').apply_to_buttons(apply_equip, lambda b: b.res_id == WEAPONS.CANNON)

	def equip_weapon(self, weapon_id):
		if EquipWeaponFromInventory(self.instance, weapon_id, 1).execute(self.instance.session) == 0:
			self.weapon_inventory.alter(weapon_id, 1)
		self.widget.child_finder('weapon_inventory').update()

	def unequip_weapon(self, weapon_id):
		if UnequipWeaponToInventory(self.instance, weapon_id, 1).execute(self.instance.session) == 0:
			self.weapon_inventory.alter(weapon_id, -1)
		self.widget.child_finder('weapon_inventory').update()

