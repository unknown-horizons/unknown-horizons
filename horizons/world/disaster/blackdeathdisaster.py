# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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
from horizons.world.status import BlackDeathStatusIcon
from horizons.constants import GAME_SPEED, BUILDINGS, RES, TIER
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.util.worldobject import WorldObject
import random

class BlackDeathDisaster(Disaster):
	"""Simulates the Black Death.

	Currently only affects settlers.
	Starts at a certain building and will spread out over time.

	"""

	TYPE = "Happy dying."
	NOTIFICATION_TYPE = 'BUILDING_INFECTED_BY_BLACK_DEATH'

	SEED_CHANCE = 0.01


	EXPANSION_RADIUS = 7

	# Defines the minimum number of pioneer or higher residences that need to be in a
	# settlement before this disaster can break loose
	MIN_SETTLERS_FOR_BREAKOUT = 15

	TIME_BEFORE_HAVOC = GAME_SPEED.TICKS_PER_SECOND * 4
	EXPANSION_TIME = TIME_BEFORE_HAVOC // 2 # try twice before dying

	DISASTER_RES = RES.BLACKDEATH

	def __init__(self, settlement, manager):
		super(BlackDeathDisaster, self).__init__(settlement, manager)
		self._affected_buildings = []

	def save(self, db):
		super(BlackDeathDisaster, self).save(db)
		for building in self._affected_buildings:
			ticks = Scheduler().get_remaining_ticks(self, Callback(self.wreak_havoc, building), True)
			db("INSERT INTO black_death_disaster(disaster, building, remaining_ticks_havoc) VALUES(?, ?, ?)",
			   self.worldid, building.worldid, ticks)

	def load(self, db, worldid):
		super(BlackDeathDisaster, self).load(db, worldid)
		for building_id, ticks in db("SELECT building, remaining_ticks_havoc FROM BlackDeathDisaster WHERE disaster = ?", worldid):
			# do half of infect()
			building = WorldObject.get_object_by_id(building_id)
			self.log.debug("%s loading disaster %s", self, building)
			self.infect(building, load=(db, worldid))

	def breakout(self):
		assert self.can_breakout(self._settlement)
		super(BlackDeathDisaster, self).breakout()
		possible_buildings = self._settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]
		building = self._settlement.session.random.choice(possible_buildings)
		self.infect(building)
		self.log.debug("%s breakout out on %s at %s", self, building, building.position)

	@classmethod
	def can_breakout(cls, settlement):
		return settlement.owner.settler_level >= TIER.SETTLERS and \
		       settlement.count_buildings(BUILDINGS.RESIDENTIAL) > cls.MIN_SETTLERS_FOR_BREAKOUT

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
		"""Infect a building with the black death.
		@load: (db, disaster_worldid), set on restoring infected state of savegame"""
		super(BlackDeathDisaster, self).infect(building, load=load)
		# keep in sync with load()
		AddStatusIcon.broadcast(building, BlackDeathStatusIcon(building))
		NewDisaster.broadcast(building.owner, building, BlackDeathDisaster)
		self._affected_buildings.append(building)
		havoc_time = self.TIME_BEFORE_HAVOC
		if load:
			db, worldid = load
			havoc_time = db("SELECT remaining_ticks_havoc FROM black_death_disaster WHERE disaster = ? AND building = ?", worldid, building.worldid)[0][0]
		print "infect 2"
		Scheduler().add_new_object(Callback(self.wreak_havoc, building), self, run_in=havoc_time)

	def recover(self, building):
		super(BlackDeathDisaster, self).recover(building)
		RemoveStatusIcon.broadcast(self, building, BlackDeathStatusIcon)
		Scheduler().rem_call(self, Callback(self.wreak_havoc, building))
		self._affected_buildings.remove(building)

	def evaluate(self):
		return len(self._affected_buildings) > 0

	def wreak_havoc(self, building):
		"""Some inhabitants have to die."""
		super(BlackDeathDisaster, self).wreak_havoc(building)
		self._affected_buildings.remove(building)
		if building.inhabitants > 1:
			inhabitants_that_will_die = random.randint(1, building.inhabitants)
			building.inhabitants -= inhabitants_that_will_die
			self.log.debug("%s inhabitants dying", inhabitants_that_will_die)
