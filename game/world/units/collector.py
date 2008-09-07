# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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
import game.main
import operator
import weakref


class BuildingCollector(StorageHolder, Unit):
	movement = Movement.CARRIAGE_MOVEMENT
	"""
	How does this class work ?
	Timeline:
	init
	|-search_job()
	  |- get_job   - he found a job ( it's best )
	  |-

	"""
	def __init__(self, home_building, slots = 1, size = 6, start_hidden=True, **kwargs):
		super(BuildingCollector, self).__init__(x=home_building.position.origin.x,
												y=home_building.position.origin.y,
												slots = slots,
												size = size,
												**kwargs)
		print 'carriage beeing inited'
		self.home_building = weakref.ref(home_building)

		for res in home_building.get_consumed_res(): # NOTE: this does not work for multiple production lines yet.
			if not self.inventory.hasSlot(res):
				self.inventory.addSlot(res, size)

		self.start_hidden = start_hidden
		if self.start_hidden:
			self.hide()

		# start searching jobs just when construction (of subclass) is completed
		game.main.session.scheduler.add_new_object(self.search_job, self, 1)

	def save(self, db):
		super(BuildingCollector, self).save(db)
		db("UPDATE unit SET owner = ? WHERE rowid = ?", self.home_building().getId(), self.getId())
		print 'savin job', (self.job is not None)
		if self.job is not None:
			db("INSERT INTO collector_job(rowid, object, resource, amount) VALUES(?, ?, ?, ?)", self.getId(), self.job.object.getId(), self.job.res, self.job.amount)

		# TODO:
		# state of current job

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		self.job = self.get_job()
		if self.job is None:
			print self.id, 'JOB NONE'
			game.main.session.scheduler.add_new_object(self.search_job, self, 32)
		else:
			print self.id, 'EXECUTE JOB'
			self.begin_current_job()

	def get_job(self):
		"""Returns the next job or None"""

		if self.home_building() is None:
			return None

		print self.id, 'GET JOB'
		collectable_res = self.get_collectable_res()
		if len(collectable_res) == 0:
			return None
		jobs = []
		for building in self.get_buildings_in_range():
			if building.inventory is self.home_building().inventory:
				continue
			for res in collectable_res:
				res_amount = building.inventory.get_value(res)
				if res_amount > 0:
					# get sum of picked up resources for res
					total_pickup_amount = sum([ carriage.job.amount for carriage in building._Provider__collectors if carriage.job.res == res ])
					# check how much will be delivered
					total_registered_amount_consumer = sum([ carriage.job.amount for carriage in self.home_building()._Consumer__collectors if carriage.job.res == res ])
					# check if there are resources left to pickup
					max_consumer_res_free = self.home_building().inventory.get_size(res)-(total_registered_amount_consumer+self.home_building().inventory.get_value(res))
					if res_amount > total_pickup_amount and max_consumer_res_free > 0:
						# add a new job
						jobs.append(Job(building, res, min(res_amount - total_pickup_amount, self.inventory.get_size(res), max_consumer_res_free)))

		# sort job list
		jobs.sort(key=operator.attrgetter('rating') )
		jobs.reverse()

		for job in jobs:
			if self.check_move(job.object.position) is not None:
				return job
		return None

	def setup_new_job(self):
		"""Executes the necessary actions to begin a new job"""
		self.job.object._Provider__collectors.append(self)
		self.home_building()._Consumer__collectors.append(self)

	def begin_current_job(self):
		"""Executes the current job"""
		print self.id, 'BEGIN CURRENT JOB'
		self.setup_new_job()
		self.show()
		self.move(self.job.object.position, self.begin_working)

	def begin_working(self):
		"""Pretends that the collector works by waiting some time"""
		# uncomment the following line when all collectors have a "stopped" animation
		#self._instance.act("stopped", self._instance.getFacingLocation(), True)
		if self.job.object:
			print self.getId(), 'BEGIN WORKING'
			game.main.session.scheduler.add_new_object(self.finish_working, self, 16)
		else:
			self.reroute()

	def finish_working(self):
		if self.job.object:
			print self.getId(), 'FINISH WORKING'
			self._instance.act("default", self._instance.getFacingLocation(), True)
			# transfer res
			self.transfer_res()
			# deregister at the target we're at
			self.job.object._Provider__collectors.remove(self)
			# move back to home
			self.move_home(callback=self.reached_home)
		else:
			self.reroute()

	def reroute(self):
		print self.getId(), 'Rerouting from', self.position
		# Get a new job
		print "Old job %s" % self.job
		job = self.get_job()
		# Check if there is a new job
		if job:
			# There is a new job!
			self.job = job
			print "New job %s" % self.job
			self.begin_current_job()
		else:
			# There is no new job...
			# Return home and end job
			self.move_home(callback=self.reached_home)

	def reached_home(self):
		""" we finished now our complete work. Let's do it again in 32 ticks
			you can use this as event as after work
		"""
		print self.id, 'FINISHED WORK'

		if self.home_building() is not None:
			remnant = self.home_building().inventory.alter_inventory(self.job.res, self.job.amount)
			assert(remnant == 0)
			remnant = self.inventory.alter_inventory(self.job.res, -self.job.amount)
			assert(remnant == 0)
			self.home_building()._Consumer__collectors.remove(self)
		self.end_job()

	def end_job(self):
		# he finished the job now
		# before the new job can begin this will be executed
		if self.start_hidden:
			self.hide()
		game.main.session.scheduler.add_new_object(self.search_job , self, 32)

	def transfer_res(self):
		print self.id, 'TRANSFER PICKUP'
		res_amount = self.job.object.pickup_resources(self.job.res, self.job.amount)
		# should not to be. register_collector function at the building should prevent it
		print self.id, 'TRANSFERED res:', self.job.res,' amount: ', res_amount,' we should :', self.job.amount
		assert(res_amount == self.job.amount)
		self.inventory.alter_inventory(self.job.res, res_amount)

	def get_collectable_res(self):
		"""Gets all resources the Collector can collect"""
		print self.id, 'GET COLLECTABLE RES'
		# find needed res (only res that we have free room for) - Building function
		return self.home_building().get_needed_res()

	def get_buildings_in_range(self):
		print self.id, 'GET BUILDINGS IN RANGE'
		"""returns all buildings in range
		Overwrite in subclasses that need ranges arroung the pickup."""
		from game.world.provider import Provider
		return [building for building in self.home_building().get_buildings_in_range() if isinstance(building, Provider)]

	def move_home(self, callback=None):
		self.move(self.home_building().position, callback=callback, destination_in_building=True)


class StorageCollector(BuildingCollector):
	""" Same as BuildingCollector, except that it moves on roads.
	Used in storage facilities.
	"""
	movement = Movement.STORAGE_CARRIAGE_MOVEMENT

	def begin_current_job(self):
		"""Declare target of StorageCollector as building, because it always is"""
		super(StorageCollector, self).begin_current_job()
		self.move(self.job.object.position, self.begin_working, destination_in_building = True)

class AnimalCollector(BuildingCollector):
	""" Collector that gets resources from animals """

	def begin_current_job(self):
		"""Tell the animal to stop. First step of a job"""
		print self.id, 'BEGIN CURRENT JOB'
		self.setup_new_job()
		self.stop_animal()

	def pickup_animal(self):
		"""Moves collector to animal. Called by animal when it actually stopped"""
		print self.id, 'PICKUP ANIMAL'
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
		print self.id, 'GET ANIMALS IN RANGE'
		"""returns all buildings in range
		Overwrite in subclasses that need ranges arroung the pickup."""
		return self.home_building().animals

	def stop_animal(self):
		"""Tell animal to stop at the next occasion"""
		print self.id, 'STOP ANIMAL', self.job.object.id
		self.job.object.stop_after_job(self)

	def get_animal(self):
		"""Sends animal to collectors home building"""
		print self.id, 'GET ANIMAL'
		self.job.object.move(self.home_building().position, destination_in_building = True)

	def release_animal(self):
		"""Let animal free after shearing"""
		print self.id, 'RELEASE ANIMAL', self.job.object.getId()
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
