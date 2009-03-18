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

import random
import weakref

import game.main

from game.world.production import SecondaryProducer
from game.world.pathfinding import Movement
from game.util import Rect, Point, WorldObject
from unit import Unit
from collector import BuildingCollector
from nature import GrowingUnit
from collector import Job

class Animal(BuildingCollector, GrowingUnit, SecondaryProducer):
	grazingTime = 2
	movement = Movement.COLLECTOR_MOVEMENT

	def __init__(self, home_building, start_hidden=False, **kwargs):
		super(Animal, self).__init__(home_building = home_building, \
																 start_hidden = start_hidden, **kwargs)
		self.__init()

	def __init(self):
		self.collector = None

	def register_at_home_building(self):
		self.home_building().animals.append(self)

	def save(self, db):
		super(Animal, self).save(db)

	def load(self, db, worldid):
		super(Animal, self).load(db, worldid)
		self.__init()

	def search_job(self):
		"""Search for a job, only called if the collector does not have a job."""
		if self.collector is not None:
			self.collector.pickup_animal()
			self.collector = None
			self.state = self.states.stopped
		else:
			super(Animal, self).search_job()

	def setup_new_job(self):
		self.job.object._Provider__collectors.append(self)

	def finish_working(self):
		#print self.id, 'FINISH WORKING'
		# transfer ressources
		self.transfer_res()
		# deregister at the target we're at
		self.job.object._Provider__collectors.remove(self)
		self.end_job()

	def get_collectable_res(self):
		#print self.id, 'GET COLLECTABLE RES'
		return self.get_needed_res()

	def stop_after_job(self, collector):
		"""Tells the unit to stop after the current job and call the collector to pick it up"""
		self.collector = collector

	def create_collector(self):
		pass

	def sort_jobs(self, jobs):
		from random import shuffle
		shuffle(jobs)
		return jobs