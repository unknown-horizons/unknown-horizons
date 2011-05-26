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

class AIPlayer(GenericAI):
	"""This is the AI that builds settlements."""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'on_a_mission')

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, session, id, name, color, **kwargs):
		super(AIPlayer, self).__init__(session, id, name, color, **kwargs)
		Scheduler().add_new_object(Callback(self.__init), self)
		Scheduler().add_new_object(Callback(self.start), self, run_in = 2)

	def __init(self):
		for ship in self.session.world.ships:
			if ship.owner == self:
				self.ships[ship] = self.shipStates.on_a_mission

		self.missions = {}
		self.island = self.session.world.islands[0]

		self.land_manager = LandManager(self.island, self)
		self.land_manager.divide()
		self.land_manager.display()

		self.complete_inventory = CompleteInventory(self)

	def build_tents(self):
		if self.village_builder.build_tent():
			self.log.info('Built a tent')
			Scheduler().add_new_object(Callback(self.build_tents), self, run_in = 16)
		else:
			self.log.info('All tents have been built')

	def report_success(self, mission, msg):
		print mission, msg
		if isinstance(mission, FoundSettlement):
			self.land_manager.settlement = mission.settlement
			self.village_builder = VillageBuilder(self.land_manager)
			self.village_builder.create_plan()
			self.village_builder.build_roads()
			self.village_builder.build_main_square()
			self.village_builder.display()
			Scheduler().add_new_object(Callback(self.build_tents), self)

			self.production_builder = ProductionBuilder(self.land_manager, mission.branch_office)
			self.production_builder.build_fisher()
			self.production_builder.build_fisher()
			self.production_builder.build_lumberjack()
			self.production_builder.build_lumberjack()
			self.production_builder.display()

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
