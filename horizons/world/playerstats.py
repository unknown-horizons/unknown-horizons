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

import math

from collections import defaultdict

from horizons.util import WorldObject
from horizons.entities import Entities
from horizons.constants import SETTLER, BUILDINGS, PRODUCTION, RES, UNITS
from horizons.util.python import decorators
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.component.selectablecomponent import SelectableComponent
from horizons.world.production.producer import Producer

class PlayerStats(WorldObject):
	def __init__(self, player):
		super(PlayerStats, self).__init__()
		self.player = player
		self.db = player.session.db
		self._collect_info()

	def _collect_info(self):
		settlers = defaultdict(lambda: 0)
		settler_buildings = defaultdict(lambda: 0)
		settler_resources_provided = defaultdict(lambda: 0)
		buildings = defaultdict(lambda: 0)
		available_resources = defaultdict(lambda: 0)
		total_resources = defaultdict(lambda: 0)
		ships = defaultdict(lambda: 0)
		running_costs = 0
		taxes = 0
		usable_land = 0
		settlements = 0

		for settlement in self.player.settlements:
			for building in settlement.buildings:
				buildings[building.id] += 1

				# collect info about settlers
				if building.id == BUILDINGS.RESIDENTIAL_CLASS:
					settlers[building.level] += building.inhabitants
					settler_buildings[building.level] += 1
					for production in building.get_component(Producer).get_productions():
						if production.get_state() is PRODUCTION.STATES.producing:
							produced_res = production.get_produced_res()
							if RES.HAPPINESS_ID in produced_res:
								happiness = produced_res[RES.HAPPINESS_ID]
								for resource_id in production.get_consumed_resources():
									settler_resources_provided[resource_id] += happiness / production.get_production_time()

				# resources held in buildings
				if building.has_component(StorageComponent) and building.id not in [BUILDINGS.WAREHOUSE_CLASS, BUILDINGS.STORAGE_CLASS, BUILDINGS.MAIN_SQUARE_CLASS]:
					for resource_id, amount in building.get_component(StorageComponent).inventory:
						total_resources[resource_id] += amount

				# resource held by collectors
				if hasattr(building, 'get_local_collectors'):
					for collector in building.get_local_collectors():
						for resource_id, amount in collector.get_component(StorageComponent).inventory:
							total_resources[resource_id] += amount

			# resources in settlement inventories
			for resource_id, amount in settlement.get_component(StorageComponent).inventory:
				available_resources[resource_id] += amount

			# land that could be built on (the building on it may need to be destroyed first)
			for tile in settlement.ground_map.itervalues():
				if 'constructible' in tile.classes:
					usable_land += 1

			settlements += 1
			running_costs += settlement.cumulative_running_costs
			taxes += settlement.cumulative_taxes

		# resources in player controlled ships
		for ship in self.player.session.world.ships:
			if ship.owner is self.player:
				ships[ship.id] += 1
				if ship.has_component(SelectableComponent):
					for resource_id, amount in ship.get_component(StorageComponent).inventory:
						available_resources[resource_id] += amount

		for resource_id, amount in available_resources.iteritems():
			total_resources[resource_id] += amount

		self._calculate_settler_score(settlers, settler_buildings, settler_resources_provided)
		self._calculate_building_score(buildings)
		self._calculate_resource_score(available_resources, total_resources)
		self._calculate_unit_score(ships)
		self._calculate_land_score(usable_land, settlements)
		self._calculate_money_score(running_costs, taxes, self.player.get_component(StorageComponent).inventory[RES.GOLD_ID])
		self._calculate_total_score()

	settler_values = {
			SETTLER.SAILOR_LEVEL: 2,
			SETTLER.PIONEER_LEVEL: 3,
			SETTLER.SETTLER_LEVEL: 7,
			SETTLER.CITIZEN_LEVEL: 15,
			}
	settler_building_values = {
			SETTLER.SAILOR_LEVEL: 3,
			SETTLER.PIONEER_LEVEL: 5,
			SETTLER.SETTLER_LEVEL: 11,
			SETTLER.CITIZEN_LEVEL: 19,
			}
	settler_resource_provided_coefficient = 0.1
	settler_score_coefficient = 0.3

	def _calculate_settler_score(self, settlers, settler_buildings, settler_resources_provided):
		total = 0
		for level, number in settlers.iteritems():
			total += self.settler_values[level] * number
		for level, number in settler_buildings.iteritems():
			total += self.settler_building_values[level] * number
		for amount in settler_resources_provided.itervalues():
			total += amount * self.settler_resource_provided_coefficient
		self.settler_score = int(total * self.settler_score_coefficient)

	building_score_coefficient = 0.006

	def _calculate_building_score(self, buildings):
		total = 0
		resources = defaultdict(lambda: 0)
		for building_id, amount in buildings.iteritems():
			for resource_id, res_amount in Entities.buildings[building_id].costs.iteritems():
				resources[resource_id] += amount * res_amount
		for resource_id, amount in resources.iteritems():
			if resource_id == RES.GOLD_ID:
				total += amount # for some reason the value of gold is 0 by default
			else:
				total += amount * self.db.get_res_value(resource_id)
		self.building_score = int(total * self.building_score_coefficient)

	unavailable_resource_coefficient = 0.3 # the resource exists but isn't usable so it is worth less
	overridden_resource_values = {RES.RAW_CLAY_ID: 1, RES.RAW_IRON_ID: 3}
	resource_score_coefficient = 0.01

	def _calculate_resource_score(self, available_resources, total_resources):
		total = 0
		for resource_id, amount in available_resources.iteritems():
			if resource_id in self.overridden_resource_values: # natural resources have 0 value by default
				total += amount * self.overridden_resource_values[resource_id]
			else:
				value = self.db.get_res_value(resource_id)
				if value is not None: # happiness and some coverage resources have no value
					total += amount * value
		for resource_id, amount in total_resources.iteritems():
			extra_amount = (amount - available_resources[resource_id])
			if resource_id in self.overridden_resource_values: # natural resources have 0 value by default
				total += extra_amount * self.overridden_resource_values[resource_id] * self.unavailable_resource_coefficient
			else:
				value = self.db.get_res_value(resource_id)
				if value is not None: # happiness and some coverage resources have no value
					total += extra_amount * value * self.unavailable_resource_coefficient
		self.resource_score = int(total * self.resource_score_coefficient)

	unit_value = {UNITS.FRIGATE_CLASS: 1.5, UNITS.PLAYER_SHIP_CLASS: 1, UNITS.USABLE_FISHER_BOAT: 1, UNITS.FISHER_BOAT_CLASS: 0.05}
	unit_score_coefficient = 10

	def _calculate_unit_score(self, ships):
		total = 0
		for unit_id, amount in ships.iteritems():
			total += self.unit_value[unit_id] * amount
		self.unit_score = int(total * self.unit_score_coefficient)

	settlement_value = 30
	land_score_coefficient = 0.03

	def _calculate_land_score(self, usable_land, settlements):
		total = 0
		total += usable_land
		total += self.settlement_value * settlements
		self.land_score = int(total * self.land_score_coefficient)

	running_cost_coefficient = 10
	minimum_money = 500
	money_power = 0.4
	money_score_coefficient = 1.3

	def _calculate_money_score(self, running_costs, taxes, money):
		total = 0
		total += money
		total += self.running_cost_coefficient * (taxes - running_costs)
		total = math.pow(max(self.minimum_money, total), self.money_power)
		self.money_score = int(total * self.money_score_coefficient)

	def _calculate_total_score(self):
		self.total_score = self.settler_score + self.building_score + self.resource_score + self.unit_score + self.land_score + self.money_score

decorators.bind_all(PlayerStats)
