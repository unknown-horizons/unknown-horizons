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
from game.world.units.carriage import BuildingCarriage, AnimalCarriage
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
		self.x, self.y = None, None
		self.local_carriages = []
		self.inventory = Storage()
		Producer.__init__(self)
		Consumer.__init__(self)

	def create_carriage(self):
		# this class of buildings doesn't have carriages
		pass

class AnimalFarm(SecondaryProducer):
	""" This class builds pasturage in the radius automatically,
	so that farm animals can graze there """
	def __init__(self, x, y, owner, instance = None):
		SecondaryProducer.__init__(self, x, y, owner, instance)

		self.pasture = []

		self.recreate_pasture()

		self.animals = []
		animals = game.main.db("SELECT animal, number from animals where building = ?", self.id)
		for (animal,number) in animals:
			for i in xrange(0,number):
				self.animals.append(game.main.session.entities.units[animal](self))

		self.create_carriage()

	def create_carriage(self):
		self.local_carriages.append(game.main.session.entities.units[7](self))

	def recreate_pasture(self):
		""" Turns everything in the radius to pasture, that can be turned"""
		## TODO: don't create pasture on tiles like rocks, mountains, water..
		for coords in self.radius_coords:
			instance = game.main.session.entities.buildings[18].createInstance(coords[0],coords[1])
			building = game.main.session.entities.buildings[18](coords[0], coords[1], self.owner, instance)
			self.island.add_building(coords[0], coords[1], building, self.owner)
			self.pasture.append(building)
			building.start()

class Lumberjack(SecondaryProducer):
	"""Class representing a Lumberjack."""
	def __init__(self, x, y, owner, instance = None):
		SecondaryProducer.__init__(self, x, y, owner, instance)

		self.pasture = []

		self.recreate_pasture()

	def recreate_pasture(self):
		""" Turns everything in the radius to pasture, that can be turned"""
		for coords in self.radius_coords:
			instance = game.main.session.entities.buildings[17].createInstance(coords[0],coords[1])
			building = game.main.session.entities.buildings[17](coords[0], coords[1], self.owner, instance)
			self.island.add_building(coords[0], coords[1], building, self.owner)
			self.pasture.append(building)
			building.start()
