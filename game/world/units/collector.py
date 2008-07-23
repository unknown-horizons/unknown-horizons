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
from game.world.storage import ArbitraryStorage
from game.util import Rect, Point
from game.world.pathfinding import Movement
from game.world.building.producer import Producer
import game.main
import operator
import weakref


class BuildingCollector(Unit):
	movement = Movement.CARRIAGE_MOVEMENT
	"""
	How does this class work ?
	Timeline:
	init
	|-search_job()
	  |- get_job   - he found a job ( it's best )
	  |-

	"""

	def __init__(self, home_building, slots = 1, size = 6, start_hidden=True):
		super(BuildingCollector, self).__init__(home_building.x, home_building.y)
		self.inventory = ArbitraryStorage(slots, size)
		
		def remove_actionlistener(ref):
			import pdb
			pdb.Pdb().set_trace()
			self._instance.removeActionListener(self)
		
		self.home_building = weakref.ref(home_building, remove_actionlistener)
		
		self.start_hidden = start_hidden
		if self.start_hidden:
			self.hide()
		self.search_job()

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
		
		if (self.home_building() is None) : return None
		
		print self.id, 'GET JOB'
		collectable_res = self.get_collectable_res()
		if len(collectable_res) == 0:
			return None
		jobs = []
		for building in self.get_buildings_in_range():
			for res in collectable_res:
				res_amount = building.inventory.get_value(res)
				if res_amount > 0:
					# get sum of picked up resources for res
					total_pickup_amount = sum([ carriage.job.amount for carriage in building._Producer__registered_collectors if carriage.job.res == res ])
					# check how much will be delivered
					total_registered_amount_consumer = sum([ carriage.job.amount for carriage in self.home_building()._Consumer__registered_collectors if carriage.job.res == res ])
					# check if there are resources left to pickup
					max_consumer_res_free = self.home_building().inventory.get_size(res)-(total_registered_amount_consumer+self.home_building().inventory.get_value(res))
					if res_amount > total_pickup_amount and max_consumer_res_free > 0:
						# add a new job
						jobs.append(Job(building, res, min(res_amount - total_pickup_amount, self.inventory.get_size(res), max_consumer_res_free)))


		## TODO: Sort job list
		jobs.sort(key=operator.attrgetter('rating') )
		jobs.reverse()


		for job in jobs:
			job.path =  self.check_move(Point(job.object.x, job.object.y))
			if job.path is not None:
				return job
		return None

	def begin_current_job(self):
		"""Executes the current job"""
		print self.id, 'BEGIN CURRENT JOB'
		self.job.object._Producer__registered_collectors.append(self)
		self.home_building()._Consumer__registered_collectors.append(self)
		if self.start_hidden:
			self.show()
		self.do_move(self.job.path, self.begin_working)

	def begin_working(self):
		""""""
		# TODO: animation change
		print self.id, 'BEGIN WORKING'
		game.main.session.scheduler.add_new_object(self.finish_working, self, 16)

	def finish_working(self):
		print self.id, 'FINISH WORKING'
		# TODO: animation change
		# transfer res
		self.transfer_res()
		# deregister at the target we're at
		self.job.object._Producer__registered_collectors.remove(self)
		# reverse the path
		self.job.path.reverse()
		# move back to home
		self.do_move(self.job.path, self.reached_home)
	
	def end_job(self):
		# he finished the job now
		# before the new job can begin this will be executed
		game.main.session.scheduler.add_new_object(self.search_job , self, 32)
		

	def reached_home(self):
		""" we finished now our complete work. Let's do it again in 32 ticks
			you can use this as event as after work
		"""
		print self.id, 'FINISHED WORK'
		
		if self.home_building() is not None:
			assert(self.home_building().inventory.alter_inventory(self.job.res, self.job.amount) == 0)
			assert(self.inventory.alter_inventory(self.job.res, -self.job.amount) == 0)
		if self.start_hidden:
			self.hide()
		self.home_building()._Consumer__registered_collectors.remove(self)
		self.end_job()


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
		return [building for building in self.home_building().get_buildings_in_range() if isinstance(building, Producer)]

	
class StorageCollector(BuildingCollector):
	""" Same as BuildingCollector, except that it moves on roads.
	Used in storage facilities.
	"""
	movement = Movement.STORAGE_CARRIAGE_MOVEMENT


class AnimalCollector(BuildingCollector):
	""" Collector that gets resources from animals """
	pass

class Job(object):
	def __init__(self, object, res, amount):
		self.object = object
		self.res = res
		self.amount = amount
		self.path = []
		
		# this is rather a dummy
		self.rating = amount


