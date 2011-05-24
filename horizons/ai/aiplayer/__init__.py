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

from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject, Circle
from horizons.constants import RES, UNITS, BUILDINGS
from horizons.ext.enum import Enum
from horizons.ai.generic import GenericAI
from horizons.world.storageholder import StorageHolder
from horizons.command.unit import CreateUnit
from horizons.world.units.ship import Ship
from horizons.world.units.movingobject import MoveNotPossible
from horizons.ai.aiplayer.mission.foundsettlement import FoundSettlement
from horizons.ai.aiplayer.land_manager import LandManager

class AIPlayer(GenericAI):
	"""This is the AI that builds settlements."""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'on_a_mission')

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, session, id, name, color, **kwargs):
		super(AIPlayer, self).__init__(session, id, name, color, **kwargs)
		Scheduler().add_new_object(Callback(self.__init), self)
		Scheduler().add_new_object(Callback(self.start), self, run_in = 2)

	def __init(self):
		self.ship = None
		for t in self.session.world.ships:
			if t.owner == self:
				self.ship = t
				break

		self.missions = {}
		self.island = self.session.world.islands[0]

		self.land_manager = LandManager(self.island, self)
		self.land_manager.divide()
		self.land_manager.display()

	def report_success(self, mission, msg):
		print mission, msg

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
		found_settlement = FoundSettlement.create(self.ship, self.island, self.report_success, self.report_failure)
		self.missions[FoundSettlement.__class__] = found_settlement
		found_settlement.start()

	def notify_unit_path_blocked(self, unit):
		self.log.warning("%s %s: ship blocked", self.__class__.__name__, self.worldid)
