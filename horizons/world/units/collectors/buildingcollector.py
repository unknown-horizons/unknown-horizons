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

import operator
import weakref
import new

import horizons.main

from horizons.world.storageholder import StorageHolder
from horizons.util import Rect, Point, WorldObject
from horizons.world.pathfinding import Movement
from horizons.world.production import PrimaryProducer
from horizons.ext.enum import Enum

from collector import Collector, Job


class BuildingCollector(Collector):
	"""Collector, that works for a building and gets its needed resources.
	Essentially extends the Collector by a home building.
	"""
	def __init__(self, home_building, **kwargs):
		super(BuildingCollector, self).__init__(x=home_building.position.origin.x,
												y=home_building.position.origin.y,
												**kwargs)
		if horizons.main.debug:
			print "Initing BuildingCollector", self.id

		self.__init(home_building)

	def __init(self, home_building):
		self.home_building = weakref.ref(home_building)
		self.register_at_home_building()

	def save(self, db):
		super(BuildingCollector, self).save(db)
		# set owner to home_building (is set to player by unit)
		db("UPDATE unit SET owner = ? WHERE rowid = ?", self.home_building().getId(), self.getId())

	def load(self, db, worldid):
		super(BuildingCollector, self).load(db, worldid)

		# load home_building
		home_building_id = db("SELECT owner FROM unit WHERE rowid = ?", worldid)[0][0]
		self.__init(WorldObject.get_object_by_id(home_building_id))

	def register_at_home_building(self):
		self.home_building().local_collectors.append(self)

	def apply_state(self, state, remaining_ticks = None):
		super(BuildingCollector, self).apply_state(state, remaining_ticks)
		if state == self.states.moving_home:
			# collector is on his way home
			self.home_building()._AbstractConsumer__collectors.append(self)
			self.add_move_callback(self.reached_home)
			self.show()

	def get_home_inventory(self):
		return self.home_building().inventory

	def get_colleague_collectors(self):
		return self.home_building()._AbstractConsumer__collectors

	def get_job(self):
		"""Returns the next job or None"""
		if horizons.main.debug:
			print "Collector get_job", self.id

		if self.home_building() is None:
			return None

		collectable_res = self.get_collectable_res()
		if len(collectable_res) == 0:
			return None
		jobs = []
		for building in self.get_buildings_in_range():
			# Continue if building is of the same class as the home building or
			# they have the same inventory, to prevent e.g. weaver picking up from weaver.
			if isinstance(building, self.home_building().__class__) or \
			   building.inventory is self.home_building().inventory:
				continue
			for res in collectable_res:
				""" it is unknown what this code does, so i commented it out:
				if isinstance(building, PrimaryProducer) and \
					 building.active_production_line is not None and \
					 building.production[building.active_production_line].production.get(res,1) < 0:
					break
				"""
				job = self.check_possible_job_target(building, res)
				if job is not None:
						jobs.append(job)

		# sort job list
		jobs = self.sort_jobs(jobs)

		# check if we can move to that targets
		for job in jobs:
			if self.check_move(job.object.position):
				return job
		return None

	def setup_new_job(self):
		super(BuildingCollector, self).setup_new_job()
		self.home_building()._AbstractConsumer__collectors.append(self)

	def finish_working(self):
		"""Called when collector has stayed at the target for a while.
		Picks up the resources and sends collector home."""
		super(BuildingCollector, self).finish_working()
		if self.job.object is not None:
			self.move_home(callback=self.reached_home)

	def reroute(self):
		"""Reroutes the collector to a different job, or home if no job is found.
		Can be called the current job can't be executed any more"""
		if horizons.main.debug:
			print "Collector reroute", self.id
		#print self.getId(), 'Rerouting from', self.position
		# Get a new job
		job = self.get_job()
		# Check if there is a new job
		if job is not None:
			# There is a new job!
			self.job = job
			self.begin_current_job()
		else:
			# There is no new job...
			# Return home and end job
			self.move_home(callback=self.reached_home)

	def reached_home(self):
		"""Exchanges resources with home and 'ends' the job"""
		if horizons.main.debug:
			print "Collector reached_home", self.id

		if self.home_building() is not None:
			remnant = self.home_building().inventory.alter(self.job.res, self.job.amount)
			#assert(remnant == 0, "Home building could not take all ressources from collector.")
			remnant = self.inventory.alter(self.job.res, -self.job.amount)
			#assert(remnant == 0, "collector did not pick up amount of ressources specified by the job.")
			self.home_building()._AbstractConsumer__collectors.remove(self)
		self.end_job()

	def get_collectable_res(self):
		"""Return all resources the Collector can collect (depends on its home building)"""
		if horizons.main.debug:
			print "Collector get_collectable_res", self.id
		# find needed res (only res that we have free room for) - Building function
		return self.home_building().get_needed_res()

	def get_buildings_in_range(self):
		"""Returns all buildings in range
		Overwrite in subclasses that need ranges arroung the pickup."""
		if horizons.main.debug:
			print "Collector get_buildings_in_range", self.id
		from horizons.world.provider import Provider
		return [building for building in self.home_building().get_buildings_in_range() if isinstance(building, Provider)]

	def move_home(self, callback=None, action='move_full'):
		"""Moves collector back to its home building"""
		if horizons.main.debug:
			print "Collector move_home", self.id
		self.move(self.home_building().position, callback=callback, destination_in_building=True, action=action)
		self.state = self.states.moving_home

	def cancel(self):
		"""Cancels current job and moves back home"""
		if horizons.main.debug:
			print "Collector cancel", self.id
		if self.job.object is not None:
			self.job.object._Provider__collectors.remove(self)
		horizons.main.session.scheduler.rem_all_classinst_calls(self)
		self.move_home(callback=self.search_job, action='move')


class StorageCollector(BuildingCollector):
	""" Same as BuildingCollector, except that it moves on roads.
	Used in storage facilities.
	"""
	movement = Movement.STORAGE_COLLECTOR_MOVEMENT

	def begin_current_job(self):
		"""Declare target of StorageCollector as building, because it always is"""
		super(StorageCollector, self).begin_current_job()
		self.move(self.job.object.position, self.begin_working, destination_in_building = True)

class FieldCollector(BuildingCollector):
	""" Simular to the BuildingCollector but used on farms for example.
	The main difference is that it uses a different way to sort it's jobs, to make for a nicer
	look of farm using."""

	def sort_jobs(self, jobs):
		return self.sort_jobs_random(jobs)
