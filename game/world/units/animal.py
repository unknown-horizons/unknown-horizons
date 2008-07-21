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
from game.world.building.production import BuildinglessProducer
from game.world.storage import Storage
from game.util.rect import Rect
from game.util.point import Point
from game.command.building import Build
import game.main


class Animal(BuildingCollector, BuildinglessProducer):
	grazingTime = 2

	def __init__(self, home_building):
		self.__home_building = home_building
		BuildingCollector.__init__(self, home_building)
		BuildinglessProducer.__init__(self)
		print self.id, "Sheep ID is "
	
		
	
		
	def finish_working(self):
		print self.id, 'FINISH WORKING'
		# TODO: animation change
		# deregister at the target we're at
		self.job.building._Producer__registered_collectors.remove(self)
	
	
	def begin_current_job(self):
		"""Executes the current job"""
		print self.id, 'BEGIN CURRENT JOB'
		self.job.building._Producer__registered_collectors.append(self)
		self.__home_building._Consumer__registered_collectors.append(self)
		if self.start_hidden:
			self.show()
		self.do_move(self.job.path, self.begin_working)
	
	def get_collectable_res(self):
		print self.id, 'GET COLLECTABLE RES'
		return self.get_needed_res()
		