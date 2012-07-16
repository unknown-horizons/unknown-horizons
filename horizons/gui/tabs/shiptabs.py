# -*- coding: utf-8 -*-
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

import weakref

from horizons.constants import BUILDINGS, WEAPONS
from horizons.command.uioptions import EquipWeaponFromInventory, UnequipWeaponToInventory
from horizons.entities import Entities
from horizons.gui.tabs import OverviewTab, TradeTab
from horizons.gui.widgets.routeconfig import RouteConfig
from horizons.util import Callback
from horizons.component.storagecomponent import StorageComponent
from horizons.component.selectablecomponent import SelectableComponent


class ShipOverviewTab(OverviewTab):
	def __init__(self, instance, widget='overview_trade_ship.xml',
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png'):
		super(ShipOverviewTab, self).__init__(instance, widget, icon_path)
		self.widget.child_finder('inventory').init(self.instance.session.db, self.instance.get_component(StorageComponent).inventory)
		self.helptext = _("Ship overview")

	def _configure_route(self):
		self.route_menu = RouteConfig(self.instance)
		self.route_menu.toggle_visibility()

	def _refresh_found_settlement_button(self, events):
		island_without_player_settlement_found = False
		helptext = _("The ship needs to be close to an island to found a settlement.")
		for island in self.instance.session.world.get_islands_in_radius(self.instance.position, self.instance.radius):
			if not any(settlement.owner.is_local_player for settlement in island.settlements):
				island_without_player_settlement_found = True
			else:
				helptext = _("You already have a settlement on this island.")

		if island_without_player_settlement_found:
			events['found_settlement'] = Callback(self.instance.session.ingame_gui._build,
			                                      BUILDINGS.WAREHOUSE,
			                                      weakref.ref(self.instance) )
			self.widget.child_finder('found_settlement_bg').set_active()
			self.widget.child_finder('found_settlement').set_active()
			self.widget.child_finder('found_settlement').helptext = _("Build settlement")
		else:
			events['found_settlement'] = None
			self.widget.child_finder('found_settlement_bg').set_inactive()
			self.widget.child_finder('found_settlement').set_inactive()
			self.widget.child_finder('found_settlement').helptext = helptext

		cb = Callback( self.instance.session.ingame_gui.resource_overview.set_construction_mode,
		               self.instance,
		               Entities.buildings[BUILDINGS.WAREHOUSE].costs)
		events['found_settlement/mouseEntered'] = cb

		cb1 = Callback(self.instance.session.ingame_gui.resource_overview.close_construction_mode)
		cb2 = Callback(self.widget.child_finder('found_settlement').hide_tooltip)
		#TODO the tooltip should actually hide on its own. Ticket #1096
		cb = Callback.ChainedCallbacks(cb1, cb2)
		events['found_settlement/mouseExited'] = cb

	def _refresh_trade_button(self, events):
		warehouses = self.instance.get_tradeable_warehouses()

		if warehouses:
			if warehouses[0].owner is self.instance.owner:
				helptext = _('Load/Unload')
			else:
				helptext = _('Buy/Sell')
			events['trade'] = Callback(self.instance.get_component(SelectableComponent).show_menu, TradeTab)
			self.widget.findChild(name='trade_bg').set_active()
			self.widget.findChild(name='trade').set_active()
			self.widget.findChild(name='trade').helptext = helptext
		else:
			events['trade'] = None
			self.widget.findChild(name='trade_bg').set_inactive()
			self.widget.findChild(name='trade').set_inactive()
			self.widget.findChild(name='trade').helptext = _('Too far from the nearest tradeable warehouse')

	def _refresh_combat(self): # no combat
		def click_on_cannons(button):
			button.button.capture(Callback(
			  self.instance.session.gui.show_popup,
			  _("Cannot equip trade ship with weapons"),
			  _("It is not possible to equip a trade ship with weapons.")
			))
		self.widget.findChild(name='inventory').apply_to_buttons(click_on_cannons, lambda b: b.res_id == WEAPONS.CANNON)

	def refresh(self):
		# show rename when you click on name
		events = {
			'name': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.instance),
			'configure_route/mouseClicked': Callback(self._configure_route)
		}

		self._refresh_found_settlement_button(events)
		self._refresh_trade_button(events)
		self.widget.mapEvents(events)

		self.widget.child_finder('inventory').update()
		self._refresh_combat()
		super(ShipOverviewTab, self).refresh()


class FightingShipOverviewTab(ShipOverviewTab):
	has_stance = True
	def __init__(self, instance, widget='overview_war_ship.xml',
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png'):
		super(FightingShipOverviewTab, self).__init__(instance, widget, icon_path)


		#create weapon inventory, needed only in gui for inventory widget
		self.weapon_inventory = self.instance.get_weapon_storage()
		self.widget.findChild(name='weapon_inventory').init(self.instance.session.db, self.weapon_inventory)

	def _refresh_combat(self):
		def apply_equip(button):
			button.button.helptext = _("Equip weapon")
			button.button.capture(Callback(self.equip_weapon, button.res_id))

		def apply_unequip(button):
			button.button.helptext = _("Unequip weapon")
			button.button.capture(Callback(self.unequip_weapon, button.res_id))

		self.widget.findChild(name='weapon_inventory').apply_to_buttons(apply_unequip, lambda b: b.res_id == WEAPONS.CANNON)
		self.widget.findChild(name='inventory').apply_to_buttons(apply_equip, lambda b: b.res_id == WEAPONS.CANNON)

	def equip_weapon(self, weapon_id):
		if EquipWeaponFromInventory(self.instance, weapon_id, 1).execute(self.instance.session) == 0:
			self.weapon_inventory.alter(weapon_id, 1)
		self.widget.child_finder('weapon_inventory').update()
		self.refresh()

	def unequip_weapon(self, weapon_id):
		if UnequipWeaponToInventory(self.instance, weapon_id, 1).execute(self.instance.session) == 0:
			self.weapon_inventory.alter(weapon_id, -1)
		self.widget.child_finder('weapon_inventory').update()
		self.refresh()

	def on_instance_removed(self):
		self.weapon_inventory = None
		super(FightingShipOverviewTab, self).on_instance_removed()

class TraderShipOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(TraderShipOverviewTab, self).__init__(
			widget = 'overview_tradership.xml',
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png',
			instance = instance)
		self.helptext = _("Ship overview")

class EnemyShipOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(EnemyShipOverviewTab, self).__init__(
			widget = 'overview_enemyunit.xml',
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png',
			instance = instance)
		self.widget.findChild(name="headline").text = self.instance.owner.name
		self.helptext = _("Ship overview")
