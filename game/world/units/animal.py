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
	movement = Movement.COLLECTOR_MOVEMENT

	def __init__(self, home_building, start_hidden=False, **kwargs):
		super(Animal, self).__init__(home_building = home_building, start_hidden = start_hidden, **kwargs)
		self.collector = None

	def save(self, db):
		super(Animal, self).save(db)

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