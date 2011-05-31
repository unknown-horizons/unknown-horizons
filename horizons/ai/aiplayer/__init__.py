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

import horizons.main

from mission.foundsettlement import FoundSettlement
from landmanager import LandManager
from completeinventory import CompleteInventory
from villagebuilder import VillageBuilder
from productionbuilder import ProductionBuilder

from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject, Circle
from horizons.constants import RES, UNITS, BUILDINGS
from horizons.ext.enum import Enum
from horizons.ai.generic import GenericAI
from horizons.world.storageholder import StorageHolder
from horizons.command.unit import CreateUnit
from horizons.world.units.ship import Ship
from horizons.world.units.movingobject import MoveNotPossible
from horizons.util.python import decorators

class AIPlayer(GenericAI):
	"""This is the AI that builds settlements."""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'on_a_mission')

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, session, id, name, color, **kwargs):
		super(AIPlayer, self).__init__(session, id, name, color, **kwargs)
		Scheduler().add_new_object(Callback(self.__init), self)
		Scheduler().add_new_object(Callback(self.start), self, run_in = 2)

	def choose_island(self):
		best_island = None
		best_value = None

		for island in self.session.world.islands:
			flat_land = 0
			for tile in island.ground_map.itervalues():
				if 'constructible' in tile.classes:
					flat_land += 1
			if best_value is None or best_value < flat_land:
				best_island = island
				best_value = flat_land
		return best_island

	def __init(self):
		for ship in self.session.world.ships:
			if ship.owner == self:
				self.ships[ship] = self.shipStates.on_a_mission

		self.missions = {}
		self.island = self.choose_island()

		self.land_manager = LandManager(self.island, self)
		self.land_manager.divide()
		self.land_manager.display()

		self.fishers = []

		self.complete_inventory = CompleteInventory(self)
		self.build_queue = deque()
		self.tents = 0

	def tick(self):
		call_again = False
		if len(self.build_queue) > 0:
			self.log.info('ai.tick: build a queue item')
			task = self.build_queue.popleft()
			task()
			call_again = True
		elif self.village_builder.tents_to_build > self.tents:
			if self.tents + 1 > 3 * len(self.fishers):
				if self.production_builder.enough_collectors():
					(details, success) = self.production_builder.build_fisher()
					if success:
						self.log.info('ai.tick: built a fisher')
						call_again = True
					elif details is not None:
						self.log.info('ai.tick: not enough materials to build a fisher')
						call_again = True
					else:
						self.log.info('ai.tick: failed to build a fisher')
				else:
					(details, success) = self.production_builder.improve_collector_coverage()
					if success:
						self.log.info('ai.tick: built a storage')
						call_again = True
					elif details is not None:
						self.log.info('ai.tick: not enough materials to build a storage')
						call_again = True
					else:
						self.log.info('ai.tick: failed to build a storage')
			else:
				(tent, success) = self.village_builder.build_tent()
				if success:
					self.log.info('ai.tick: built a tent')
					self.tents += 1
					call_again = True
				elif tent is not None:
					self.log.info('ai.tick: not enough materials to build a tent')
					call_again = True
				else:
					self.log.info('ai.tick: failed to build a tent')

		if call_again:
			Scheduler().add_new_object(Callback(self.tick), self, run_in = 32)
		else:
			self.log.info('ai.tick: everything is done')

	def report_success(self, mission, msg):
		print mission, msg
		if isinstance(mission, FoundSettlement):
			self.land_manager.settlement = mission.settlement
			self.village_builder = VillageBuilder(self.land_manager)
			self.village_builder.create_plan()
			self.production_builder = ProductionBuilder(self.land_manager, mission.branch_office)
			
			self.village_builder.display()
			self.production_builder.display()

			self.build_queue.append(self.village_builder.build_roads)
			self.build_queue.append(self.production_builder.build_lumberjack)
			self.build_queue.append(self.production_builder.build_lumberjack)
			self.build_queue.append(self.village_builder.build_main_square)
			Scheduler().add_new_object(Callback(self.tick), self, run_in = 32)

	def report_failure(self, mission, msg):
		print mission, msg

	def save(self, db):
		super(AIPlayer, self).save(db)
		# TODO: save to the db

	def _load(self, db, worldid):
		super(AIPlayer, self)._load(db, worldid)
		# TODO: load from the db
		Scheduler().add_new_object(Callback(self.__init), self)

	def start(self):
		found_settlement = FoundSettlement.create(self.ships.keys()[0], self.land_manager, self.report_success, self.report_failure)
		self.missions[FoundSettlement.__class__] = found_settlement
		found_settlement.start()

	def notify_unit_path_blocked(self, unit):
		self.log.warning("%s %s: ship blocked", self.__class__.__name__, self.worldid)

decorators.bind_all(AIPlayer)
