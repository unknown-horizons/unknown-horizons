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
from fife.extensions import pychan

from horizons.gui.tabs.tabinterface import TabInterface

from horizons.scheduler import Scheduler
from horizons.extscheduler import ExtScheduler
from horizons.util import Callback, ActionSetLoader
from horizons.constants import GAME_SPEED, SETTLER, BUILDINGS, WEAPONS, PRODUCTION
from horizons.gui.widgets.tradewidget import TradeWidget
from horizons.gui.widgets.internationaltradewidget import InternationalTradeWidget
from horizons.gui.widgets.routeconfig import RouteConfig
from horizons.command.uioptions import EquipWeaponFromInventory, UnequipWeaponToInventory
from horizons.command.production import ToggleActive
from horizons.command.building import Tear
from horizons.command.uioptions import SetTaxSetting
from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.util.gui import load_uh_widget, create_resource_icon
from horizons.util.pychananimation import PychanAnimation
from horizons.entities import Entities
from horizons.world.component.namedcomponent import NamedComponent
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.component.tradepostcomponent import TradePostComponent
from horizons.world.production.producer import Producer
from horizons.util.messaging.message import SettlerUpdate


class OverviewTab(TabInterface):
	has_stance = False
	def __init__(self, instance, widget = 'overviewtab.xml', \
	             icon_path='content/gui/icons/tabwidget/common/building_overview_%s.png'):
		super(OverviewTab, self).__init__(widget)
		self.instance = instance
		self.init_values()
		self._refresh_scheduled = False
		self.button_up_image = icon_path % 'u'
		self.button_active_image = icon_path % 'a'
		self.button_down_image = icon_path % 'd'
		self.button_hover_image = icon_path % 'h'
		self.tooltip = _("Overview")

		if self.__class__.has_stance:
			self.init_stance_widget()

		# set player emblem
		if self.widget.child_finder('player_emblem'):
			if self.instance.owner is not None:
				self.widget.child_finder('player_emblem').image =  \
			    'content/gui/images/tabwidget/emblems/emblem_%s.png' %  self.instance.owner.color.name
			else:
				self.widget.child_finder('player_emblem').image = \
			    'content/gui/images/tabwidget/emblems/emblem_no_player.png'

	def _schedule_refresh(self):
		"""Schedule a refresh soon, dropping all other refresh request, that appear until then.
		This saves a lot of CPU time, if you have a huge island, or play on high speed."""
		if not self._refresh_scheduled:
			self._refresh_scheduled = True
			def unset_flag():
				self._refresh_scheduled = False
			ExtScheduler().add_new_object(Callback.ChainedCallbacks(unset_flag, self.refresh),
			                              self, run_in=0.3)

	def refresh(self):
		if (hasattr(self.instance, 'name') or self.instance.has_component(NamedComponent)) and self.widget.child_finder('name'):
			name_widget = self.widget.child_finder('name')
			# Named objects can't be translated.
			if self.instance.has_component(NamedComponent):
				name_widget.text = unicode(self.instance.get_component(NamedComponent).name)
			else:
				name_widget.text = _(self.instance.name)

		if hasattr(self.instance, 'running_costs') and \
		   self.widget.child_finder('running_costs'):
			self.widget.child_finder('running_costs').text = \
			    unicode( self.instance.running_costs )

		self.widget.adaptLayout()

	def show(self):
		super(OverviewTab, self).show()
		if not self.instance.has_change_listener(self.refresh):
			self.instance.add_change_listener(self.refresh)
		if not self.instance.has_remove_listener(self.on_instance_removed):
			self.instance.add_remove_listener(self.on_instance_removed)
		if hasattr(self.instance, 'settlement') and \
		   self.instance.settlement is not None and \
		   not self.instance.settlement.has_change_listener(self._schedule_refresh):
			# listen for settlement name changes displayed as tab headlines
			self.instance.settlement.add_change_listener(self._schedule_refresh)

	def hide(self):
		super(OverviewTab, self).hide()
		if self.instance is not None:
			if self.instance.has_change_listener(self.refresh):
				self.instance.remove_change_listener(self.refresh)
			if self.instance.has_remove_listener(self.on_instance_removed):
				self.instance.remove_remove_listener(self.on_instance_removed)
		if hasattr(self.instance, 'settlement') and \
		   self.instance.settlement is not None and \
		   self.instance.settlement.has_change_listener(self._schedule_refresh):
			self.instance.settlement.remove_change_listener(self._schedule_refresh)

		if self._refresh_scheduled:
			ExtScheduler().rem_all_classinst_calls(self)

	def on_instance_removed(self):
		self.on_remove()
		self.instance = None

	def init_stance_widget(self): # call for tabs with stances
		stance_widget = self.widget.findChild(name='stance')
		stance_widget.init(self.instance)
		self.add_remove_listener(stance_widget.remove)


class WarehouseOverviewTab(OverviewTab):
	""" the main tab of warehouses and storages """

	def __init__(self, instance):
		super(WarehouseOverviewTab, self).__init__(
			widget = 'overview_warehouse.xml',
			instance = instance
		)
		self.widget.findChild(name="headline").text = unicode(self.instance.settlement.get_component(NamedComponent).name)
		self.tooltip = _("Warehouse overview")
		self._refresh_collector_utilisation()

	def _refresh_collector_utilisation(self):
		utilisation = int(round(self.instance.get_collector_utilisation() * 100))
		self.widget.findChild(name="collector_utilisation").text = unicode(str(utilisation) + '%')

	def refresh(self):
		self.widget.findChild(name="headline").text = unicode(self.instance.settlement.get_component(NamedComponent).name)
		events = {
				'headline': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.instance.settlement)
		         }
		self.widget.mapEvents(events)
		self._refresh_collector_utilisation()
		super(WarehouseOverviewTab, self).refresh()

	def show(self):
		super(WarehouseOverviewTab, self).show()
		Scheduler().add_new_object(Callback(self._refresh_collector_utilisation), self, run_in = GAME_SPEED.TICKS_PER_SECOND, loops = -1)

	def hide(self):
		super(WarehouseOverviewTab, self).hide()
		Scheduler().rem_all_classinst_calls(self)

	def on_instance_removed(self):
		Scheduler().rem_all_classinst_calls(self)
		super(WarehouseOverviewTab, self).on_instance_removed()


class ShipOverviewTab(OverviewTab):
	def __init__(self, instance, widget = 'overview_trade_ship.xml', \
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png'):
		super(ShipOverviewTab, self).__init__(instance, widget, icon_path)
		self.widget.child_finder('inventory').init(self.instance.session.db, self.instance.get_component(StorageComponent).inventory)
		self.tooltip = _("Ship overview")

	def _configure_route(self):
		self.route_menu = RouteConfig(self.instance)
		self.route_menu.toggle_visibility()

	def _refresh_found_settlement_button(self, events):
		island_without_player_settlement_found = False
		tooltip = _("The ship needs to be close to an island to found a settlement.")
		for island in self.instance.session.world.get_islands_in_radius(self.instance.position, self.instance.radius):
			if not any(settlement.owner.is_local_player for settlement in island.settlements):
				island_without_player_settlement_found = True
			else:
				tooltip = _("You already have a settlement on this island.")

		if island_without_player_settlement_found:
			events['found_settlement'] = Callback(self.instance.session.ingame_gui._build, \
			                                     BUILDINGS.WAREHOUSE_CLASS, \
			                                     weakref.ref(self.instance) )
			self.widget.child_finder('found_settlement_bg').set_active()
			self.widget.child_finder('found_settlement').set_active()
			self.widget.child_finder('found_settlement').tooltip = _("Build settlement")
		else:
			events['found_settlement'] = None
			self.widget.child_finder('found_settlement_bg').set_inactive()
			self.widget.child_finder('found_settlement').set_inactive()
			self.widget.child_finder('found_settlement').tooltip = tooltip

		cb = Callback( self.instance.session.ingame_gui.resource_overview.set_construction_mode,
		               self.instance,
		               Entities.buildings[BUILDINGS.WAREHOUSE_CLASS].costs)
		events['found_settlement/mouseEntered'] = cb

		cb1 = Callback(self.instance.session.ingame_gui.resource_overview.close_construction_mode)
		cb2 = Callback(self.widget.child_finder('found_settlement').hide_tooltip)
		#TODO the tooltip should actually hide on its own. Ticket #1096
		cb = Callback.ChainedCallbacks(cb1, cb2)
		events['found_settlement/mouseExited'] = cb

	def _refresh_trade_button(self, events):
		warehouses = self.instance.session.world.get_warehouses(self.instance.position, \
			self.instance.radius, self.instance.owner, True)

		if warehouses:
			if warehouses[0].owner is self.instance.owner:
				wdg = TradeWidget(self.instance)
				tooltip = _('Load/Unload')
			else:
				wdg = InternationalTradeWidget(self.instance)
				tooltip = _('Buy/Sell')
			events['trade'] = Callback(self.instance.session.ingame_gui.show_menu, wdg)
			self.widget.findChild(name='trade_bg').set_active()
			self.widget.findChild(name='trade').set_active()
			self.widget.findChild(name='trade').tooltip = tooltip
		else:
			events['trade'] = None
			self.widget.findChild(name='trade_bg').set_inactive()
			self.widget.findChild(name='trade').set_inactive()
			self.widget.findChild(name='trade').tooltip = _('Too far from the nearest own or allied warehouse')

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
	def __init__(self, instance, widget = 'overview_war_ship.xml', \
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png'):
		super(FightingShipOverviewTab, self).__init__(instance, widget, icon_path)


		#create weapon inventory, needed only in gui for inventory widget
		self.weapon_inventory = self.instance.get_weapon_storage()
		self.widget.findChild(name='weapon_inventory').init(self.instance.session.db, self.weapon_inventory)

	def _refresh_combat(self):
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
		self.refresh()

	def unequip_weapon(self, weapon_id):
		if UnequipWeaponToInventory(self.instance, weapon_id, 1).execute(self.instance.session) == 0:
			self.weapon_inventory.alter(weapon_id, -1)
		self.widget.child_finder('weapon_inventory').update()
		self.refresh()

	def on_instance_removed(self):
		self.weapon_inventory = None
		super(FightingShipOverviewTab, self).on_instance_removed()

class TowerOverviewTab(OverviewTab): # defensive tower
	def __init__(self, instance):
		super(TowerOverviewTab, self).__init__(
			widget = 'overview_tower.xml',
			instance = instance
		)
		self.widget.findChild(name="headline").text = unicode(self.instance.settlement.get_component(NamedComponent).name)
		self.tooltip = _("Tower overview")

class TraderShipOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(TraderShipOverviewTab, self).__init__(
			widget = 'overview_tradership.xml',
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png',
			instance = instance
		)
		self.tooltip = _("Ship overview")

class GroundUnitOverviewTab(OverviewTab):
	has_stance = True
	def __init__(self, instance):
		super(GroundUnitOverviewTab, self).__init__(
			widget = 'overview_groundunit.xml',
			instance = instance)
		self.tooltip = _("Unit overview")
		health_widget = self.widget.findChild(name='health')
		health_widget.init(self.instance)
		self.add_remove_listener(health_widget.remove)
		weapon_storage_widget = self.widget.findChild(name='weapon_storage')
		weapon_storage_widget.init(self.instance)
		self.add_remove_listener(weapon_storage_widget.remove)

class ProductionOverviewTab(OverviewTab):
	ACTIVE_PRODUCTION_ANIM_DIR = "content/gui/images/animations/cogs/large"
	BUTTON_BACKGROUND = "content/gui/images/buttons/msg_button.png"

	def  __init__(self, instance, widget='overview_productionbuilding.xml',
		         production_line_gui_xml='overview_productionline.xml'):
		super(ProductionOverviewTab, self).__init__(
			widget = widget,
			instance = instance
		)
		self.tooltip = _("Production overview")
		self.production_line_gui_xml = production_line_gui_xml
		self._animations = []

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self._refresh_utilisation()

		# remove old production line data
		parent_container = self.widget.child_finder('production_lines')
		while len(parent_container.children) > 0:
			child = parent_container.children[-1]
			if hasattr(child, "anim"):
				child.anim.stop()
				del child.anim
			parent_container.removeChild( child )

		# create a container for each production
		# sort by production line id to have a consistent (basically arbitrary) order
		for production in sorted(self.instance.get_component(Producer).get_productions(), \
								             key=(lambda x: x.get_production_line_id())):

			if not production.has_change_listener(self.refresh):
				# we need to be notified of small production changes, that aren't passed through the instance
				production.add_change_listener(self.refresh)

			gui = load_uh_widget(self.production_line_gui_xml)
			# fill in values to gui reflecting the current game state
			container = gui.findChild(name="production_line_container")
			if production.is_paused():
				container.removeChild( container.findChild(name="toggle_active_active") )
				toggle_icon = container.findChild(name="toggle_active_inactive")
				toggle_icon.name = "toggle_active"
			else:
				container.removeChild( container.findChild(name="toggle_active_inactive") )
				toggle_icon = container.findChild(name="toggle_active_active")
				toggle_icon.name = "toggle_active"

				if production.get_state() == PRODUCTION.STATES.producing:
					bg = pychan.widgets.Icon(image=self.__class__.BUTTON_BACKGROUND)
					bg.position = toggle_icon.position
					container.addChild(bg)
					container.removeChild(toggle_icon) # fix z-ordering
					container.addChild(toggle_icon)
					anim = PychanAnimation(toggle_icon, self.__class__.ACTIVE_PRODUCTION_ANIM_DIR)
					container.anim = anim
					anim.start(1.0/12, -1) # always start anew, people won't notice
					self._animations.append( weakref.ref( anim ) )

			# fill it with input and output resources
			in_res_container = container.findChild(name="input_res")
			for in_res in production.get_consumed_resources():
				filled = float(self.instance.get_component(StorageComponent).inventory[in_res]) * 100 / \
				       self.instance.get_component(StorageComponent).inventory.get_limit(in_res)
				in_res_container.addChild( \
				  ImageFillStatusButton.init_for_res(self.instance.session.db,\
				                                     in_res, \
				                                     self.instance.get_component(StorageComponent).inventory[in_res], \
				                                     filled, \
				                                     use_inactive_icon=False, \
				                                     uncached=True) \
				)
			out_res_container = container.findChild(name="output_res")
			for out_res in production.get_produced_res():
				filled = float(self.instance.get_component(StorageComponent).inventory[out_res]) * 100 /  \
				       self.instance.get_component(StorageComponent).inventory.get_limit(out_res)
				out_res_container.addChild( \
				  ImageFillStatusButton.init_for_res(self.instance.session.db, \
				                                     out_res, \
				                                     self.instance.get_component(StorageComponent).inventory[out_res], \
				                                     filled, \
				                                     use_inactive_icon=False, \
				                                     uncached=True) \
				)


			# fix pychans lack of dynamic container sizing
			# the container in the xml must provide a height attribute, that is valid for
			# one resource.
			max_res_in_one_line = max(len(production.get_produced_res()), \
			                          len(production.get_consumed_resources()))
			container.height = max_res_in_one_line * container.height


			# active toggle_active button
			container.mapEvents( \
			  { 'toggle_active': \
			    Callback(ToggleActive(self.instance.get_component(Producer), production).execute, self.instance.session) \
			    } )
			# NOTE: this command causes a refresh, so we needn't change the toggle_active-button-image
			container.stylize('menu_black')
			parent_container.addChild(container)
		super(ProductionOverviewTab, self).refresh()

	def destruct_building(self):
		self.instance.session.ingame_gui.hide_menu()
		Tear(self.instance).execute(self.instance.session)

	def _refresh_utilisation(self):
		utilisation = 0
		if self.instance.has_component(Producer):
			utilisation = int(round(self.instance.get_component(Producer).capacity_utilisation * 100))
		self.widget.child_finder('capacity_utilisation').text = unicode(str(utilisation) + '%')

	def show(self):
		super(ProductionOverviewTab, self).show()
		Scheduler().add_new_object(Callback(self._refresh_utilisation), self, run_in = GAME_SPEED.TICKS_PER_SECOND, loops = -1)

	def hide(self):
		super(ProductionOverviewTab, self).hide()
		self._cleanup()

	def on_instance_removed(self):
		self._cleanup()
		super(ProductionOverviewTab, self).on_instance_removed()

	def _cleanup(self):
		Scheduler().rem_all_classinst_calls(self)
		for production in self.instance.get_component(Producer).get_productions():
			if production.has_change_listener(self.refresh):
				production.remove_change_listener(self.refresh)
		for anim in self._animations:
			if anim():
				anim().stop()
		self._animations = []


class FarmProductionOverviewTab(ProductionOverviewTab):
	def  __init__(self, instance):
		super(FarmProductionOverviewTab, self).__init__(
			instance = instance,
			widget = 'overview_farm.xml',
			production_line_gui_xml = "overview_farmproductionline.xml"
		)
		self.tooltip = _("Production overview")

class SettlerOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(SettlerOverviewTab, self).__init__(
			widget = 'overview_settler.xml',
			instance = instance
		)
		self.tooltip = _("Settler overview")
		self.widget.findChild(name="headline").text = unicode(self.instance.settlement.get_component(NamedComponent).name)
		_setup_tax_slider(self.widget.child_finder('tax_slider'), self.widget.child_finder('tax_val_label'),
		                  self.instance.settlement, self.instance.level)

		self.widget.child_finder('tax_val_label').text = unicode(self.instance.settlement.tax_settings[self.instance.level])
		action_set = ActionSetLoader.get_sets()[self.instance._action_set_id]
		action_gfx = action_set.items()[0][1]
		image = action_gfx[45].keys()[0]
		self.widget.findChild(name="building_image").image = image

	def on_settler_level_change(self, message):
		assert isinstance(message, SettlerUpdate)
		_setup_tax_slider(self.widget.child_finder('tax_slider'), self.widget.child_finder('tax_val_label'),
		                  self.instance.settlement, message.level)
		self.widget.child_finder('tax_val_label').text = unicode(self.instance.settlement.tax_settings[self.instance.level])

	def show(self):
		super(SettlerOverviewTab, self).show()
		self.instance.session.message_bus.subscribe_locally(SettlerUpdate, self.instance, self.on_settler_level_change)

	def hide(self):
		self.instance.session.message_bus.unsubscribe_locally(SettlerUpdate, self.instance, self.on_settler_level_change)
		super(SettlerOverviewTab, self).hide()

	def refresh(self):
		self.widget.child_finder('happiness').progress = self.instance.happiness
		self.widget.child_finder('inhabitants').text = u"%s/%s" % (
		                                               self.instance.inhabitants,
		                                               self.instance.inhabitants_max)
		self.widget.child_finder('taxes').text = unicode(self.instance.last_tax_payed)
		self.update_consumed_res()
		self.widget.findChild(name="headline").text = unicode(self.instance.settlement.get_component(NamedComponent).name)
		events = {
				'headline': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.instance.settlement)
		         }
		self.widget.mapEvents(events)
		super(SettlerOverviewTab, self).refresh()

	def update_consumed_res(self):
		"""Updates the container that displays the needed resources of the settler"""
		container = self.widget.findChild(name="needed_res")
		# remove icons from the container
		container.removeChildren(*container.children)

		# create new ones
		resources = self.instance.get_currently_not_consumed_resources()
		for res in resources:
			icon = create_resource_icon(res, self.instance.session.db)
			container.addChild(icon)

		container.adaptLayout()

class SignalFireOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(SignalFireOverviewTab, self).__init__(
			widget = 'overview_signalfire.xml',
			instance = instance
		)
		action_set = ActionSetLoader.get_sets()[self.instance._action_set_id]
		action_gfx = action_set.items()[0][1]
		image = action_gfx[45].keys()[0]
		self.widget.findChild(name="building_image").image = image
		self.tooltip = _("Overview")

class EnemyBuildingOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(EnemyBuildingOverviewTab, self).__init__(
			widget = 'overview_enemybuilding.xml',
			instance = instance
		)
		self.widget.findChild(name="headline").text = unicode(self.instance.owner.name)

class EnemyWarehouseOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(EnemyWarehouseOverviewTab, self).__init__(
			widget = 'overview_enemywarehouse.xml',
			instance = instance
		)
		self.widget.findChild(name="headline").text = unicode(self.instance.settlement.get_component(NamedComponent).name)
		self.tooltip = _("Warehouse overview")

	def refresh(self):
		settlement = self.instance.settlement
		self.widget.findChild(name="headline").text = unicode(settlement.get_component(NamedComponent).name)

		selling_inventory = self.widget.findChild(name='selling_inventory')
		selling_inventory.init(self.instance.session.db, settlement.get_component(StorageComponent).inventory, settlement.get_component(TradePostComponent).sell_list, True)

		buying_inventory = self.widget.findChild(name='buying_inventory')
		buying_inventory.init(self.instance.session.db, settlement.get_component(StorageComponent).inventory, settlement.get_component(TradePostComponent).buy_list, False)

		super(EnemyWarehouseOverviewTab, self).refresh()

class EnemyShipOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(EnemyShipOverviewTab, self).__init__(
			widget = 'overview_enemyunit.xml',
			icon_path='content/gui/icons/tabwidget/ship/ship_inv_%s.png',
			instance = instance
		)
		self.widget.findChild(name="headline").text = unicode(self.instance.owner.name)

class ResourceDepositOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(ResourceDepositOverviewTab, self).__init__(
			widget = 'overview_resourcedeposit.xml',
			instance = instance
		)
		res = self.instance.session.db.get_resource_deposit_resources(self.instance.id)
		# type: [ (res, min_amount, max_amount)]
		# let it display starting from 0, not min_amount, else it looks like there's nothing in it
		# when parts of the ore have been mined already
		res_range = 0, res[0][2]
		self.widget.child_finder("inventory").init(self.instance.session.db, \
		                                           self.instance.get_component(StorageComponent).inventory,
		                                           ordinal=res_range)

	def refresh(self):
		super(ResourceDepositOverviewTab, self).refresh()
		self.widget.child_finder("inventory").update()


###
# Minor utility functions

def _setup_tax_slider(slider, val_label, settlement, level):
	"""Set up a slider to work as tax slider"""
	slider.scale_start = SETTLER.TAX_SETTINGS_MIN
	slider.scale_end = SETTLER.TAX_SETTINGS_MAX
	slider.step_length = SETTLER.TAX_SETTINGS_STEP
	slider.value = settlement.tax_settings[level]
	slider.stylize('book')
	def on_slider_change():
		val_label.text = unicode(slider.value)
		if(settlement.tax_settings[level] != slider.value):
			SetTaxSetting(settlement, level, slider.value).execute(settlement.session)
	slider.capture(on_slider_change)
