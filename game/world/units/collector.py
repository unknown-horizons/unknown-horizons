# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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

from game.world.units.unit import Unit
from game.world.storageholder import StorageHolder
from game.util import Rect, Point
from game.world.pathfinding import Movement
from game.world.production import PrimaryProducer
from game.ext.enum import Enum
import game.main
import operator
import weakref
import new


class BuildingCollector(StorageHolder, Unit):
	movement = Movement.COLLECTOR_MOVEMENT
	"""
	Gets resources for e.g. a weaver, that needs wool

	Timeline:
	init
	|-search_job()
	  |- get_job   - he found a job ( it's best )
	  |-

	"""
	states = Enum('idle', 'moving_to_target', 'working', 'moving_home')

	# NOTE: see bottom class for further class variables

	def __init__(self, home_building, slots = 1, size = 6, start_hidden=True, **kwargs):
		super(BuildingCollector, self).__init__(x=home_building.position.origin.x,
												y=home_building.position.origin.y,
												slots = slots,
												size = size,
												**kwargs)
		if game.main.debug:
			print "Initing BuildingCollector", self.id
		self.home_building = weakref.ref(home_building)
		self.inventory.limit = size;

		self.start_hidden = start_hidden
		if self.start_hidden:
			self.hide()

		self.state = self.states.idle

		# start searching jobs just when construction (of subclass) is completed
		game.main.session.scheduler.add_new_object(self.search_job, self, 1)

	def save(self, db):
		super(BuildingCollector, self).save(db)
		# set owner to home_building (is set to player by unit)
		db("UPDATE unit SET owner = ? WHERE rowid = ?", self.home_building().getId(), self.getId())

		# save state and remaining ticks for next callback
		current_callback = new.instancemethod(self.callbacks_for_state[self.state], self)
		calls = game.main.session.scheduler.get_classinst_calls(self, current_callback)
		assert(len(calls) == 1)
		remaining_ticks = calls.values()[0]
		db("INSERT INTO collector(rowid, state, remaining_ticks) VALUES(?, ?, ?)", \
			 self.getId(), self.state.index, remaining_ticks)

		# save the job
		if self.job is not None and self.job.object is not None:
			db("INSERT INTO collector_job(rowid, object, resource, amount) VALUES(?, ?, ?, ?)", \
				 self.getId(), self.job.object.getId(), self.job.res, self.job.amount)



		# checklist:
		# register collector at target/source
		# show/hide
		# save exact number of ticks,
		# states: moving to target, working, moving back

	def load(self, db, worldid):
		super(BuildingCollector, self).load(db, worldid)

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		if game.main.debug:
			print "Collector seach_job", self.id
		self.job = self.get_job()
		if self.job is None:
			game.main.session.scheduler.add_new_object(self.search_job, self, 32)
		else:
			self.begin_current_job()

	def get_job(self):
		"""Returns the next job or None"""
		if game.main.debug:
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
				if isinstance(building, PrimaryProducer) and \
				   building.active_production_line is not None and \
				   building.production[building.active_production_line].production.get(res,1) < 0:
					break
				res_amount = building.inventory[res]
				if res_amount > 0:
					# get sum of picked up resources by other collectors for res
					total_pickup_amount = sum([ collector.job.amount for collector in \
												building._Provider__collectors if \
												collector.job.res == res ])
					# check how much will be delivered
					total_registered_amount_consumer = sum([ collector.job.amount for \
															 collector in \
															 self.home_building()._Consumer__collectors if \
															 collector.job.res == res ])
					# check if there are resources left to pickup
					max_consumer_res_free = self.home_building().inventory.get_limit(res)-\
										  (total_registered_amount_consumer+\
										   self.home_building().inventory[res])
					if res_amount > total_pickup_amount and max_consumer_res_free > 0:
						# add a new job
						jobs.append(Job(building, res, min(res_amount - \
														   total_pickup_amount,\
														   self.inventory.get_limit(res), \
														   max_consumer_res_free)))

		# sort job list
		jobs = self.sort_jobs(jobs)

		for job in jobs:
			if self.check_move(job.object.position):
				return job
		return None

	def setup_new_job(self):
		"""Executes the necessary actions to begin a new job"""
		if game.main.debug:
			print "Collector setup_new_job", self.id
		self.job.object._Provider__collectors.append(self)
		self.home_building()._Consumer__collectors.append(self)

	def sort_jobs(self, jobs):
		"""Sorts the jobs for further processing. This has been moved to a seperate function so it
		can be overwritten by subclasses. A building collector might sort after a specific rating,
		a lumberjack might just take a random tree.
		@param jobs: list of Job instances that should be sorted an then returned.
		@return: sorted list of Job instances."""
		if game.main.debug:
			print "Collector sort_jobs", self.id
		jobs.sort(key=operator.attrgetter('rating') )
		jobs.reverse()
		return jobs

	def begin_current_job(self):
		"""Executes the current job"""
		if game.main.debug:
			print "Collector begin_current_job", self.id
		self.setup_new_job()
		self.show()
		self.move(self.job.object.position, self.begin_working)
		self.state = self.states.moving_to_target

	def begin_working(self):
		"""Pretends that the collector works by waiting some time"""
		# uncomment the following line when all collectors have a "stopped" animation
		#self._instance.act("stopped", self._instance.getFacingLocation(), True)
		if game.main.debug:
			print "Collector begin_working", self.id
		if self.job.object is not None:
			game.main.session.scheduler.add_new_object(self.finish_working, self, 16)
			self.state = self.states.working
		else:
			self.reroute()

	def finish_working(self):
		"""Called when collector is stayed at the target for a while.
		Picks up the resources and sends collector home."""
		if game.main.debug:
			print "Collector finish_working", self.id
		if self.job.object is not None:
			self.act("idle", self._instance.getFacingLocation(), True)
			# transfer res
			self.transfer_res()
			# deregister at the target we're at
			self.job.object._Provider__collectors.remove(self)
			# move back to home
			self.move_home(callback=self.reached_home)
		else:
			self.reroute()

	def reroute(self):
		if game.main.debug:
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
		"""We finished now our complete work. You can use this as event as after work.
		"""
		if game.main.debug:
			print "Collector reached_home", self.id

		if self.home_building() is not None:
			remnant = self.home_building().inventory.alter(self.job.res, self.job.amount)
			#assert(remnant == 0, "Home building could not take all ressources from collector.")
			remnant = self.inventory.alter(self.job.res, -self.job.amount)
			#assert(remnant == 0, "collector did not pick up amount of ressources specified by the job.")
			self.home_building()._Consumer__collectors.remove(self)
		self.end_job()

	def end_job(self):
		"""Contrary to setup_new_job"""
		# he finished the job now
		# before the new job can begin this will be executed
		if game.main.debug:
			print "Collector end_job", self.id
		if self.start_hidden:
			self.hide()
		game.main.session.scheduler.add_new_object(self.search_job , self, 32)
		self.state = self.states.idle

	def transfer_res(self):
		"""Transfers resources from target to collector inventory"""
		if game.main.debug:
			print "Collector transfer_res", self.id
		res_amount = self.job.object.pickup_resources(self.job.res, self.job.amount)
		# should not to be. register_collector function at the building should prevent it
		assert(res_amount == self.job.amount, "collector could not pickup amount of ressources, that was planned for the current job.")
		self.inventory.alter(self.job.res, res_amount)

	def get_collectable_res(self):
		"""Return all resources the Collector can collect (depends on its home building)"""
		if game.main.debug:
			print "Collector get_collectable_res", self.id
		# find needed res (only res that we have free room for) - Building function
		return self.home_building().get_needed_res()

	def get_buildings_in_range(self):
		"""returns all buildings in range
		Overwrite in subclasses that need ranges arroung the pickup."""
		if game.main.debug:
			print "Collector get_buildings_in_range", self.id
		from game.world.provider import Provider
		return [building for building in self.home_building().get_buildings_in_range() if isinstance(building, Provider)]

	def move_home(self, callback=None, action='move_full'):
		if game.main.debug:
			print "Collector move_home", self.id
		self.move(self.home_building().position, callback=callback, destination_in_building=True, action=action)
		self.state = self.states.moving_home

	def cancel(self):
		if game.main.debug:
			print "Collector cancel", self.id
		if job.object is not None:
			self.job.object._Provider__collectors.remove(self)
		game.main.session.scheduler.rem_all_classinst_calls(self)
		self.move_home(callback=self.search_job, action='move')

	callbacks_for_state = { \
		states.idle: search_job, \
		states.moving_to_target: begin_working, \
		states.working: finish_working, \
		states.moving_home: reached_home \
		}


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
		"""Sorts the jobs for further processing. This has been moved to a seperate function so it
		can be overwritten by subclasses. A building collector might sort after a specific rating,
		a lumberjack might just take a random tree.
		@param jobs: list of Job instances that should be sorted an then returned.
		@return: sorted list of Job instances.
		"""
		if game.main.debug:
			print "FieldCollector sort_jobs", self.id
		from random import shuffle
		shuffle(jobs)
		return jobs


class AnimalCollector(BuildingCollector):
	""" Collector that gets resources from animals """

	def begin_current_job(self):
		"""Tell the animal to stop. First step of a job"""
		#print self.id, 'BEGIN CURRENT JOB'
		self.setup_new_job()
		self.stop_animal()

	def pickup_animal(self):
		"""Moves collector to animal. Called by animal when it actually stopped"""
		#print self.id, 'PICKUP ANIMAL'
		self.show()
		self.move(self.job.object.position, self.begin_working)

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
		#print self.id, 'GET ANIMALS IN RANGE'
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
		"""Let animal free after shearing"""
		#print self.id, 'RELEASE ANIMAL', self.job.object.getId()
		game.main.session.scheduler.add_new_object(self.job.object.search_job, self.job.object, 16)


class Job(object):
	def __init__(self, object, res, amount):
		self._object = weakref.ref(object)
		self.res = res
		self.amount = amount

		# this is rather a dummy
		self.rating = amount

	@property
	def object(self):
		return self._object()
