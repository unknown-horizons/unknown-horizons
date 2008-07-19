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
from game.world.units.carriage import BuildingCarriage
from game.world.units.nature import GrowingUnit
from game.world.building.production import SecondaryProducer
from game.world.storage import Storage
from game.util.rect import Rect
from game.util.point import Point
from game.command.building import Build
import game.main


class Animal(BuildingCarriage, GrowingUnit):
	grazingTime = 2

	def __init__(self, building):
		self.animal_building = building

		self.production = game.main.session.entities.buildings[19]()

		# workaround: the BuildingCarriage needs coords in ctor for inital placement
		BuildingCarriage.__init__(self, self.production, self.production.inventory, attached_building=self.animal_building)

		self.production.restart_animation = self.restart_animation
		self.production.next_animation = self.next_animation

		GrowingUnit.__init__(self, self.production)

	def get_possible_pickup_places(self):
		""" Returns places that should be analysed for pickup
		@return: list: [ (building, [ produced_res_id, .. ] ) ]
		"""
		possible_pickup_places = []
		for p in self.animal_building.pasture:
			possible_pickup_places.append( (p, p.prod_res) )
		return possible_pickup_places

	def get_position(self):
		return self.unit_position

	def calc_best_pickup(self, possible_pickups, max_amount, max_distance):
		pickups = []
		for pickup in possible_pickups:
			if pickup[2] > 0:
				pickups.append(pickup)
		choice = int(round(random.uniform(0, len(pickups)-1)))
		return [pickups[choice][4], pickups[choice]]

	def reached_pickup(self):
		print "reached pickup"
		game.main.session.scheduler.add_new_object(self.finished_grazing, self, game.main.session.timer.ticks_per_second*self.__class__.grazingTime)

	def finished_grazing(self):
		print 'FIN GRAZING AT', self.target
		self.transfer_pickup()
		self.target = []
		if self.production.get_growing_info()[1] > 0:
			# produced something, wait for AnimalCarriage
			pass
		else:
			self.send()

	def next_animation(self):
		# this prevents growing by time
		# cause animals grow, when they ate enough
		# if other animals do grow by time, we need to create two Animal classes,
		self.loop_until = 99999
		GrowingUnit.next_animation(self)

	def move(self, destination, callback = None):
		ret = Unit.move(self, destination, callback)
		# keep position synchronised for pickup
		# this is obviously not exact, but should do it (at least for now)
		self.production.x = self.path[ len(self.path)-1 ][0]
		self.production.y = self.path[ len(self.path)-1 ][1]
		return ret

	def do_move(self, path, callback = None):
		self.production.x = path[ len(path)-1 ][0]
		self.production.y = path[ len(path)-1 ][1]
		Unit.do_move(self, path, callback)
		