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

from horizons.world.production import SecondaryProduction
from horizons.world.provider import Provider
from horizons.util import Point, Circle, WorldObject
from horizons.world.pathfinding.pather import SoldierPather, BuildingCollectorPather
from collectors import Collector, BuildingCollector

class Animal(SecondaryProduction):
	"""Base Class for all animals. An animal is a unit, that consumes resources (e.g. grass)
	and usually produce something (e.g. wool)."""
	log = logging.getLogger('world.units.animal')

	def __init__(self, **kwargs):
		super(Animal, self).__init__(**kwargs)

	def create_collector(self):
		# no collector for our consumed resources
		pass

	def get_collectable_res(self):
		return self.get_needed_res()

class CollectorAnimal(Animal):
	"""Animals that will inherit from collector"""
	def __init__(self, **kwargs):
		super(CollectorAnimal, self).__init__(**kwargs)
		self.__init()

	def sort_jobs(self, jobs):
		# no intelligent job selection
		return self.sort_jobs_random(jobs)

	def __init(self):
		self.collector = None

	def load(self, db, worldid):
		self.__init()
		super(CollectorAnimal, self).load(db, worldid)

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

	def finish_working(self):
		# animal is done when it has eaten, and
		# doesn't have to get home, so end job right now
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


class WildAnimal(CollectorAnimal, Collector):
	"""Animals, that live in the nature and feed on natural resources.
	These animals can be hunted.

	They produce wild animal meat and feed on wild animal food x, which is produced by
	e.g. a tree.

	It is assumed, that they need all resources, that they use, for reproduction. If they have
	gathered all resources, and their inventory is full, they reproduce.
	"""
	walking_range = 5
	WORK_DURATION = 48

	# see documentation of self.health
	HEALTH_INIT_VALUE = 10
	HEALTH_INCREASE_ON_FEEDING = 2
	HEALTH_DECREASE_ON_NO_JOB = 3
	HEALTH_LEVEL_TO_REPRODUCE = 50

	def __init__(self, island, start_hidden=False, can_reproduce = True, **kwargs):
		super(WildAnimal, self).__init__(start_hidden=start_hidden, **kwargs)
		self.__init(island, can_reproduce)
		self.log.debug("Wild animal %s created at "+str(self.position)+\
									 "; can_reproduce: %s; population now: %s", \
				self.getId(), can_reproduce, len(self.home_island.wild_animals))

	def __init(self, island, can_reproduce, health = None):
		# good health is the main target of an animal. it increases when they eat and
		# decreases, when they have no food. if it reaches 0, they die, and
		# if it reaches REPRODUCE_ON_HEALTH_LEVEL, they reproduce
		self.health = health if health is not None else self.HEALTH_INIT_VALUE
		self.can_reproduce = can_reproduce
		self._home_island = weakref.ref(island)
		self.home_island.wild_animals.append(self)

	@property
	def home_island(self):
		return self._home_island()

	def save(self, db):
		super(WildAnimal, self).save(db)
		#import pdb ; pdb.set_trace()
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
		#import pdb ; pdb.set_trace()
		super(WildAnimal, self).load(db, worldid)
		# get own properties
		health, can_reproduce = \
				db("SELECT health, can_reproduce FROM wildanimal WHERE rowid = ?", worldid)[0]
		# get home island
		home_island_id = db("SELECT owner FROM unit WHERE rowid = ?", worldid)[0]
		island = WorldObject.get_object_by_id(home_island_id)
		self.__init(island, bool(can_reproduce), health)

	def apply_state(self, state, remaining_ticks=None):
		super(WildAnimal, self).apply_state(state, remaining_ticks)
		if self.state == self.states.no_job_waiting:
			horizons.main.session.scheduler.add_new_object(self.handle_no_possible_job, self, \
																										 remaining_ticks)
		elif self.state == self.states.no_job_walking_randomly:
			self.add_move_callback(self.search_job)

	def get_home_inventory(self):
		return self.inventory

	def handle_no_possible_job(self):
		"""Just walk to a random location nearby and search there for food, when we arrive"""
		self.log.debug('WildAnimal %s: no possible job; health: %s', self.getId(), self.health)

		# decrease health because of lack of food
		self.health -= self.HEALTH_DECREASE_ON_NO_JOB
		if self.health <= 0:
			self.die()
			return

		# if can't find a job, we walk to a random location near us and search there
		self.log.debug('WildAnimal %s: get_rand_loc start',self.getId())
		target = self.get_random_location_in_range()
		self.log.debug('WildAnimal %s: get_rand_loc end',self.getId())
		if target is not None:
			self.log.debug('WildAnimal %s: no possible job, walking to %s',self.getId(),str(target))
			self.move(target, callback=self.search_job)
			self.state = self.states.no_job_walking_randomly
		else:
			# we couldn't find a target, just try again 3 secs later
			self.log.debug('WildAnimal %s: no possible job, no possible new loc', self.getId())
			horizons.main.session.scheduler.add_new_object(self.handle_no_possible_job, self, 48)
			self.state = self.states.no_job_waiting

	def get_random_location_in_range(self):
		"""Returns a random location in walking_range, that we can find a path to
		@return: Instance of Point or None"""
		target = None
		found_possible_target = False
		possible_walk_targets = Circle(self.position, self.walking_range).get_coordinates()
		possible_walk_targets.remove(self.position.to_tuple())

		while not found_possible_target and len(possible_walk_targets) > 0:
			target_tuple = possible_walk_targets[random.randint(0, len(possible_walk_targets)-1)]
			possible_walk_targets.remove(target_tuple)
			target = Point(*target_tuple)
			found_possible_target = self.check_move(target)
			# temporary hack to make sure that animal doesn't leave island (necessary until
			# SOLDIER_MOVEMENT is fully implemented and working)
			if found_possible_target:
				#assert horizons.main.session.world.get_island(target.x, target.y) is not None
				if horizons.main.session.world.get_island(target.x, target.y) is None:
					self.log.warning("WildAnimal %s tried to walk on a tile, that is not on an island!", self.getId())
					found_possible_target = False

		if found_possible_target:
			return target
		else:
			return None

	def get_job(self):
		self.log.debug('WildAnimal %s: get_job' % self.getId())

		jobs = [] # list of possible jobs
		needed_resources = self.get_needed_res()

		# iterate over all possible providers and needed resources
		# and save possible job targets
		for provider in self.get_providers_in_range():
			for res in needed_resources:
				job = self.check_possible_job_target(provider, res)
				if job is not None:
					jobs.append(job)

		return self.get_best_possible_job(jobs)

	def reroute(self):
		# when target is gone, search another one
		self.search_job()

	def get_providers_in_range(self):
		"""Returns all producers in the range of the animal. Useful when searching for food"""
		return [ b for b in self.home_island.buildings if \
						 isinstance(b, Provider) and \
						 self.position.distance(b.position) <= self.walking_range ]

	def end_job(self):
		super(WildAnimal, self).end_job()
		# check if we can reproduce
		self.log.debug("Wild animal %s end_job; health: %s", self.getId(), self.health)
		self.health += self.HEALTH_INCREASE_ON_FEEDING
		if self.health >= self.HEALTH_LEVEL_TO_REPRODUCE:
			self.reproduce()
			self.health = self.HEALTH_INIT_VALUE

	def reproduce(self):
		"""Create another animal of our type on the place where we stand"""
		if not self.can_reproduce:
			return

		self.log.debug("Wild animal %s REPRODUCING", self.getId())
		# create offspring
		horizons.main.session.entities.units[self.id](self.home_island, \
			x=self.position.x, y=self.position.y, \
			can_reproduce = self.next_clone_can_reproduce())
		# reset resources
		for res in self.get_consumed_res():
			self.inventory.reset(res)

	def next_clone_can_reproduce(self):
		"""Returns, wether the next child will be able to reproduce himself.
		Some animal can't reproduce, which makes population growth easier to control."""
		while True:
			yield True
			yield False

	def die(self):
		"""Makes animal die, e.g. because of starvation"""
		self.log.debug("Wild animal %s dying", self.getId())
		# we don't do anything here, just remove reference and
		# leave animal as is - garbage collection will do the rest
		self.home_island.wild_animals.remove(self)

	def create_pather(self):
		return SoldierPather(self)

	def cancel(self):
		if self.job.object is not None:
			self.job.object._Provider__collectors.remove(self)
		self.get_job()


class FarmAnimal(CollectorAnimal, BuildingCollector):
	"""Animals that are bred and live in the surrounding area of a farm, such as sheep.
	They have a home_building, representing their farm; they usually feed on whatever
	the farm grows, and collectors from the farm can collect their produced resources.
	"""
	grazingTime = 2
	def __init__(self, home_building, start_hidden=False, **kwargs):
		super(FarmAnimal, self).__init__(home_building = home_building, \
																 start_hidden = start_hidden, **kwargs)

	def register_at_home_building(self, unregister=False):
		if unregister:
			self.home_building().animals.remove(self)
		else:
			self.home_building().animals.append(self)

	def setup_new_job(self):
		self.job.object._Provider__collectors.append(self)

	def create_pather(self):
		return BuildingCollectorPather(self)
