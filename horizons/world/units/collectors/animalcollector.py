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

from horizons.world.storageholder import StorageHolder
from horizons.util import Point

from buildingcollector import BuildingCollector


class AnimalCollector(BuildingCollector):
	""" Collector that gets resources from animals """

	def __init__(self, *args, **kwargs):
		super(AnimalCollector, self).__init__(*args, **kwargs)

	def load(self, db, worldid):
		super(AnimalCollector, self).load(db, worldid)
		if self.state == self.states.waiting_for_animal_to_stop:
			if self.job is not None:
				# register at target
				self.job.object.stop_after_job(self)

	def cancel(self):
		assert False

	def apply_state(self, state, remaining_ticks=None):
		super(AnimalCollector, self).apply_state(state, remaining_ticks)
		if self.state == self.states.waiting_for_animal_to_stop:
			self.setup_new_job()

	def begin_current_job(self):
		"""Tell the animal to stop."""
		#print self.id, 'BEGIN CURRENT JOB'
		self.setup_new_job()
		self.stop_animal()
		self.state = self.states.waiting_for_animal_to_stop

	def pickup_animal(self):
		"""Moves collector to animal. Called by animal when it actually stopped"""
		#print self.id, 'PICKUP ANIMAL'
		self.show()
		self.move(self.job.object.position, self.begin_working)
		self.state = self.states.moving_to_target

	def finish_working(self):
		"""Transfer res and such. Called when collector arrives at the animal"""
		super(AnimalCollector, self).finish_working()
		self.get_animal()

	def reached_home(self):
		"""Transfer res to home building and such. Called when collector arrives at it's home"""
		super(AnimalCollector, self).reached_home()
		# sheep and herder are inside the building now, pretending to work.
		self.release_animal()

	def get_buildings_in_range(self):
		# This is only a small workarround
		# as long we have no Collector class
		return self.get_animals_in_range()

	def get_animals_in_range(self):
		# TODO: use the Collector class instead of BuildCollector
		"""returns all buildings in range
		Overwrite in subclasses that need ranges arroung the pickup."""
		return self.home_building().animals

	def stop_animal(self):
		"""Tell animal to stop at the next occasion"""
		#print self.id, 'STOP ANIMAL', self.job.object.id
		self.job.object.stop_after_job(self)

	def get_animal(self):
		"""Sends animal to collectors home building"""
		#print self.id, 'GET ANIMAL'
		self.job.object.move(self.home_building().position, destination_in_building = True, action='move_full')

	def release_animal(self):
		"""Let animal free after shearing and schedules search for a new job for animal."""
		#print self.id, 'RELEASE ANIMAL', self.job.object.getId()
		horizons.main.session.scheduler.add_new_object(self.job.object.search_job, self.job.object, 16)
