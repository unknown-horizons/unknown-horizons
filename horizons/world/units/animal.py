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

import logging

from horizons.scheduler import Scheduler

from horizons.util.pathfinding.pather import SoldierPather
from horizons.util.shapes import Point
from horizons.util.worldobject import WorldObject
from horizons.world.units.collectors import Collector, BuildingCollector, JobList
from horizons.constants import GAME_SPEED
from horizons.world.units.movingobject import MoveNotPossible
from horizons.component.storagecomponent import StorageComponent
from horizons.world.resourcehandler import ResourceHandler
from horizons.world.units.unit import Unit

class Animal(ResourceHandler):
	"""Base Class for all animals. An animal is a unit, that consumes resources (e.g. grass)
	and usually produce something (e.g. wool, meat)."""
	log = logging.getLogger('world.units.animal')

	def __init__(self, *args, **kwargs):
		super(Animal, self).__init__(*args, **kwargs)

class CollectorAnimal(Animal):
	"""Animals that will inherit from collector"""
	def __init__(self, **kwargs):
		super(CollectorAnimal, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		self.collector = None

	def load(self, db, worldid):
		self.__init()
		super(CollectorAnimal, self).load(db, worldid)

	def apply_state(self, state, remaining_ticks=None):
		super(CollectorAnimal, self).apply_state(state, remaining_ticks)
		if self.state == self.states.no_job_walking_randomly:
			self.add_move_callback(self.search_job)

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

	def remove_stop_after_job(self):
		"""Let the animal continue as usual after the job. Can only be called
		after stop_after_job"""
		assert self.collector is not None
		self.collector = None

	def has_collectors(self):
		"""Whether this unit is just now or about to be collected"""
		return self.collector is not None or self.state == self.states.waiting_for_herder

	def finish_working(self):
		# animal is done when it has eaten, and
		# doesn't have to get home, so end job right now
		Collector.finish_working(self)
		self.end_job()

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		self.log.debug("%s search job", self)
		if self.collector is not None:
			# tell the animalcollector to pick me up
			collector = self.collector
			self.collector = None
			collector.pickup_animal()
			self.state = self.states.waiting_for_herder
		else:
			super(CollectorAnimal, self).search_job()

	def get_home_inventory(self):
		return self.get_component(StorageComponent).inventory

	def get_collectable_res(self):
		return self.get_needed_resources()

class WildAnimal(Animal, Unit):
	"""Animals, that live in the nature and feed on natural resources.
	These animals can be hunted.

	They produce wild animal meat and feed on wild animal food x, which is produced by
	e.g. a tree.

	It is assumed, that they need all resources, that they use, for reproduction. If they have
	gathered all resources, and their inventory is full, they reproduce.
	"""
	walking_range = 6
	work_duration = 96
	pather_class = SoldierPather

	def __init__(self, owner, start_hidden=False, **kwargs):
		super(WildAnimal, self).__init__(start_hidden=start_hidden, owner=owner, **kwargs)
		self.__init(owner)
		self.log.debug("Wild animal %s created at " + str(self.position) +
		               "; population now: %s",
				self.worldid, len(self.home_island.wild_animals))

	def __init(self, island):
		"""
		@param island: Hard reference to island
		"""
		self.home_island = island
		self.home_island.wild_animals.append(self)
		self.collector = None
		self.waiting_for_job = False

		self.move_randomly()

	def die(self):
		"""Makes animal die, e.g. because of starvation or getting killed by herder"""
		self.log.debug("%s dying", self)
		self.home_island.wild_animals.remove(self)
		self.remove()

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

	def remove_stop_after_job(self):
		"""Let the animal continue as usual after the job. Can only be called
		after stop_after_job"""
		assert self.collector is not None
		self.collector = None
		self.move_randomly()

	def has_collectors(self):
		"""Whether this unit is just now or about to be collected"""
		return self.collector is not None

	def save(self, db):
		super(WildAnimal, self).save(db)
		# save members
		db("INSERT INTO wildanimal(rowid) VALUES(?)",
			 self.worldid, self.health, int(self.can_reproduce))
		# set island as owner
		db("UPDATE unit SET owner = ? WHERE rowid = ?", self.home_island.worldid, self.worldid)

		# save remaining ticks when in waiting state
		if self.waiting_for_job:
			calls = Scheduler().get_classinst_calls(self, self.handle_no_possible_job)
			assert len(calls) == 1, 'calls: %s' % calls
			remaining_ticks = max(calls.values()[0], 1) # we have to save a number > 0
			db("UPDATE collector SET remaining_ticks = ? WHERE rowid = ?",
				 remaining_ticks, self.worldid)

	def load(self, db, worldid):
		super(WildAnimal, self).load(db, worldid)
		# get home island
		island = WorldObject.get_object_by_id(db.get_unit_owner(worldid))
		self.__init(island)

	def apply_state(self, state, remaining_ticks=None):
		super(WildAnimal, self).apply_state(state, remaining_ticks)
		if self.state == self.states.no_job_waiting:
			Scheduler().add_new_object(self.handle_no_possible_job, self, remaining_ticks)

	def move_randomly(self):
		"""Just walk to a random location nearby and search there for food, when we arrive"""
		self.log.debug('%s: searching for random move position', self)
		self.waiting_for_job = False

		if self.collector is not None:
			# tell the animalcollector to pick me up
			collector = self.collector
			self.collector = None
			collector.pickup_animal()
			return

		# if can't find a job, we walk to a random location near us and search there
		random = self.session.random.random()
		(target, path) = self.get_random_location(self.walking_range)
		if random < 0.5:
			(target, path) = self.get_random_location(self.walking_range)
			if target is not None:
				self.log.debug('%s: walking to %s', self, str(target))
				self.move(target, callback=self.move_randomly, path=path)
				return
		# we couldn't find a target, just chill for a moment
		self.log.debug('%s: no possible new loc', self)
		Scheduler().add_new_object(self.move_randomly, self, GAME_SPEED.TICKS_PER_SECOND*3)
		self.waiting_for_job = True

	def get_home_inventory(self):
		return self.get_component(StorageComponent).inventory

	def __str__(self):
		return "%s(health=%s)" % (super(WildAnimal, self).__str__(),
		                          getattr(self, 'health', None))


class FarmAnimal(CollectorAnimal, BuildingCollector):
	"""Animals that are bred and live in the surrounding area of a farm, such as sheep.
	They have a home_building, representing their farm; they usually feed on whatever
	the farm grows, and collectors from the farm can collect their produced resources.
	"""
	job_ordering = JobList.order_by.random

	def __init__(self, home_building, start_hidden=False, **kwargs):
		super(FarmAnimal, self).__init__(home_building=home_building,
		                                 start_hidden=start_hidden, **kwargs)

	def register_at_home_building(self, unregister=False):
		if unregister:
			self.home_building.animals.remove(self)
		else:
			self.home_building.animals.append(self)

	def get_buildings_in_range(self, reslist=None):
		# we are only allowed to pick up at our pasture
		return [self.home_building]

	def _get_random_positions_on_object(self, obj):
		"""Returns a shuffled list of tuples, that are in obj, but not in self.position"""
		coords = obj.position.get_coordinates()
		my_position = self.position.to_tuple()
		if my_position in coords:
			coords.remove(my_position)
		self.session.random.shuffle(coords)
		return coords

	def begin_current_job(self):
		# we can only move on 1 building; simulate this by choosing a random location with
		# the building
		coords = self._get_random_positions_on_object(self.job.object)

		# move to first walkable target coord we find
		for coord in coords:
			# job target is walkable, so at least one coord of it has to be
			# so we can safely assume, that we will find a walkable coord
			target_location = Point(*coord)
			if self.check_move(target_location):
				super(FarmAnimal, self).begin_current_job(job_location=target_location)
				return
		assert False

	def handle_no_possible_job(self):
		"""Walk around on field, search again, when we arrive"""
		for coord in self._get_random_positions_on_object(self.home_building):
			try:
				self.move(Point(*coord), callback=self.search_job)
				self.state = self.states.no_job_walking_randomly
				return
			except MoveNotPossible:
				pass
		# couldn't find location, so don't move
		super(FarmAnimal, self).handle_no_possible_job()
