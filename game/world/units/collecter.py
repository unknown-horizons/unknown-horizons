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
import game.main

class BuildingCollecter(Unit):

	def __init__(self, x, y, home_building, slots = 1, size = 6):
		super(BuildingCollecter, self).__init__(x, y)
		self.inventory = ArbitraryStorage(slots, size)
		self.__home_building = home_building

		self.search_job()

	def search_job(self):
		"""Search for a job, only called if the collecter does not have a job."""
		job = self.get_job()
		if job is None:
			game.main.scheduler.add_object(self.search_job, self, 32)
		else:
			self.execute_job(job)

	def get_job(self):
		"""Returns the next job or None"""
		# get collectable res
		#    find needed res (only res that we have free room for) - Building function
		#    and collecter has free room
		# find building in range
		#    providing res in needed_res
		#       check if res is free to pick up
		#
		# return job(building, res, amount)
	def execute_job(self, job):
		"""Executes a job"""

class Job(object):
	def __init__(self, building, res, amount):
		self.building = building
		self.res = res
		self.amount = amount


