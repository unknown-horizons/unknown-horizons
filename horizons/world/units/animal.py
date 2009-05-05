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

import horizons.main

from horizons.world.production import SecondaryProducer
from horizons.world.pathfinding import Movement
from horizons.util import Rect, Point, WorldObject, Circle
from unit import Unit
from collectors import Collector, BuildingCollector, Job
from nature import GrowingUnit

class Animal(GrowingUnit, SecondaryProducer):
	"""Base Class for all animals. An animal is a unit, that consumes resources (e.g. grass)
	and usually produce something (e.g. wool)."""
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


class WildAnimal(Animal, Collector):
	"""Animals, that live in the nature and feed on natural resources.
	These animals can be hunted."""
	movement = Movement.SOLDIER_MOVEMENT
	walking_range = 5

	def __init__(self, island, start_hidden=False, **kwargs):
		super(WildAnimal, self).__init__(start_hidden=start_hidden, **kwargs)
		self.__init(island)

	def __init(self, island):
		self._home_island = weakref.ref(island)
		self.home_island.wild_animals.append(self)

	@property
	def home_island(self):
		return self._home_island()

	def get_home_inventory(self):
		return self.inventory

	def get_buildings_in_range(self):
		buildings = []
		from horizons.world.provider import Provider
		# collect all providers in the surrounding circle (=animal range)
		for tile in self.home_island.get_surrounding_tiles(self.position, self.walking_range):
			if isinstance(tile.object, Provider):
				buildings.append(tile.object)
		return buildings

	def handle_no_possible_job(self):
		"""Just walk to a random location nearby and search there for food, when we arrive"""
		if horizons.main.debug: print 'WildAnimal %s: no possible job' % self.getId()
		# if we have a job, we walk to a random location near us and search there
		target = None
		found_possible_target = False
		possible_walk_targets = Circle(self.position, self.walking_range).get_coordinates()
		endless_loop_prevention = 20 # if this var reaches 0, we give up searching for a path
		while not found_possible_target and endless_loop_prevention > 0:
			endless_loop_prevention -= 1
			target = Point(*possible_walk_targets[random.randint(0, len(possible_walk_targets)-1)])
			found_possible_target = self.check_move(target)
			# temporary hack to make sure that animal doesn't leave island (necessary until
			# SOLDIER_MOVEMENT is fully implemented and working)
			if horizons.main.session.world.get_island(target.x, target.y) is None:
				found_possible_target = False
		if found_possible_target:
			self.move(target, callback=self.search_job)
		else:
			# we couldn't find a target, just try again 3 secs later
			horizons.main.session.scheduler.add_new_object(self.handle_no_possible_job, self, 48)

	def get_job(self):
		if horizons.main.debug: print 'WildAnimal %s: get_job' % self.getId()
		return None

	def reroute(self):
		# when target is gone, search another one
		self.search_job()


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

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		if self.collector is not None:
			self.collector.pickup_animal()
			self.collector = None
			self.state = self.states.stopped
		else:
			super(FarmAnimal, self).search_job()

	def setup_new_job(self):
		self.job.object._Provider__collectors.append(self)

	def finish_working(self):
		#print self.id, 'FINISH WORKING'
		# transfer ressources
		self.transfer_res()
		# deregister at the target we're at
		self.job.object._Provider__collectors.remove(self)
		self.end_job()

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

