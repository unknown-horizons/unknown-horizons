# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.command.unit import CreateUnit
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import RES, WILD_ANIMAL
from horizons.scheduler import Scheduler
from horizons.util.pathfinding.pather import SoldierPather
from horizons.util.worldobject import WorldObject
from horizons.world.resourcehandler import ResourceHandler
from horizons.world.units.collectors import Collector, Job


class Animal(ResourceHandler):
	"""Base Class for all animals. An animal is a unit, that consumes resources (e.g. grass)
	and usually produce something (e.g. wool, meat)."""
	log = logging.getLogger('world.units.animal')

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class CollectorAnimal(Animal):
	"""Animals that will inherit from collector"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.__init()

	def __init(self):
		self.collector = None

	def load(self, db, worldid):
		self.__init()
		super().load(db, worldid)

	def apply_state(self, state, remaining_ticks=None):
		super().apply_state(state, remaining_ticks)
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
			super().search_job()

	def get_home_inventory(self):
		return self.get_component(StorageComponent).inventory

	def get_collectable_res(self):
		return self.get_needed_resources()


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

	def __init__(self, owner, start_hidden=False, can_reproduce=True, **kwargs):
		super().__init__(start_hidden=start_hidden, owner=owner, **kwargs)
		self.__init(owner, can_reproduce)
		self.log.debug("Wild animal %s created at " + str(self.position) +
		               "; can_reproduce: %s; population now: %s",
				self.worldid, can_reproduce, len(self.home_island.wild_animals))

	def __init(self, island, can_reproduce, health=None):
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
		self.home_island = island
		self.home_island.wild_animals.append(self)

		resources = self.get_needed_resources()
		assert resources in [[RES.WILDANIMALFOOD], []]
		self._required_resource_id = RES.WILDANIMALFOOD
		self._building_index = self.home_island.get_building_index(self._required_resource_id)

	def save(self, db):
		super().save(db)
		# save members
		db("INSERT INTO wildanimal(rowid, health, can_reproduce) VALUES(?, ?, ?)",
			 self.worldid, self.health, int(self.can_reproduce))
		# set island as owner
		db("UPDATE unit SET owner = ? WHERE rowid = ?", self.home_island.worldid, self.worldid)

		# save remaining ticks when in waiting state
		if self.state == self.states.no_job_waiting:
			calls = Scheduler().get_classinst_calls(self, self.handle_no_possible_job)
			assert len(calls) == 1, 'calls: {}'.format(calls)
			remaining_ticks = max(list(calls.values())[0], 1) # we have to save a number > 0
			db("UPDATE collector SET remaining_ticks = ? WHERE rowid = ?",
				 remaining_ticks, self.worldid)

	def load(self, db, worldid):
		super().load(db, worldid)
		# get own properties
		health, can_reproduce = db.get_wildanimal_row(worldid)
		# get home island
		island = WorldObject.get_object_by_id(db.get_unit_owner(worldid))
		self.__init(island, bool(can_reproduce), health)

	def get_collectable_res(self):
		return [self._required_resource_id]

	def apply_state(self, state, remaining_ticks=None):
		super().apply_state(state, remaining_ticks)
		if self.state == self.states.no_job_waiting:
			Scheduler().add_new_object(self.handle_no_possible_job, self, remaining_ticks)

	def handle_no_possible_job(self):
		"""Just walk to a random location nearby and search there for food, when we arrive"""
		self.log.debug('%s: no possible job; health: %s', self, self.health)
		# decrease health because of lack of food
		self.health -= WILD_ANIMAL.HEALTH_DECREASE_ON_NO_JOB
		if self.health <= 0:
			self.die()
			return

		# if can't find a job, we walk to a random location near us and search there
		(target, path) = self.get_random_location(self.walking_range)
		if target is not None:
			self.log.debug('%s: no possible job, walking to %s', self, str(target))
			self.move(target, callback=self.search_job, path=path)
			self.state = self.states.no_job_walking_randomly
		else:
			# we couldn't find a target, just try again 3 secs later
			self.log.debug('%s: no possible job, no possible new loc', self)
			Scheduler().add_new_object(self.handle_no_possible_job, self, 48)
			self.state = self.states.no_job_waiting

	def get_job(self):
		pos = self.position.to_tuple()

		# try to get away with a random job (with normal forest density this works > 99% of the time)
		for i in range(min(5, self._building_index.get_num_buildings_in_range(pos))):
			provider = self._building_index.get_random_building_in_range(pos)
			if provider is not None and self.check_possible_job_target(provider):
				# animals only collect one resource
				entry = self.check_possible_job_target_for(provider, self._required_resource_id)
				if entry:
					path = self.check_move(provider.loading_area)
					if path:
						job = Job(provider, [entry])
						job.path = path
						return job

		# NOTE: use random job, works fine and is faster than looking for the best
		return None

	def check_possible_job_target(self, provider):
		if provider.position.contains(self.position):
			# force animal to choose a tree where it currently not stands
			return False
		return super().check_possible_job_target(provider)

	def end_job(self):
		super().end_job()
		# check if we can reproduce
		self.log.debug("%s end_job; health: %s", self, self.health)
		self.health += WILD_ANIMAL.HEALTH_INCREASE_ON_FEEDING
		if self.can_reproduce and self.health >= WILD_ANIMAL.HEALTH_LEVEL_TO_REPRODUCE and \
			len(self.home_island.wild_animals) < (self.home_island.num_trees // WILD_ANIMAL.POPULATION_LIMIT):
			self.reproduce()
			# reproduction costs health
			self.health = WILD_ANIMAL.HEALTH_INIT_VALUE

	def reproduce(self):
		"""Create another animal of our type on the place where we stand"""
		if not self.can_reproduce:
			return

		self.log.debug("%s REPRODUCING", self)
		# create offspring
		CreateUnit(self.owner.worldid, self.id, self.position.x, self.position.y,
		           can_reproduce=self.next_clone_can_reproduce())(issuer=None)
		# reset own resources
		for res in self.get_consumed_resources():
			self.get_component(StorageComponent).inventory.reset(res)

	def next_clone_can_reproduce(self):
		"""Returns, whether the next child will be able to reproduce himself.
		Some animal can't reproduce, which makes population growth easier to control.
		@return: bool"""
		return (self.session.random.randint(0, 2) > 0) # 2/3 chance for True

	def die(self):
		"""Makes animal die, e.g. because of starvation or getting killed by herder"""
		self.log.debug("%s dying", self)
		self.home_island.wild_animals.remove(self)
		self.remove()

	def cancel(self, continue_action=None):
		if continue_action is None:
			continue_action = self.search_job
		super().cancel(continue_action=continue_action)

	def __str__(self):
		return "{}(health={})".format(super().__str__(),
		                              getattr(self, 'health', None))
