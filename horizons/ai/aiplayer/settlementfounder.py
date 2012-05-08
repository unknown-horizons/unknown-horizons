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

import logging

from collections import defaultdict

from horizons.ai.aiplayer.mission.foundsettlement import FoundSettlement
from horizons.ai.aiplayer.mission.preparefoundationship import PrepareFoundationShip
from horizons.ai.aiplayer.landmanager import LandManager
from horizons.constants import RES, BUILDINGS
from horizons.util.python import decorators
from horizons.component.storagecomponent import StorageComponent

class SettlementFounder(object):
	"""This class handles the settlement founding activities of an AI player."""

	log = logging.getLogger("ai.aiplayer.settlement_founder")

	def __init__(self, owner):
		super(SettlementFounder, self).__init__()
		self.owner = owner
		self.session = owner.session
		self.world = owner.world
		self.personality = owner.personality_manager.get('SettlementFounder')
		self.__island_value_cache = {} # {island_id: (last_change_id, value), ...}

	def _evaluate_island(self, island):
		"""Return (flat land, utility value) of the given island."""
		flat_land = 0
		resources = defaultdict(lambda: 0)

		for tile in island.ground_map.itervalues():
			if 'constructible' not in tile.classes:
				continue
			object = tile.object
			if object is not None and not object.buildable_upon:
				if object.id in [BUILDINGS.CLAY_DEPOSIT, BUILDINGS.MOUNTAIN] and (tile.x, tile.y) == object.position.origin.to_tuple():
					# take the natural resources into account
					usable = True # is the deposit fully available (no part owned by a player)?
					for coords in object.position.tuple_iter():
						if island.ground_map[coords].settlement is not None:
							usable = False
							break
					if usable:
						for resource_id, amount in object.get_component(StorageComponent).inventory.itercontents():
							resources[resource_id] += amount
				continue
			if tile.settlement is not None:
				continue
			flat_land += 1

		# calculate the value of the island by taking into account the available land, resources, and number of enemy settlements
		value = flat_land
		value += min(resources[RES.RAW_CLAY], self.personality.max_raw_clay) * self.personality.raw_clay_importance
		if resources[RES.RAW_CLAY] < self.personality.min_raw_clay:
			value -= self.personality.no_raw_clay_penalty
		value += min(resources[RES.RAW_IRON], self.personality.max_raw_iron) * self.personality.raw_iron_importance
		if resources[RES.RAW_IRON] < self.personality.min_raw_iron:
			value -= self.personality.no_raw_iron_penalty
		value -= len(island.settlements) * self.personality.enemy_settlement_penalty

		# take into the distance to our old warehouses and the other players' islands
		for settlement in self.world.settlements:
			if settlement.owner is self.owner:
				value += self.personality.compact_empire_importance / float(island.position.distance(settlement.warehouse.position) + self.personality.extra_warehouse_distance)
			else:
				value -= self.personality.nearby_enemy_penalty / float(island.position.distance(settlement.island.position) + self.personality.extra_enemy_island_distance)

		return (flat_land, max(2, int(value)))

	def _get_available_islands(self, min_land):
		"""Return a list of available islands in the form [(value, island), ...]."""
		options = []
		for island in self.owner.world.islands:
			if island.worldid not in self.owner.islands:
				if island.worldid not in self.__island_value_cache or self.__island_value_cache[island.worldid][0] != island.last_change_id:
					self.__island_value_cache[island.worldid] = (island.last_change_id, self._evaluate_island(island))
				if self.__island_value_cache[island.worldid][1][0] >= min_land:
					options.append((self.__island_value_cache[island.worldid][1][1], island))
		return options

	def _choose_island(self, min_land):
		"""Randomly choose one of the big enough islands. Return the island or None if it is impossible."""
		options = self._get_available_islands(min_land)
		if not options:
			return None
		total_value = sum(zip(*options)[0])

		# choose a random big enough island with probability proportional to its value
		choice = self.session.random.randint(0, total_value - 1)
		for (land, island) in options:
			if choice <= land:
				return island
			choice -= land
		return None

	def _found_settlement(self, island, ship, feeder_island):
		"""Found a settlement on the given island using the given ship."""
		land_manager = LandManager(island, self.owner, feeder_island)
		land_manager.display()
		self.owner.islands[island.worldid] = land_manager
		self.owner.start_mission(FoundSettlement.create(ship, land_manager, self.owner.report_success, self.owner.report_failure))

	def _have_settlement_starting_resources(self, ship, settlement, min_money, min_resources):
		"""Returns a boolean showing whether we have enough resources to found a new settlement."""
		if self.owner.get_component(StorageComponent).inventory[RES.GOLD] < min_money:
			return False

		if ship is not None:
			for res, amount in ship.get_component(StorageComponent).inventory.itercontents():
				if res in min_resources and min_resources[res] > 0:
					min_resources[res] = max(0, min_resources[res] - amount)

		if settlement:
			for res, amount in settlement.get_component(StorageComponent).inventory.itercontents():
				if res in min_resources and min_resources[res] > 0:
					min_resources[res] = max(0, min_resources[res] - amount)

		for missing in min_resources.itervalues():
			if missing > 0:
				return False
		return True

	def have_starting_resources(self, ship, settlement):
		"""Returns a boolean showing whether we have enough resources to found a new normal settlement."""
		return self._have_settlement_starting_resources(ship, settlement, self.personality.min_new_island_gold, \
				                                        {RES.BOARDS: self.personality.min_new_island_boards, RES.FOOD: self.personality.min_new_island_food, RES.TOOLS: self.personality.min_new_island_tools})

	def have_feeder_island_starting_resources(self, ship, settlement):
		"""Returns a boolean showing whether we have enough resources to found a new feeder island."""
		return self._have_settlement_starting_resources(ship, settlement, self.personality.min_new_feeder_island_gold, \
				                                        {RES.BOARDS: self.personality.min_new_island_boards, RES.TOOLS: self.personality.min_new_island_tools})

	def _prepare_foundation_ship(self, settlement_manager, ship, feeder_island):
		"""Start a mission to load the settlement foundation resources on the given ship from the specified settlement."""
		self.owner.start_mission(PrepareFoundationShip(settlement_manager, ship, feeder_island, self.owner.report_success, self.owner.report_failure))

	def _want_another_village(self):
		"""Return a boolean showing whether we want to start another settlement with a village."""
		# avoid having more than one developing island with a village at a time
		for settlement_manager in self.owner.settlement_managers:
			if not settlement_manager.feeder_island and not settlement_manager.can_provide_resources():
				return False
		return True

	def tick(self):
		"""Found a new settlement or prepare a foundation ship if possible and required."""
		ship = None
		for possible_ship, state in self.owner.ships.iteritems():
			if state is self.owner.shipStates.idle:
				# TODO: make sure the ship is actually usable for founding a settlement
				ship = possible_ship
				break
		if ship is None and self.owner.ships:
			#self.log.info('%s.tick: all ships are in use', self)
			return

		island = None
		for min_size in self.personality.island_size_sequence:
			island = self._choose_island(min_size)
			if island is not None:
				break
		if island is None:
			#self.log.info('%s.tick: no good enough islands', self)
			return

		if self.owner.need_feeder_island:
			if self.have_feeder_island_starting_resources(ship, None):
				if ship is None:
					self.owner.request_ship()
				else:
					self.log.info('%s.tick: send %s on a mission to found a feeder settlement', self, ship)
					self._found_settlement(island, ship, True)
			else:
				for settlement_manager in self.owner.settlement_managers:
					if self.have_feeder_island_starting_resources(ship, settlement_manager.land_manager.settlement):
						if ship is None:
							self.owner.request_ship()
						else:
							self.log.info('%s.tick: send ship %s on a mission to get resources for a new feeder settlement', self, ship)
							self._prepare_foundation_ship(settlement_manager, ship, True)
						return
		elif self._want_another_village():
			if self.have_starting_resources(ship, None):
				if ship is None:
					self.owner.request_ship()
				else:
					self.log.info('%s.tick: send ship %s on a mission to found a settlement', self, ship)
					self._found_settlement(island, ship, False)
			else:
				for settlement_manager in self.owner.settlement_managers:
					if not settlement_manager.can_provide_resources():
						continue
					if self.have_starting_resources(ship, settlement_manager.land_manager.settlement):
						if ship is None:
							self.owner.request_ship()
						else:
							self.log.info('%s.tick: send ship %s on a mission to get resources for a new settlement', self, ship)
							self._prepare_foundation_ship(settlement_manager, ship, False)
						return

	def can_found_feeder_island(self):
		"""Return a boolean showing whether there is an island that could be turned into a feeder island."""
		return bool(self._get_available_islands(self.personality.min_feeder_island_area))

	def found_feeder_island(self):
		"""Call this function to let the player know that a new feeder island is needed."""
		if self.can_found_feeder_island():
			self.owner.need_feeder_island = True

	def __str__(self):
		return '%s SettlementFounder' % (self.owner)

decorators.bind_all(SettlementFounder)