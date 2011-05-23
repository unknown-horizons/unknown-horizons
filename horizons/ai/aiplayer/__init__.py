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

class AIPlayer(GenericAI):
	"""This is the AI that builds settlements."""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'on_a_mission')

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, session, id, name, color, **kwargs):
		super(AIPlayer, self).__init__(session, id, name, color, **kwargs)
		self.log.info('created AI')
		Scheduler().add_new_object(Callback(self.start), self, run_in = 0)

	def report_result(self, mission, msg):
		print mission, msg

	def save(self, db):
		super(AIPlayer, self).save(db)
		# TODO: save to the db
		self.log.info('saved AI')

	def _load(self, db, worldid):
		super(AIPlayer, self)._load(db, worldid)
		# TODO: load from the db
		self.log.info('loaded AI')

	def start(self):
		self.missions = []
		ship = None
		for t in self.session.world.ships:
			if t.owner == self:
				ship = t
				break
		island = self.session.world.islands[0]
		self.missions.append(FoundSettlement.create(ship, island, self.report_result, self.report_result))
		for mission in self.missions:
			mission.start()
