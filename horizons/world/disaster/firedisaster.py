# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

from horizons.world.disaster import Disaster
from horizons.messaging import AddStatusIcon, RemoveStatusIcon, NewDisaster
from horizons.world.status import FireStatusIcon
from horizons.constants import GAME_SPEED, BUILDINGS, RES, TIER
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.util.worldobject import WorldObject

class FireDisaster(Disaster):
	"""Simulates a fire.

	Currently only affects settlers.
	Starts at a certain building and will spread out over time.

	"""

	TYPE = "The Flames Of The End"
	NOTIFICATION_TYPE = 'BUILDING_ON_FIRE'

	SEED_CHANCE = 0.005


	EXPANSION_RADIUS = 3

	# Defines the minimum number of pioneer or higher residences that need to be in a
	# settlement before this disaster can break loose
	MIN_PIONEERS_FOR_BREAKOUT = 7

	TIME_BEFORE_HAVOC = GAME_SPEED.TICKS_PER_SECOND * 30
	EXPANSION_TIME = (TIME_BEFORE_HAVOC // 2) - 1 # try twice before dying

	DISASTER_RES = RES.FIRE

	def __init__(self, settlement, manager):
		super(FireDisaster, self).__init__(settlement, manager)
		self._affected_buildings = []

	def save(self, db):
		super(FireDisaster, self).save(db)
		for building in self._affected_buildings:
			ticks = Scheduler().get_remaining_ticks(self, Callback(self.wreak_havoc, building), True)
			db("INSERT INTO fire_disaster(disaster, building, remaining_ticks_havoc) VALUES(?, ?, ?)",
			   self.worldid, building.worldid, ticks)

	def load(self, db, worldid):
		super(FireDisaster, self).load(db, worldid)
		for building_id, ticks in db("SELECT building, remaining_ticks_havoc FROM fire_disaster WHERE disaster = ?", worldid):
			# do half of infect()
			building = WorldObject.get_object_by_id(building_id)
			self.log.debug("%s loading disaster %s", self, building)
			self.infect(building, load=(db, worldid))

	def breakout(self):
		assert self.can_breakout(self._settlement)
		super(FireDisaster, self).breakout()
		possible_buildings = self._settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
		building = self._settlement.session.random.choice(possible_buildings)
		self.infect(building)
		self.log.debug("%s breakout out on %s at %s", self, building, building.position)

	@classmethod
	def can_breakout(cls, settlement):
		return settlement.owner.settler_level >= TIER.PIONEERS and \
		       settlement.count_buildings(BUILDINGS.RESIDENTIAL) > cls.MIN_PIONEERS_FOR_BREAKOUT

	def expand(self):
		if not self.evaluate():
			self._manager.end_disaster(self._settlement)
			self.log.debug("%s ending", self)
			# We are done here, time to leave
			return
		self.log.debug("%s still active, expanding..", self)
		for building in self._affected_buildings:
			for tile in self._settlement.get_tiles_in_radius(building.position, self.EXPANSION_RADIUS, False):
				if tile.object is not None and tile.object.id == BUILDINGS.RESIDENTIAL and tile.object not in self._affected_buildings:
					if self._settlement.session.random.random() <= self.SEED_CHANCE:
						self.infect(tile.object)
						return

	def end(self):
		Scheduler().rem_all_classinst_calls(self)

	def infect(self, building, load=None):
		"""Infect a building with fire.
		@load: (db, disaster_worldid), set on restoring infected state of savegame"""
		super(FireDisaster, self).infect(building, load=load)
		# keep in sync with load()
		AddStatusIcon.broadcast(building, FireStatusIcon(building))
		NewDisaster.broadcast(building.owner, building, FireDisaster)
		self._affected_buildings.append(building)
		havoc_time = self.TIME_BEFORE_HAVOC
		if load:
			db, worldid = load
			havoc_time = db("SELECT remaining_ticks_havoc FROM fire_disaster WHERE disaster = ? AND building = ?", worldid, building.worldid)[0][0]

		Scheduler().add_new_object(Callback(self.wreak_havoc, building), self, run_in=havoc_time)

	def recover(self, building):
		super(FireDisaster, self).recover(building)
		RemoveStatusIcon.broadcast(self, building, FireStatusIcon)
		Scheduler().rem_call(self, Callback(self.wreak_havoc, building))
		self._affected_buildings.remove(building)

	def evaluate(self):
		return len(self._affected_buildings) > 0

	def wreak_havoc(self, building):
		super(FireDisaster, self).wreak_havoc(building)
		self._affected_buildings.remove(building)
		building.make_ruin()
