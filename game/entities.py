# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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

from game.world.building import BuildingClass
from game.world.units import UnitClass
from game.world.ground import GroundClass
import game.main

class Entities(object):
	"""Class that stores all the special classes for buildings, grounds etc. Stores class objects, not instances.
	Loads everything from the db"""
	def __init__(self):
		super(Entities, self).__init__()
		self.grounds = {}
		for (ground_id,) in game.main.db("SELECT rowid FROM data.ground"):
			self.grounds[ground_id] = GroundClass(ground_id)

		self.buildings = {}
		for (building_id,) in game.main.db("SELECT rowid FROM data.building"):
			self.buildings[building_id] = BuildingClass(building_id)

		self.units = {}
		for (unit_id,) in game.main.db("SELECT rowid FROM data.unit"):
			self.units[unit_id] = UnitClass(unit_id)

	def __del__(self):
		self.grounds = None
		self.buildings = None
		self.units = None
