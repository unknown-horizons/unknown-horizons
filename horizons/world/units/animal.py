# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import random
import weakref
import logging

import horizons.main

from horizons.world.production.producer import Producer
from horizons.util import Point, Circle, WorldObject
from horizons.world.pathfinding.pather import SoldierPather, BuildingCollectorPather
from collectors import Collector, BuildingCollector, JobList, Job
from horizons.constants import WILD_ANIMAL

class Animal(Producer):
	"""Base Class for all animals. An animal is a unit, that consumes resources (e.g. grass)
	and usually produce something (e.g. wool)."""
	log = logging.getLogger('world.units.animal')

	def __init__(self, **kwargs):
		super(Animal, self).__init__(**kwargs)

	def get_collectable_res(self):
		return self.get_needed_resources()

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

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

	def remove_stop_after_job(self):
		"""Let the animal continue as usual after the job. Can only be called
		after stop_after_job"""
		assert self.collector is not None
		self.collector = None

	def finish_working(self):
		# animal is done when it has eaten, and
		# doesn't have to get home, so end job right now
		print '%s finished WORKING' % self
		Collector.finish_working(self)
		self.end_job()

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		self.log.debug("CollectorAnimal %s search job", self.getId())
		if self.collector is not None:
			self.collector.pickup_animal()
			self.collector = None
			self.state = self.states.stopped
		else:
			super(CollectorAnimal, self).search_job()

	def get_home_inventory(self):
		return self.inventory


class WildAnimal(CollectorAnimal, Collector):
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

	# see documentation of self.health
	def __init__(self, island, start_hidden=False, can_reproduce = True, **kwargs):
		super(WildAnimal, self).__init__(start_hidden=start_hidden, **kwargs)
		self.__init(island, can_reproduce)
		self.log.debug("Wild animal %s created at "+str(self.position)+\
									 "; can_reproduce: %s; population now: %s", \
				self.getId(), can_reproduce, len(self.home_island.wild_animals))

	def __init(self, island, can_reproduce, health = None):
		"""
		@param island: Hard reference to island
		@param can_reproduce: bool
		@param health: int or None
		"""
		assert isinstance(can_reproduce, bool)
		# good health is the main target of an animal. it increases when they eat and
		# decreases, when they have no food. if it reaches 0, they die, and
		# if it reaches HEALTH_LEVEL_TO_REPRODUCE, they reproduce
		self.health = health if health is not None else WILD_ANIMAL.HEALTH_INIT_VALUE
		self.can_reproduce = can_reproduce
		self._home_island = weakref.ref(island)
		self.home_island.wild_animals.append(self)

	@property
	def home_island(self):
		return self._home_island()

	def save(self, db):
		super(WildAnimal, self).save(db)
		# save members
		db("INSERT INTO wildanimal(rowid, health, can_reproduce) VALUES(?, ?, ?)", \
			 self.getId(), self.health, int(self.can_reproduce))
		# set island as owner
		db("UPDATE unit SET owner = ? WHERE rowid = ?", self.home_island.getId(), self.getId())

		# save remaining ticks when in waiting state
		if self.state == self.states.no_job_waiting:
			calls = horizons.main.session.scheduler.get_classinst_calls(self,  \
																												self.handle_no_possible_job)
			assert(len(calls) == 1)
			remaining_ticks = calls.values()[0]
			db("UPDATE collector SET remaining_ticks = ? WHERE rowid = ?", \
				 remaining_ticks, self.getId())

	def load(self, db, worldid):
		super(WildAnimal, self).load(db, worldid)
		# get own properties
		health, can_reproduce = \
				db("SELECT health, can_reproduce FROM wildanimal WHERE rowid = ?", worldid)[0]
		# get home island
		home_island_id = db("SELECT owner FROM unit WHERE rowid = ?", worldid)[0][0]
		island = WorldObject.get_object_by_id(home_island_id)
		self.__init(island, bool(can_reproduce), health)

	def apply_state(self, state, remaining_ticks=None):
		super(WildAnimal, self).apply_state(state, remaining_ticks)
		if self.state == self.states.no_job_waiting:
			horizons.main.session.scheduler.add_new_object(self.handle_no_possible_job, self, \
																										 remaining_ticks)
		elif self.state == self.states.no_job_walking_randomly:
			self.add_move_callback(self.search_job)

	def handle_no_possible_job(self):
		"""Just walk to a random location nearby and search there for food, when we arrive"""
		self.log.debug('WildAnimal %s: no possible job; health: %s', self.getId(), self.health)
		# decrease health because of lack of food
		self.health -= WILD_ANIMAL.HEALTH_DECREASE_ON_NO_JOB
		if self.health <= 0:
			self.die()
			return

		# if can't find a job, we walk to a random location near us and search there
		target = self.get_random_location(self.walking_range)
		if target is not None:
			self.log.debug('WildAnimal %s: no possible job, walking to %s',self.getId(),str(target))
			self.move(target, callback=self.search_job)
			self.state = self.states.no_job_walking_randomly
		else:
			# we couldn't find a target, just try again 3 secs later
			self.log.debug('WildAnimal %s: no possible job, no possible new loc', self.getId())
			horizons.main.session.scheduler.add_new_object(self.handle_no_possible_job, self, 48)
			self.state = self.states.no_job_waiting

	def get_job(self):
		self.log.debug('WildAnimal %s: get_job' % self.getId())

		jobs = JobList(JobList.order_by.random)
		collectable_resources = self.get_needed_resources()

		# iterate over all possible providers and needed resources
		# and save possible job targets
		reach = Circle(self.position, self.walking_range)
		for provider in self.home_island.get_providers_in_range(reach):
			if self.check_possible_job_target(provider):
				for res in collectable_resources:
					job = self.check_possible_job_target_for(provider, res)
					if job is not None:
						jobs.append(job)

		return self.get_best_possible_job(jobs)

	def reroute(self):
		# when target is gone, search another one
		self.search_job()

	def end_job(self):
		super(WildAnimal, self).end_job()
		# check if we can reproduce
		self.log.debug("Wild animal %s end_job; health: %s", self.getId(), self.health)
		self.health += WILD_ANIMAL.HEALTH_INCREASE_ON_FEEDING
		if self.can_reproduce and self.health >= WILD_ANIMAL.HEALTH_LEVEL_TO_REPRODUCE:
			self.reproduce()
			self.health = WILD_ANIMAL.HEALTH_INIT_VALUE

	def reproduce(self):
		"""Create another animal of our type on the place where we stand"""
		if not self.can_reproduce:
			return

		self.log.debug("Wild animal %s REPRODUCING", self.getId())
		# create offspring
		horizons.main.session.entities.units[self.id](self.home_island, \
			x=self.position.x, y=self.position.y, \
			can_reproduce = self.next_clone_can_reproduce())
		# reset own resources
		for res in self.get_consumed_resources():
			self.inventory.reset(res)

	def next_clone_can_reproduce(self):
		"""Returns, wether the next child will be able to reproduce himself.
		Some animal can't reproduce, which makes population growth easier to control.
		@return: bool"""
		return bool(random.randint(0, 1))

	def die(self):
		"""Makes animal die, e.g. because of starvation or getting killed by herder"""
		self.log.debug("Wild animal %s dying", self.getId())
		self.home_island.wild_animals.remove(self)
		self.remove()

	def cancel(self):
		super(WildAnimal, self).cancel(continue_action=self.search_job)

	def __str__(self):
		return "%s(health=%s)" % (super(WildAnimal, self).__str__(), \
															self.health if hasattr(self, 'health') else None)


class FarmAnimal(CollectorAnimal, BuildingCollector):
	"""Animals that are bred and live in the surrounding area of a farm, such as sheep.
	They have a home_building, representing their farm; they usually feed on whatever
	the farm grows, and collectors from the farm can collect their produced resources.
	"""
	job_ordering = JobList.order_by.random
	grazingTime = 2

	def __init__(self, home_building, start_hidden=False, **kwargs):
		super(FarmAnimal, self).__init__(home_building = home_building, \
																 start_hidden = start_hidden, **kwargs)

	def register_at_home_building(self, unregister=False):
		if unregister:
			self.home_building.animals.remove(self)
		else:
			self.home_building.animals.append(self)

	def get_buildings_in_range(self):
		# we are only allowed to pick up at our pasture
		return [self.home_building]

	def begin_current_job(self):
		# we can only move on 1 building; simulate this by chosing a random location with
		# the building
		coords = self.job.object.position.get_coordinates()
		# usually, the animal stands "in" the building. but when the animalcollector gets it,
		# it's outside of it. therefore it happens, that the position isn't in the buildings coords.
		my_position = self.position.to_tuple()
		if my_position in coords:
			coords.remove(my_position)
		target_location = coords[ random.randint(0, len(coords)-1) ]
		target_location = Point(*target_location)
		super(FarmAnimal, self).begin_current_job(job_location=target_location)
