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

import weakref

from horizons.util import WorldObject, Circle
from horizons.world.pathfinding.pather import RoadPather, BuildingCollectorPather

from collector import Collector, JobList


class BuildingCollector(Collector):
	"""Collector, that works for a building and gets its needed resources.
	Essentially extends the Collector by a home building.
	"""
	job_ordering = JobList.order_by.amount
	pather_class = BuildingCollectorPather

	def __init__(self, home_building, **kwargs):
		super(BuildingCollector, self).__init__(x=home_building.position.origin.x,
												y=home_building.position.origin.y,
												**kwargs)
		self.__init(home_building)

	def __init(self, home_building):
		self._home_building = weakref.ref(home_building)
		self.register_at_home_building()

	@property
	def home_building(self):
		return self._home_building()

	def save(self, db):
		super(BuildingCollector, self).save(db)
		# set owner to home_building (is set to player by unit)
		db("UPDATE unit SET owner = ? WHERE rowid = ?", self.home_building.getId(), self.getId())

	def load(self, db, worldid):
		# we have to call __init here before super().load, because a superclass uses a method,
		# which is overwritten here, that uses a member, which has to be initialised via __init.

		# load home_building
		home_building_id = db("SELECT owner FROM unit WHERE rowid = ?", worldid)[0][0]
		self.__init(WorldObject.get_object_by_id(home_building_id))

		super(BuildingCollector, self).load(db, worldid)

	def register_at_home_building(self, unregister = False):
		"""Creates reference for self at home building (only hard reference except for
		in job.object)
		@param unregister: wether to reverse registration
		"""
		if unregister:
			self.home_building.remove_local_collector(self)
		else:
			self.home_building.add_local_collector(self)

	def apply_state(self, state, remaining_ticks = None):
		super(BuildingCollector, self).apply_state(state, remaining_ticks)
		if state == self.states.moving_home:
			# collector is on his way home
			self.add_move_callback(self.reached_home)
			self.show()

	def remove(self):
		self.register_at_home_building(unregister=True)
		super(BuildingCollector, self).remove()

	def get_home_inventory(self):
		return self.home_building.inventory

	def get_colleague_collectors(self):
		return self.home_building.get_local_collectors()

	def get_job(self):
		"""Returns the next job or None"""
		self.log.debug("Collector %s get_job", self.getId())
		if self.home_building is None:
			return None

		collectable_res = self.get_collectable_res()
		if len(collectable_res) == 0:
			return None

		jobs = JobList(self.job_ordering)
		for building in self.get_buildings_in_range():
			if self.check_possible_job_target(building): # check if we can pickup here in principle
				for res in collectable_res:
					job = self.check_possible_job_target_for(building, res) # check if we also get res here
					if job is not None:
						jobs.append(job)

		return self.get_best_possible_job(jobs)

	def finish_working(self):
		"""Called when collector has stayed at the target for a while.
		Picks up the resources and sends collector home."""
		if self.job.object is not None:
			self.move_home(callback=self.reached_home)
		super(BuildingCollector, self).finish_working()

	def reroute(self):
		"""Reroutes the collector to a different job, or home if no job is found.
		Can be called the current job can't be executed any more"""
		self.log.debug("Collector %s reroute", self.getId())
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
		"""Exchanges resources with home and calss end_job"""
		self.log.debug("Collector %s reached home", self.getId())

		if self.home_building is not None:
			self.log.debug("Collector %s brought home %s of %s", self.getId(), self.job.amount, self.job.res)
			remnant = self.home_building.inventory.alter(self.job.res, self.job.amount)
			#assert remnant == 0, "Home building could not take all ressources from collector."
			remnant = self.inventory.alter(self.job.res, -self.job.amount)
			assert remnant == 0
		self.end_job()

	def get_collectable_res(self):
		"""Return all resources the Collector can collect (depends on its home building)"""
		# find needed res (only res that we have free room for) - Building function
		return self.home_building.get_needed_resources()

	def get_buildings_in_range(self):
		"""Returns all buildings in range
		Overwrite in subclasses that need ranges arroung the pickup."""
		reach = Circle(self.home_building.position.center(), self.home_building.radius)
		return self.home_building.island().get_providers_in_range(reach)

	def move_home(self, callback=None, action='move_full'):
		"""Moves collector back to its home building"""
		self.log.debug("Collector %s move_home", self.getId())
		self.move(self.home_building.position, callback=callback, destination_in_building=True, action=action)
		self.state = self.states.moving_home

	def cancel(self):
		"""Cancels current job and moves back home"""
		self.log.debug("Collector %s cancel", self.getId())
		if self.job.object is not None:
			self.job.object.remove_incoming_collector(self)
		self.job = None
		self.move_home(callback=self.search_job, action='move')


class StorageCollector(BuildingCollector):
	""" Same as BuildingCollector, except that it moves on roads.
	Used in storage facilities.
	"""
	pather_class = RoadPather
	destination_always_in_building = True


class FieldCollector(BuildingCollector):
	""" Simular to the BuildingCollector but used on farms for example.
	The main difference is that it uses a different way to sort it's jobs, to make for a nicer
	look of farm using."""
	job_ordering = JobList.order_by.random


class SettlerCollector(StorageCollector):
	"""Collector for settlers."""
	pass

