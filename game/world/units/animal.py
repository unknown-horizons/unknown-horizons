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
from game.world.units.carriage import BuildingCarriage
from game.world.building.production import SecondaryProducer
from game.world.storage import Storage
from game.util.rect import Rect
from game.util.point import Point
from game.command.building import Build
import game.main 


class Animal(BuildingCarriage):
	grazingTime = 2
	
	def __init__(self, building):
		self.attached_building = building
		
		self.building = game.main.session.entities.buildings[19]()
		
		# workaround: the BuildingCarriage needs coords in ctor for inital placement
		self.building.x = self.attached_building.x
		self.building.y = self.attached_building.y
		BuildingCarriage.__init__(self, self.building, self.building.inventory)
		del self.building.x, self.building.y
		
	def get_possible_pickup_places(self):
		""" Returns places that should be analysed for pickup
		@return: list: [ (building, [ produced_res_id, .. ] ) ]
		"""
		possible_pickup_places = []
		for p in self.attached_building.pasture:
			possible_pickup_places.append( (p, p.prod_res) )
		return possible_pickup_places
	
	def get_position(self):
		return Point(self.unit_position[0], self.unit_position[1])
	
	def reached_pickup(self):
		game.main.session.scheduler.add_new_object(self.finished_grazing, self, game.main.session.timer.ticks_per_second*self.__class__.grazingTime)
		
	def finished_grazing(self):
		self.transfer_pickup()
		self.send()

		
		