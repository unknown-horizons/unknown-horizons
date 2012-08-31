# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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
import fnmatch
import os

from horizons.util import Callback, YamlCache

class _EntitiesLazyDict(dict):
	def __init__(self):
		self._future_entries = {}

	def create_on_access(self, key, construction_function):
		self._future_entries[key] = construction_function

	def __getitem__(self, key):
		try:
			return super(_EntitiesLazyDict, self).__getitem__(key)
		except KeyError:
			fun = self._future_entries.pop(key)
			elem = fun()
			self[key] = elem
			return elem


class Entities(object):
	"""Class that stores all the special classes for buildings, grounds etc.
	Stores class objects, not instances.
	Loads everything from the db."""
	loaded = False

	log = logging.getLogger('entities')

	@classmethod
	def load(cls, db, load_now=False):
		if cls.loaded:
			return

		cls.load_grounds(db, load_now)
		cls.load_buildings(db, load_now)
		cls.load_units(load_now)
		cls.loaded = True

	@classmethod
	def load_grounds(cls, db, load_now=False):
		cls.log.debug("Entities: loading grounds")
		if hasattr(cls, "grounds"):
			cls.log.debug("Entities: grounds already loaded")
			return
		from world.ground import GroundClass
		cls.grounds = _EntitiesLazyDict()
		for (ground_id,) in db("SELECT ground_id FROM tile_set"):
			cls.grounds.create_on_access(ground_id, Callback(GroundClass, db, ground_id))
			if load_now:
				cls.grounds[ground_id]
		cls.grounds[-1] = GroundClass(db, -1)

	@classmethod
	def load_buildings(cls, db, load_now=False):
		cls.log.debug("Entities: loading buildings")
		if hasattr(cls, 'buildings'):
			cls.log.debug("Entities: buildings already loaded")
			return
		cls.buildings = _EntitiesLazyDict()
		from world.building import BuildingClass
		for root, dirnames, filenames in os.walk('content/objects/buildings'):
			for filename in fnmatch.filter(filenames, '*.yaml'):
				cls.log.debug("Loading: " + filename)
				# This is needed for dict lookups! Do not convert to os.join!
				full_file = root + "/" + filename
				result = YamlCache.get_file(full_file, game_data=True)
				if result is None: # discard empty yaml files
					print "Empty yaml file {file} found, not loading!".format(file=full_file)
					continue

				result['yaml_file'] = full_file

				building_id = int(result['id'])
				cls.buildings.create_on_access(building_id, Callback(BuildingClass, db=db, id=building_id, yaml_data=result))
				# NOTE: The current system now requires all building data to be loaded
				if load_now or True:
					cls.buildings[building_id]

	@classmethod
	def load_units(cls, load_now=False):
		cls.log.debug("Entities: loading units")
		if hasattr(cls, 'units'):
			cls.log.debug("Entities: units already loaded")
			return
		cls.units = _EntitiesLazyDict()

		from world.units import UnitClass
		for root, dirnames, filenames in os.walk('content/objects/units'):
			for filename in fnmatch.filter(filenames, '*.yaml'):
				full_file = os.path.join(root, filename)
				result = YamlCache.get_file(full_file, game_data=True)
				unit_id = int(result['id'])
				cls.units.create_on_access(unit_id, Callback(UnitClass, id=unit_id, yaml_data=result))
				if load_now:
					cls.units[unit_id]
