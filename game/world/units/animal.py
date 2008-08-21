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

import random
from game.world.units.unit import Unit
from game.world.units.collector import BuildingCollector
from game.world.units.nature import GrowingUnit
from game.util.rect import Rect
from game.util.point import Point
from collector import Job
from game.world.production import SecondaryProducer
from game.world.pathfinding import Movement
import game.main
import weakref

class Animal(BuildingCollector, GrowingUnit, SecondaryProducer):
	grazingTime = 2
	movement = Movement.CARRIAGE_MOVEMENT

	def __init__(self, home_building, start_hidden=False, **kwargs):
		super(Animal, self).__init__(home_building = home_building, start_hidden = start_hidden, **kwargs)
		self.collector = None

	def save(self, db):
		super(Animal, self).save(db)
		# NOTE: home_building and start_hidden are also set in BuildingCollector

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		if self.collector is not None:
			self.collector.pickup_animal()
			self.collector = None
		else:
			super(Animal, self).search_job()

	def setup_new_job(self):
		self.job.object._Provider__collectors.append(self)

	def finish_working(self):
		print self.id, 'FINISH WORKING'
		# transfer ressources
		self.transfer_res()
		# deregister at the target we're at
		self.job.object._Provider__collectors.remove(self)
		self.end_job()

	def get_job(self):
		"""Returns the next job or None"""
		# FIXME: this code is mostly, if not fully, copied from collector
		#        it's already inconsistent, so delete the double code and
		#        make them share one implementation
		print self.id, 'GET JOB'
		collectable_res = self.get_collectable_res()
		if len(collectable_res) == 0:
			return None
		jobs = []
		for building in self.get_buildings_in_range():
			for res in collectable_res:
				res_amount = building.inventory.get_value(res)
				if res_amount > 0:
					# get sum of picked up ressources for res
					total_pickup_amount = sum([ carriage.job.amount for carriage in building._Provider__collectors if carriage.job.res == res ])
					# check how much will be delivered
					# this is a animal. It delivers to himself. So it can get only one item at time
					total_registered_amount_consumer = 0
					# check if there are ressources left to pickup
					max_consumer_res_free = self.inventory.get_size(res) - self.inventory.get_value(res)
					if res_amount > total_pickup_amount and max_consumer_res_free > 0:
						# add a new job
						jobs.append(Job(building, res, min(res_amount - total_pickup_amount, self.inventory.get_size(res), max_consumer_res_free)))

		## TODO: Sort job list
		jobs.sort(lambda x,y: random.randint(-1,1))

		for job in jobs:
			job.path =  self.check_move(Point(job.object.position.origin.x, job.object.position.origin.y))
			if job.path is not None:
				return job
		return None

	def get_collectable_res(self):
		print self.id, 'GET COLLECTABLE RES'
		return self.get_needed_res()

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

	def create_carriage(self):
		pass
