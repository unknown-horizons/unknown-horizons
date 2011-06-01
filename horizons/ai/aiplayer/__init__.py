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

import logging

from collections import deque

from mission.foundsettlement import FoundSettlement
from mission.preparefoundationship import PrepareFoundationShip
from landmanager import LandManager
from completeinventory import CompleteInventory
from settlementmanager import SettlementManager

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject
from horizons.constants import RES, BUILDINGS
from horizons.ext.enum import Enum
from horizons.ai.generic import GenericAI
from horizons.util.python import decorators

class AIPlayer(GenericAI):
	"""This is the AI that builds settlements."""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'on_a_mission')

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, session, id, name, color, **kwargs):
		super(AIPlayer, self).__init__(session, id, name, color, **kwargs)
		self.__init()
		Scheduler().add_new_object(Callback(self.finish_init), self, run_in = 0)
		Scheduler().add_new_object(Callback(self.tick), self, run_in = 2)

	def choose_island(self, min_land):
		best_island = None
		best_value = None

		for island in self.session.world.islands:
			if island in self.islands:
				continue

			flat_land = 0
			for tile in island.ground_map.itervalues():
				if 'constructible' in tile.classes:
					if tile.object is None or tile.object.buildable_upon:
						flat_land += 1
			if flat_land >= min_land and (best_value is None or best_value < flat_land):
				best_island = island
				best_value = flat_land
		return best_island

	def finish_init(self):
		for ship in self.session.world.ships:
			if ship.owner == self:
				self.ships[ship] = self.shipStates.idle

	def __init(self):
		self.islands = {}
		self.settlement_managers = []
		self.missions = []
		self.fishers = []
		self.complete_inventory = CompleteInventory(self)

	def report_success(self, mission, msg):
		self.missions.remove(mission)
		if mission.ship:
			self.ships[mission.ship] = self.shipStates.idle
		if isinstance(mission, FoundSettlement):
			settlement_manager = SettlementManager(mission.land_manager, mission.branch_office)
			self.settlement_managers.append(settlement_manager)

	def report_failure(self, mission, msg):
		self.missions.remove(mission)
		if mission.ship:
			self.ships[mission.ship] = self.shipStates.idle
		if isinstance(mission, FoundSettlement):
			del self.islands[mission.land_manager.island]

	def save(self, db):
		super(AIPlayer, self).save(db)

		# save the player
		current_callback = Callback(self.tick)
		calls = Scheduler().get_classinst_calls(self, current_callback)
		assert len(calls) == 1, "got %s calls for saving %s: %s" % (len(calls), current_callback, calls)
		remaining_ticks = max(calls.values()[0], 1)
		db("INSERT INTO ai_player(rowid, remaining_ticks) VALUES(?, ?)", self.worldid, remaining_ticks)

		# save the ships
		for ship, state in self.ships.iteritems():
			db("INSERT INTO ai_ship(rowid, owner, state) VALUES(?, ?, ?)", ship.worldid, self.worldid, state.index)

		# save the land managers
		for island, land_manager in self.islands.iteritems():
			land_manager.save(db)

		# save the settlement managers
		for settlement_manager in self.settlement_managers:
			settlement_manager.save(db)

		# save the missions
		for mission in self.missions:
			mission.save(db)

	def _load(self, db, worldid):
		super(AIPlayer, self)._load(db, worldid)
		self.__init()

		remaining_ticks = db("SELECT remaining_ticks FROM ai_player WHERE rowid = ?", worldid)[0][0]
		Scheduler().add_new_object(Callback(self.tick), self, run_in = remaining_ticks)

	def finish_loading(self, db):
		""" This is called separately because most objects are loaded after the player. """

		# load the ships
		for ship_id, state_id in db("SELECT rowid, state FROM ai_ship WHERE owner = ?", self.worldid):
			ship = WorldObject.get_object_by_id(ship_id)
			self.ships[ship] = self.shipStates[state_id]

		# load the land managers
		for worldid, island_id in db("SELECT rowid, island FROM ai_land_manager WHERE owner = ?", self.worldid):
			island = WorldObject.get_object_by_id(island_id)
			self.islands[island] = LandManager.load(db, self, island, worldid)

		# load the settlement managers
		for land_manager in self.islands.itervalues():
			settlement_manager_id = db("SELECT rowid FROM ai_settlement_manager WHERE land_manager = ?", land_manager.worldid)[0][0]
			self.settlement_managers.append(SettlementManager.load(db, settlement_manager_id))

		# TODO: load the missions
		for mission in self.missions:
			raise NotImplementedError

	def found_settlement(self, island, ship):
		self.ships[ship] = self.shipStates.on_a_mission
		land_manager = LandManager(island, self)
		land_manager.display()
		self.islands[island] = land_manager

		found_settlement = FoundSettlement.create(ship, land_manager, self.report_success, self.report_failure)
		self.missions.append(found_settlement)
		found_settlement.start()

	def have_starting_resources(self, ship, settlement):
		if self.complete_inventory.money < 3500:
			return False

		need = {RES.BOARDS_ID: 17, RES.FOOD_ID: 10, RES.TOOLS_ID: 5}
		for res, amount in ship.inventory:
			if res in need and need[res] > 0:
				need[res] = max(0, need[res] - amount)

		if settlement:
			for res, amount in settlement.inventory:
				if res in need and need[res] > 0:
					need[res] = max(0, need[res] - amount)

		for missing in need.itervalues():
			if missing > 0:
				return False
		return True

	def prepare_foundation_ship(self, settlement_manager, ship):
		self.ships[ship] = self.shipStates.on_a_mission
		mission = PrepareFoundationShip(settlement_manager, ship, self.report_success, self.report_failure)
		self.missions.append(mission)
		mission.start()

	def tick(self):
		Scheduler().add_new_object(Callback(self.tick), self, run_in = 37)

		ship = self.ships.keys()[0]
		if self.ships[ship] != self.shipStates.idle:
			#self.log.info('ai.tick: no available ships')
			return

		island = self.choose_island(500 if self.settlement_managers else 150)
		if island is None:
			#self.log.info('ai.tick: no good enough islands')
			return

		if self.have_starting_resources(ship, None):
			self.log.info('ai.tick: send ship %s on a mission to found a settlement', ship)
			self.found_settlement(island, ship)
		else:
			for settlement_manager in self.settlement_managers:
				if not settlement_manager.can_provide_resources():
					continue
				if self.have_starting_resources(ship, settlement_manager.land_manager.settlement):
					self.log.info('ai.tick: send ship %s on a mission to get resources for a new settlement', ship)
					self.prepare_foundation_ship(settlement_manager, ship)
					return

	def notify_unit_path_blocked(self, unit):
		self.log.warning("%s %s: ship blocked", self.__class__.__name__, self.worldid)

decorators.bind_all(AIPlayer)
