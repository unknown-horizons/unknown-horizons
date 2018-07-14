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

import weakref

from horizons.command.uioptions import EquipWeaponFromInventory, UnequipWeaponToInventory
from horizons.component.selectablecomponent import SelectableComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS, WEAPONS
from horizons.entities import Entities
from horizons.gui.widgets.routeconfig import RouteConfig
from horizons.i18n import gettext as T, gettext_lazy as LazyT
from horizons.util.python.callback import Callback

from .overviewtab import OverviewTab
from .tradetab import TradeTab


class ShipOverviewTab(OverviewTab):
	widget = 'overview_ship.xml'
	icon_path = 'icons/tabwidget/ship/ship_inv'
	helptext = LazyT("Ship overview")

	def init_widget(self):
		super().init_widget()
		self.ship_inv = self.instance.get_component(StorageComponent).inventory
		self.widget.child_finder('inventory').init(self.instance.session.db, self.ship_inv)

		# FIXME having to access the WindowManager this way is pretty ugly
		self._windows = self.instance.session.ingame_gui.windows
		self.route_menu = RouteConfig(self._windows, self.instance)

	def _configure_route(self):
		self._windows.toggle(self.route_menu)

	def _refresh_found_settlement_button(self, events):
		island_without_player_settlement_found = False
		helptext = T("The ship needs to be close to an island to found a settlement.")
		for island in self.instance.session.world.get_islands_in_radius(self.instance.position, self.instance.radius):
			if not any(settlement.owner.is_local_player for settlement in island.settlements):
				island_without_player_settlement_found = True
			else:
				helptext = T("You already have a settlement on this island.")

		if island_without_player_settlement_found:
			events['found_settlement'] = Callback(self.instance.session.ingame_gui._build,
			                                      BUILDINGS.WAREHOUSE,
			                                      weakref.ref(self.instance))
			self.widget.child_finder('found_settlement_bg').set_active()
			self.widget.child_finder('found_settlement').set_active()
			self.widget.child_finder('found_settlement').helptext = T("Build settlement")
		else:
			events['found_settlement'] = None
			self.widget.child_finder('found_settlement_bg').set_inactive()
			self.widget.child_finder('found_settlement').set_inactive()
			self.widget.child_finder('found_settlement').helptext = helptext

		cb = Callback(self.instance.session.ingame_gui.resource_overview.set_construction_mode,
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
				helptext = T('Load/Unload')
			else:
				helptext = T('Buy/Sell')
			events['trade'] = Callback(self.instance.get_component(SelectableComponent).show_menu, TradeTab)
			self.widget.findChild(name='trade_bg').set_active()
			self.widget.findChild(name='trade').set_active()
			self.widget.findChild(name='trade').helptext = helptext
		else:
			events['trade'] = None
			self.widget.findChild(name='trade_bg').set_inactive()
			self.widget.findChild(name='trade').set_inactive()
			self.widget.findChild(name='trade').helptext = T('Too far from the nearest tradeable warehouse')

	def _refresh_combat(self): # no combat
		def click_on_cannons(button):
			button.button.capture(Callback(
			  self.instance.session.ingame_gui.open_popup,
			  T("Cannot equip trade ship with weapons"),
			  T("It is not possible to equip a trade ship with weapons.")
			))
		self.widget.findChild(name='inventory').apply_to_buttons(click_on_cannons, lambda b: b.res_id == WEAPONS.CANNON)

	def _refresh_traderoute_config_button(self, events):
		#verify if there are possible destinations for a traderoute
		warehouses = self.instance.session.world.settlements

		possible_warehouses = [warehouse for warehouse in warehouses if self.instance.session.world.diplomacy.can_trade(self.instance.session.world.player, warehouse.owner)]

		if len(possible_warehouses) > 1:
			events['configure_route'] = Callback(self._configure_route)
			self.widget.findChild(name='configure_route').set_active()
			self.widget.findChild(name='configure_route').helptext = T("Configure trade route")
		else:
			events['configure_route'] = None
			self.widget.findChild(name='configure_route').set_inactive()
			self.widget.findChild(name='configure_route').helptext = T("No available destinations for a trade route")

	def refresh(self):
		events = {
			# show rename when you click on name
			'name': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.instance),
		}

		self._refresh_found_settlement_button(events)
		self._refresh_trade_button(events)
		self._refresh_traderoute_config_button(events)
		self.widget.mapEvents(events)

		self.widget.child_finder('inventory').update()
		self._refresh_combat()
		super().refresh()

	def hide(self):
		self.route_menu.hide()
		super().hide()


class FightingShipOverviewTab(ShipOverviewTab):
	widget = 'overview_war_ship.xml'
	# TODO why is this here:
	icon_path = 'icons/tabwidget/ship/ship_inv'

	has_stance = True

	def init_widget(self):
		super().init_widget()
		# Create weapon inventory, needed only in gui for inventory widget.
		self.weapon_inventory = self.instance.get_weapon_storage()
		self.widget.findChild(name='weapon_inventory').init(self.instance.session.db, self.weapon_inventory)

	def _refresh_combat(self):
		def apply_equip(button):
			button.button.helptext = T("Equip weapon")
			button.button.capture(Callback(self.equip_weapon, button.res_id))

		def apply_unequip(button):
			button.button.helptext = T("Unequip weapon")
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
		super().on_instance_removed()


class TradeShipOverviewTab(ShipOverviewTab):
	widget = 'overview_trade_ship.xml'
	icon_path = 'icons/tabwidget/ship/ship_inv'
	helptext = LazyT("Ship overview")

	def _refresh_discard_resources(self):
		if self.ship_inv.get_sum_of_stored_resources() == 0:
			self.widget.findChild(name='discard_res_bg').set_inactive()
			self.widget.findChild(name='discard_res').set_inactive()
		else:
			self.widget.findChild(name='discard_res_bg').set_active()
			self.widget.findChild(name='discard_res').set_active()

	def _discard_resources(self):
		self.ship_inv.reset_all()
		self.widget.child_finder('inventory').update()

	def refresh(self):
		super().refresh()
		events = {

		        'discard_res/mouseClicked': Callback(self._discard_resources)
		}
		self.widget.mapEvents(events)
		self._refresh_discard_resources()
		super().refresh()


class TraderShipOverviewTab(OverviewTab):
	widget = 'overview_tradership.xml'
	icon_path = 'icons/tabwidget/ship/ship_inv'
	helptext = LazyT("Ship overview")


class EnemyShipOverviewTab(OverviewTab):
	widget = 'overview_enemyunit.xml'
	icon_path = 'icons/tabwidget/ship/ship_inv'
	helptext = LazyT("Ship overview")

	def init_widget(self):
		super().init_widget()
		self.widget.findChild(name="headline").text = self.instance.owner.name
