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

from game.world.building import BuildingClass
from game.world.units import UnitClass
from game.world.ground import GroundClass
import game.main
from living import *

class Entities(livingObject):
	"""Class that stores all the special classes for buildings, grounds etc. Stores class objects, not instances."""
	def begin(self):
		super(Entities, self).begin()
		self._instances = {}
		self._instances_id = 0

		self.grounds = {}
		for (ground_id,) in game.main.db("SELECT rowid FROM data.ground"):
			self.grounds[ground_id] = GroundClass(ground_id)

		self.buildings = {}
		for (building_id,) in game.main.db("SELECT rowid FROM data.building"):
			self.buildings[building_id] = BuildingClass(building_id)

		self.units = {}
		for (unit_id,) in game.main.db("SELECT rowid FROM data.unit"):
			self.units[unit_id] = UnitClass(unit_id)

	def registerInstance(self, instance):
		id = self._instances_id
		self._instances[id] = instance
		self._instances_id += 1
		return str(id)

	def updateInstance(self, id, instance):
		self._instances[int(id)] = instance

	def deleteInstance(self, id):
		del self._instances[int(id)]

	def getInstance(self, id):
		return self._instances[int(id)]
