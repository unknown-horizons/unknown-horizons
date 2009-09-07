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

import horizons.main
from horizons.scheduler import Scheduler

from horizons.world.storageholder import StorageHolder
from horizons.util import Point, Circle

from buildingcollector import BuildingCollector


class AnimalCollector(BuildingCollector):
	""" Collector that gets resources from animals.
	Behaviour (timeline):
	 - search for an animal which has resources to pick up
	 - tell animal to stop when its current job is done
	 - wait for callback from this animal, notifying that we can pick it up
	 - walk to animal
	 - walk home (with animal walking along)
	 - stay at home building for a while
	 - release animal
	 """
	def __init__(self, *args, **kwargs):
		super(AnimalCollector, self).__init__(*args, **kwargs)

	def load(self, db, worldid):
		super(AnimalCollector, self).load(db, worldid)
		if self.state == self.states.waiting_for_animal_to_stop:
			if self.job is not None:
				# register at target
				self.job.object.stop_after_job(self)

	def cancel(self):
		if self.job is not None:
			if self.state == self.states.waiting_for_animal_to_stop:
				self.job.object.remove_stop_after_job()
		super(AnimalCollector, self).cancel()

	def apply_state(self, state, remaining_ticks=None):
		super(AnimalCollector, self).apply_state(state, remaining_ticks)
		if self.state == self.states.waiting_for_animal_to_stop:
			self.setup_new_job()

	def begin_current_job(self):
		"""Tell the animal to stop."""
		self.setup_new_job()
		self.stop_animal()
		self.state = self.states.waiting_for_animal_to_stop

	def pickup_animal(self):
		"""Moves collector to animal. Called by animal when it actually stopped"""
		self.show()
		move_possible = self.move(self.job.object.position, self.begin_working)
		if not move_possible:
			# the animal is now unreachable.
			self.job.object.remove_stop_after_job()
			self.job.object.search_job()
			self.cancel()
		self.state = self.states.moving_to_target

	def finish_working(self):
		"""Transfer res and such. Called when collector arrives at the animal"""
		self.get_animal()
		super(AnimalCollector, self).finish_working()

	def reached_home(self):
		"""Transfer res to home building and such. Called when collector arrives at it's home"""
		# sheep and herder are inside the building now, pretending to work.
		self.release_animal()
		super(AnimalCollector, self).reached_home()

	def get_buildings_in_range(self):
		return self.get_animals_in_range()

	def get_animals_in_range(self):
		"""returns all buildings in range
		Overwrite in subclasses that need ranges around the pickup."""
		return self.home_building.animals

	def stop_animal(self):
		"""Tell animal to stop at the next occasion"""
		self.job.object.stop_after_job(self)

	def get_animal(self):
		"""Sends animal to collectors home building"""
		#print self.id, 'GET ANIMAL'
		move_possible = self.job.object.move(self.home_building.position, \
		                                     destination_in_building = True, action='move_full')
		assert move_possible, "Animal can't join animal collector cause he can't find a path"

	def release_animal(self):
		"""Let animal free after shearing and schedules search for a new job for animal."""
		Scheduler().add_new_object(self.job.object.search_job, self.job.object, 16)


class FarmAnimalCollector(AnimalCollector):
	def get_animals_in_range(self):
		buildings = self.home_building.island.get_providers_in_range(Circle(self.home_building.position.center(), self.home_building.radius))
		animals = []
		for building in buildings:
			try:
				animals.extend(building.animals)
			except AttributeError:
				pass # this building has no animals
		return animals


class HunterCollector(AnimalCollector):
	def get_animals_in_range(self):
		return self.home_building.island.wild_animals

	def finish_working(self):
		super(HunterCollector, self).finish_working()
		# kill animal when we got our res
		self.job.object.die()

	def release_animal(self):
		# we don't release it, we already killed it.
		pass

	def get_animal(self):
		pass
