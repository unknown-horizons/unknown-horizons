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

from horizons.constants import GAME_SPEED
from horizons.scheduler import Scheduler
from horizons.world.units.collectors.buildingcollector import BuildingCollector
from horizons.world.units.unitexeptions import MoveNotPossible


class AnimalCollector(BuildingCollector):
	""" Collector that gets resources from animals.
	Behavior (timeline):
	 - search for an animal which has resources to pick up
	 - tell animal to stop when its current job is done
	 - wait for callback from this animal, notifying that we can pick it up
	 - walk to animal
	 - walk home (with animal walking along)
	 - stay at home building for a while
	 - release animal
	 """
	kill_animal = False # whether we kill the animals

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def load(self, db, worldid):
		super().load(db, worldid)

	def apply_state(self, state, remaining_ticks=None):
		super().apply_state(state, remaining_ticks)
		if state == self.states.waiting_for_animal_to_stop:
			# register at target
			self.setup_new_job()
			self.stop_animal()
		elif state == self.states.moving_home:
			if not self.__class__.kill_animal:
				self.setup_new_job() # register at target if it's still alive

	def cancel(self, continue_action=None):
		if self.job is not None:
			if self.state == self.states.waiting_for_animal_to_stop:
				if hasattr(self.job.object, 'remove_stop_after_job'):
					# when loading a game fails and the world is destructed again, the
					# worldid may not yet have been resolved to an actual in-game object
					self.job.object.remove_stop_after_job()
		super().cancel(continue_action=continue_action)

	def begin_current_job(self):
		"""Tell the animal to stop."""
		self.setup_new_job()
		self.stop_animal()
		self.state = self.states.waiting_for_animal_to_stop

	def pickup_animal(self):
		"""Moves collector to animal. Called by animal when it actually stopped"""
		self.show()
		try:
			self.move(self.job.object.loading_area, self.begin_working)
		except MoveNotPossible:
			# the animal is now unreachable.
			self.job.object.search_job()
			self.state = self.states.idle
			self.cancel(continue_action=self.search_job)
			return
		self.state = self.states.moving_to_target

	def finish_working(self):
		"""Called when collector arrives at the animal. Move home with the animal"""
		if self.__class__.kill_animal:
			# get res now, and kill animal right after
			super().finish_working()
		else:
			self.move_home(callback=self.reached_home)
		self.get_animal() # get or kill animal

	def reached_home(self):
		"""Transfer res to home building and such. Called when collector arrives at it's home"""
		if not self.__class__.kill_animal:
			# sheep and herder are inside the building now, pretending to work.
			super().finish_working(collector_already_home=True)
			self.release_animal()
		super().reached_home()

	def get_buildings_in_range(self, reslist=None):
		return self.get_animals_in_range(reslist)

	def get_animals_in_range(self, reslist=None):
		return self.home_building.animals

	def check_possible_job_target_for(self, target, res):
		# An animal can only be collected by one collector.
		# Since a collector only retrieves one type of res, and
		# an animal might produce more than one, two collectors
		# could take this animal as a target.
		# This could also happen, if the animal has an inventory
		# with a limit > 1. In this case, one collector might register
		# for the first ton, then the animal produces another one, which
		# might then be spotted by another collector.
		# TODO:
		# The animal class must be producer class that is only
		# collectable by 1 collector at a time, which also should be checked.
		# This could be a new abstract class.
		if target.has_collectors():
			return None
		else:
			return super().check_possible_job_target_for(target, res)

	def stop_animal(self):
		"""Tell animal to stop at the next occasion"""
		self.job.object.stop_after_job(self)

	def get_animal(self):
		"""Sends animal to collectors home building"""
		self.log.debug("%s getting animal %s", self, self.job.object)
		if self.__class__.kill_animal:
			self.job.object.die()
			self.job.object = None # there is no target anymore now
		else:
			self.job.object.move(self.home_building.position, destination_in_building=True,
			                     action='move_full')

	def release_animal(self):
		"""Let animal free after shearing and schedules search for a new job for animal."""
		if not self.__class__.kill_animal:
			self.log.debug("%s releasing animal %s", self, self.job.object)
			Scheduler().add_new_object(self.job.object.search_job, self.job.object,
			                           GAME_SPEED.TICKS_PER_SECOND)


class HunterCollector(AnimalCollector):
	kill_animal = True

	def get_animals_in_range(self, res=None):
		dist = self.home_building.position.distance
		radius = self.home_building.radius
		return [animal for animal in self.home_building.island.wild_animals if
		        dist(animal.position) <= radius]
