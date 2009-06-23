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

from horizons.world.production import SecondaryProducer, Provider
from horizons.world.pathfinding import Movement
from horizons.util import Point, Circle
from collectors import Collector, BuildingCollector

class Animal(SecondaryProducer):
	"""Base Class for all animals. An animal is a unit, that consumes resources (e.g. grass)
	and usually produce something (e.g. wool).

	Subclasses should inherit from Collector."""
	log = logging.getLogger('world.units.animal')

	def __init__(self, **kwargs):
		super(Animal, self).__init__(**kwargs)

	def create_collector(self):
		# no collector for our consumed resources
		pass

	def sort_jobs(self, jobs):
		# no intelligent job selection
		return self.sort_jobs_random(jobs)

	def get_collectable_res(self):
		return self.get_needed_res()

	def finish_working(self):
		# animal is done when it has eaten, and
		# doesn't have to get home, so end job right now
		Collector.finish_working(self)
		self.end_job()


class WildAnimal(Animal, Collector):
	"""Animals, that live in the nature and feed on natural resources.
	These animals can be hunted.

	They produce wild animal meat and feed on wild animal food x, which is produced by
	e.g. a tree.

	It is assumed, that they need all resources, that they use, for reproduction. If they have
	gathered all resources, and their inventory is full, they reproduce.
	"""
	movement = Movement.SOLDIER_MOVEMENT
	walking_range = 5
	WORK_DURATION = 48

	# see documentation of self.health
	HEALTH_INIT_VALUE = 10
	HEALTH_INCREASE_ON_FEEDING = 2
	HEALTH_DECREASE_ON_NO_JOB = 2
	HEALTH_LEVEL_TO_REPRODUCE = 30

	def __init__(self, island, start_hidden=False, can_reproduce = True, **kwargs):
		super(WildAnimal, self).__init__(start_hidden=start_hidden, **kwargs)
		self.__init(island, can_reproduce)
		self.log.debug("Wild animal %s created at "+str(self.position)+\
									 "; can_reproduce: %s; population now: %s", \
				self.getId(), can_reproduce, len(self.home_island.wild_animals))

	def __init(self, island, can_reproduce):
		# good health is the main target of an animal. it increases when they it and decreases, when
		# they have no food. if it reaches 0, they die, and if it reaches REPRODUCE_ON_HEALTH_LEVEL,
		# they reproduce
		self.health = self.HEALTH_INIT_VALUE
		self.can_reproduce = can_reproduce
		self._home_island = weakref.ref(island)
		self.home_island.wild_animals.append(self)

	@property
	def home_island(self):
		return self._home_island()

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

		# if we have a job, we walk to a random location near us and search there
		target = None
		found_possible_target = False
		possible_walk_targets = Circle(self.position, self.walking_range).get_coordinates()
		possible_walk_targets.remove(self.position.to_tuple())
		while not found_possible_target and len(possible_walk_targets) > 0:
			target_tuple = possible_walk_targets[random.randint(0, len(possible_walk_targets)-1)]
			possible_walk_targets.remove(target_tuple)
			target = Point(*target_tuple)
			self.log.debug('WildAnimal %s: checking random loc: %s %s', \
										 self.getId(), target_tuple[0], target_tuple[1])
			found_possible_target = self.check_move(target)
			# temporary hack to make sure that animal doesn't leave island (necessary until
			# SOLDIER_MOVEMENT is fully implemented and working)
			if found_possible_target:
				#assert horizons.main.session.world.get_island(target.x, target.y) is not None
				if horizons.main.session.world.get_island(target.x, target.y) is None:
					found_possible_target = False
		if found_possible_target:
			self.log.debug('WildAnimal %s: no possible job, walking to %s',self.getId(),str(target))
			self.move(target, callback=self.search_job)
		else:
			# we couldn't find a target, just try again 3 secs later
			self.log.debug('WildAnimal %s: no possible job, no possible new loc', self.getId())
			horizons.main.session.scheduler.add_new_object(self.handle_no_possible_job, self, 48)

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
		self.log.debug("Wild animal %s health: %s", self.getId(), self.health)
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
		# remove reference and leave animal as is - gc will do the rest
		self.home_island.wild_animals.remove(self)
		#self.__del__()

		""" old code, kept for now:
	def __del__(self):
		del self.health
		del self.can_reproduce
		super(WildAnimal, self).__del__()
		"""


class FarmAnimal(Animal, BuildingCollector):
	"""Animals that are bred and live in the surrounding area of a farm, such as sheep.
	They have a home_building, representing their farm; they usually feed on whatever
	the farm grows, and collectors from the farm can collect their produced resources.
	"""
	grazingTime = 2
	movement = Movement.COLLECTOR_MOVEMENT

	def __init__(self, home_building, start_hidden=False, **kwargs):
		super(FarmAnimal, self).__init__(home_building = home_building, \
																 start_hidden = start_hidden, **kwargs)
		self.__init()

	def __init(self):
		self.collector = None

	def register_at_home_building(self):
		self.home_building().animals.append(self)

	def save(self, db):
		super(FarmAnimal, self).save(db)

	def load(self, db, worldid):
		super(FarmAnimal, self).load(db, worldid)
		self.__init()

	def setup_new_job(self):
		self.job.object._Provider__collectors.append(self)

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		self.log.debug("FarmAnimal %s search job", self.getId())
		if self.collector is not None:
			self.collector.pickup_animal()
			self.collector = None
			self.state = self.states.stopped
		else:
			super(FarmAnimal, self).search_job()

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

