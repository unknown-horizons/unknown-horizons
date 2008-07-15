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

from building import Building, Selectable
from game.world.building.consumer import Consumer
from game.world.building.producer import Producer
from game.world.storage import Storage
from game.world.units.carriage import BuildingCarriage
from game.util.rect import Rect
from game.util.point import Point
from game.gui.tabwidget import TabWidget
import game.main
from buildable import BuildableSingle

class _DummyProducer(Building, BuildableSingle, Selectable, Producer):
	""" Class for internal use in this file only. """
	def __init__(self, x, y, owner, instance = None):
		self.local_carriages = []
		self.inventory = Storage()
		Building.__init__(self, x, y, owner, instance)
		Producer.__init__(self)

class PrimaryProducer(_DummyProducer):
	"""Class used for primary production buildings, e.g. tree

	These object produce something out of nothing, without
	requiring any raw material
	"""

class SecondaryProducer(_DummyProducer, Consumer):
	"""Class used for secondary production buildings, e.g. lumberjack, weaver

	These object turn resources into something else
	"""
	def __init__(self, x, y, owner, instance = None):
		_DummyProducer.__init__(self, x, y, owner, instance)
		Consumer.__init__(self)

	def show_menu(self):
		game.main.session.ingame_gui.show_menu(TabWidget(2, self))

class BuildinglessProducer(Producer, Consumer):
	""" Class for immaterial producers

	For example the sheep uses this to produce wool out of grass,
	because the sheep itself is a unit, not a building
	"""
	def __init__(self):
		self.local_carriages = []
		self.inventory = Storage()
		Producer.__init__(self)
		Consumer.__init__(self, create_carriage = False)

class AnimalFarm(SecondaryProducer):
	""" This class builds pasturage in the radius automatically,
	so that farm animals can graze there """
	def __init__(self, x, y, owner, instance = None):
		SecondaryProducer.__init__(self, x, y, owner, instance)

		self.building_coords = [ (x,y) for x in xrange(self.x, self.x+self.size[0]) for y in xrange(self.y, self.y+self.size[1]) ]
		rect = Rect(self.x, self.y, self.x+self.size[0]-1, self.y+self.size[1]-1)
		center = ((self.x+(self.size[0]/2)), (self.y+(self.size[1]/2)))
		self.pasture_coords = \
		[ (x,y) for x in xrange(self.x-self.radius, self.x+self.size[0]+self.radius+1) \
			for y in xrange(self.y-self.radius, self.y+self.size[1]+self.radius+1) \
				#if ( (((x-center[0]) ** 2) + ((y-center[1]) ** 2)) <= (self.radius ** 2)) and \
				if ( rect.distance( Point(x,y) ) <= self.radius ) and \
				 (x,y) not in self.building_coords ]
		self.pasture = []

		self.recreate_pasture()

		self.animals = []
		animals = game.main.db("SELECT animal, number from animals where building = ?", self.id)
		for (animal,number) in animals:
			for i in xrange(0,number):
				self.animals.append(game.main.session.entities.units[animal](self))

	def show_menu(self):
		game.main.session.ingame_gui.show_menu('herder')

	def recreate_pasture(self):
		""" Turns everything in the radius to pasture, that can be turned"""
		# use building rect here when it exists
		brect = Rect(self.x, self.y, self.x+self.size[0], self.y+self.size[1])

		for coords in self.pasture_coords:
			instance = game.main.session.entities.buildings[18].createInstance(coords[0],coords[1])
			self.pasture.append(game.main.session.entities.buildings[18](coords[0], coords[1], self.owner, instance))

class Lumberjack(SecondaryProducer):
	"""Class representing a Lumberjack."""
	def __init__(self, x, y, owner, instance = None):
		SecondaryProducer.__init__(self, x, y, owner, instance)

		self.building_coords = [ (x,y) for x in xrange(self.x, self.x+self.size[0]) for y in xrange(self.y, self.y+self.size[1]) ]
		rect = Rect(self.x, self.y, self.x+self.size[0]-1, self.y+self.size[1]-1)
		center = ((self.x+(self.size[0]/2)), (self.y+(self.size[1]/2)))

		self.pasture_coords = \
		[ (x,y) for x in xrange(self.x-self.radius, self.x+self.size[0]+self.radius+1) \
			for y in xrange(self.y-self.radius, self.y+self.size[1]+self.radius+1) \
				#if ( (((x-center[0]) ** 2) + ((y-center[1]) ** 2)) <= (self.radius ** 2)) and \
				if ( rect.distance( Point(x,y) ) <= self.radius ) and \
				 (x,y) not in self.building_coords ]

		self.pasture = []

		self.recreate_pasture()

	def recreate_pasture(self):
		""" Turns everything in the radius to pasture, that can be turned"""
		for coords in self.pasture_coords:
			instance = game.main.session.entities.buildings[17].createInstance(coords[0],coords[1])
			building = game.main.session.entities.buildings[17](coords[0], coords[1], self.owner, instance)
			self.island.add_building(coords[0], coords[1], building, self.owner)
			self.pasture.append(building)
			building.start()