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

import horizons.main

class Entities(object):
	"""Class that stores all the special classes for buildings, grounds etc.
	Stores class objects, not instances.
	Loads everything from the db."""
	loaded = False

	@classmethod
	def load(cls):
		if cls.loaded:
			return

		from world.building import BuildingClass
		from world.units import UnitClass
		from world.ground import GroundClass

		cls.grounds = {}
		for (ground_id,) in horizons.main.db("SELECT rowid FROM data.ground"):
			assert ground_id not in cls.grounds
			cls.grounds[ground_id] = GroundClass(ground_id)

		cls.buildings = {}
		for (building_id,) in horizons.main.db("SELECT id FROM data.building"):
			assert building_id not in cls.buildings
			cls.buildings[building_id] = BuildingClass(building_id)

		cls.units = {}
		for (unit_id,) in horizons.main.db("SELECT id FROM data.unit"):
			assert unit_id not in cls.units
			cls.units[unit_id] = UnitClass(unit_id)

		cls.loaded = True
