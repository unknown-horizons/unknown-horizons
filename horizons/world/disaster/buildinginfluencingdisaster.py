# ###################################################
# Copyright (C) 2013-2017 The Unknown Horizons Team
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

from typing import TYPE_CHECKING, Type

from horizons.constants import BUILDINGS, GAME_SPEED, TIER
from horizons.messaging import AddStatusIcon, NewDisaster, RemoveStatusIcon
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.util.worldobject import WorldObject
from horizons.world.disaster import Disaster

if TYPE_CHECKING:
	from horizons.world.status import StatusIcon


class BuildingInfluencingDisaster(Disaster):
	"""Simulates a building influencing disaster.

	Starts at a certain building and will spread out over time.

	"""

	# Defines the building type that should be influenced, by default it infects the residents of a settlement
	BUILDING_TYPE = BUILDINGS.RESIDENTIAL

	# Defines the minimum tier a settlement needs before this disaster can break out, by default its the PIONEER tier
	MIN_BREAKOUT_TIER = TIER.PIONEERS

	# Defines the minimum number of pioneer or higher residences that need to be in a
	# settlement before this disaster can break loose
	MIN_INHABITANTS_FOR_BREAKOUT = 5

	# Defines the status icon for the influenced BUILDING_TYPE
	STATUS_ICON = None # type: Type[StatusIcon]

	# Defines building type that consumes resources of type DISASTER_RES
	RESCUE_BUILDING_TYPE = None # type: int

	# In a range of how many tiles can the disaster spread?
	EXPANSION_RADIUS = 0

	TIME_BEFORE_HAVOC = GAME_SPEED.TICKS_PER_SECOND * 30
	# By default, try twice before disasterying
	EXPANSION_TIME = (TIME_BEFORE_HAVOC // 2) - 1

	def __init__(self, settlement, manager):
		super().__init__(settlement, manager)
		self._affected_buildings = []

	def save(self, db):
		super().save(db)
		for building in self._affected_buildings:
			ticks = Scheduler().get_remaining_ticks(self, Callback(self.wreak_havoc, building), True)
			db("INSERT INTO building_influencing_disaster(disaster, building, remaining_ticks_havoc) VALUES(?, ?, ?)",
			   self.worldid, building.worldid, ticks)

	def load(self, db, worldid):
		super().load(db, worldid)
		for building_id, ticks in db("SELECT building, remaining_ticks_havoc FROM building_influencing_disaster WHERE disaster = ?", worldid):
			# do half of infect()
			building = WorldObject.get_object_by_id(building_id)
			self.log.debug("%s loading disaster %s", self, building)
			self.infect(building, load=(db, worldid))

	def breakout(self):
		assert self.can_breakout(self._settlement)
		super().breakout()
		possible_buildings = self._settlement.buildings_by_id[self.BUILDING_TYPE]
		building = self._settlement.session.random.choice(possible_buildings)
		self.infect(building)
		self.log.debug("%s breakout out on %s at %s", self, building, building.position)

	@classmethod
	def can_breakout(cls, settlement):
		return settlement.owner.settler_level >= cls.MIN_BREAKOUT_TIER and \
		       settlement.count_buildings(cls.BUILDING_TYPE) > cls.MIN_INHABITANTS_FOR_BREAKOUT

	def expand(self):
		if not self.evaluate():
			self._manager.end_disaster(self._settlement)
			self.log.debug("%s ending", self)
			# We are done here, time to leave
			return
		self.log.debug("%s still active, expanding..", self)
		for building in self._affected_buildings:
			for tile in self._settlement.get_tiles_in_radius(building.position, self.EXPANSION_RADIUS, False):
				if tile.object is None or tile.object.id != self.BUILDING_TYPE:
					continue
				if tile.object in self._affected_buildings:
					continue
				if self._settlement.session.random.random() <= self.SEED_CHANCE:
					self.infect(tile.object)
					return

	def end(self):
		Scheduler().rem_all_classinst_calls(self)

	def infect(self, building, load=None):
		"""@load: (db, disaster_worldid), set on restoring infected state of savegame"""
		super().infect(building, load=load)
		self._affected_buildings.append(building)
		havoc_time = self.TIME_BEFORE_HAVOC
		# keep in sync with load()
		if load:
			db, worldid = load
			havoc_time = db("SELECT remaining_ticks_havoc FROM building_influencing_disaster WHERE disaster = ? AND building = ?", worldid, building.worldid)[0][0]
		Scheduler().add_new_object(Callback(self.wreak_havoc, building), self, run_in=havoc_time)
		AddStatusIcon.broadcast(building, self.STATUS_ICON(building))
		NewDisaster.broadcast(building.owner, building, self.__class__, self)

	def recover(self, building):
		super().recover(building)
		RemoveStatusIcon.broadcast(self, building, self.STATUS_ICON)
		callback = Callback(self.wreak_havoc, building)
		Scheduler().rem_call(self, callback)
		self._affected_buildings.remove(building)

	def evaluate(self):
		return len(self._affected_buildings) > 0

	def wreak_havoc(self, building):
		super().wreak_havoc(building)
		self._affected_buildings.remove(building)
