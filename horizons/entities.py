# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import logging

class Entities(object):
	"""Class that stores all the special classes for buildings, grounds etc.
	Stores class objects, not instances.
	Loads everything from the db."""
	loaded = False

	log = logging.getLogger('entities')

	@classmethod
	def load(cls, db):
		if cls.loaded:
			return

		cls.load_grounds(db)
		cls.load_buildings(db)
		cls.load_units(db)
		cls.loaded = True

	@classmethod
	def load_grounds(cls, db):
		cls.log.debug("Entities: loading grounds")
		if hasattr(cls, "grounds"):
			cls.log.debug("Entities: grounds already loaded")
			return
		from world.ground import GroundClass
		cls.grounds = {}
		for (ground_id,) in db("SELECT id FROM data.ground"):
			assert ground_id not in cls.grounds
			cls.grounds[ground_id] = GroundClass(db, ground_id)

	@classmethod
	def load_buildings(cls, db):
		cls.log.debug("Entities: loading buildings")
		if hasattr(cls, 'buildings'):
			cls.log.debug("Entities: buildings already loaded")
			return
		cls.buildings = {}
		from world.building import BuildingClass
		for (building_id,) in db("SELECT id FROM data.building"):
			assert building_id not in cls.buildings
			cls.buildings[building_id] = BuildingClass(db, building_id)

	@classmethod
	def load_units(cls, db):
		cls.log.debug("Entities: loading units")
		if hasattr(cls, 'units'):
			cls.log.debug("Entities: units already loaded")
			return
		cls.units = {}
		from world.units import UnitClass
		for (unit_id,) in db("SELECT id FROM data.unit"):
			assert unit_id not in cls.units
			cls.units[unit_id] = UnitClass(db, unit_id)
