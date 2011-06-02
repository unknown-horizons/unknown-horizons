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

from horizons.constants import BUILDINGS
from horizons.util.python import decorators
from horizons.util import WorldObject

class LandManager(WorldObject):
	"""
	Divides the given land into parts meant for different purposes.
	"""

	class purpose:
		production = 0
		village = 1

	def __init__(self, island, owner):
		super(LandManager, self).__init__()
		self.__init(island, owner)
		self._divide()

	def __init(self, island, owner):
		self.island = island
		self.settlement = None
		self.owner = owner
		self.session = self.island.session
		self.production = {}
		self.village = {}

	def save(self, db):
		super(LandManager, self).save(db)
		db("INSERT INTO ai_land_manager(rowid, owner, island) VALUES(?, ?, ?)", self.worldid, \
			self.owner.worldid, self.island.worldid)
		for (x, y) in self.production:
			db("INSERT INTO ai_land_manager_coords(land_manager, x, y, purpose) VALUES(?, ?, ?, ?)", \
				self.worldid, x, y, self.purpose.production)
		for (x, y) in self.village:
			db("INSERT INTO ai_land_manager_coords(land_manager, x, y, purpose) VALUES(?, ?, ?, ?)", \
				self.worldid, x, y, self.purpose.village)

	@classmethod
	def load(cls, db, owner, island, worldid):
		self = cls.__new__(cls)
		self._load(db, owner, island, worldid)
		return self

	def _load(self, db, owner, island, worldid):
		super(LandManager, self).load(db, worldid)
		self.__init(island, owner)

		for x, y, purpose in db("SELECT x, y, purpose FROM ai_land_manager_coords WHERE land_manager = ?", self.worldid):
			coords = (x, y)
			if purpose == self.purpose.production:
				self.production[coords] = self.island.ground_map[coords]
			elif purpose == self.purpose.village:
				self.village[coords] = self.island.ground_map[coords]

	def _coords_usable(self, coords):
		if coords in self.island.ground_map:
			tile = self.island.ground_map[coords]
			if 'constructible' not in tile.classes:
				return False
			if tile.object is not None and not tile.object.buildable_upon:
				return False
			return tile.settlement is None or tile.settlement.owner == self.owner
		return False

	def legal_for_production(self, rect):
		""" Is every tile in the rectangle in production area or on the coast? """
		for coords in rect.tuple_iter():
			if coords in self.village:
				return False
		return True

	def _divide(self):
		"""
		Divides the area of the island so that there is a large lump for the village
		and the rest for production.
		"""
		self.production = {}
		self.village = {}

		best_coords = (0, 0)
		best_buildable = 0

		for (x, y), tile in self.island.ground_map.iteritems():
			buildable = 0
			for dy in xrange(15):
				for dx in xrange(15):
					if self._coords_usable((x + dx, y + dy)):
						buildable += 1

			if buildable > best_buildable:
				best_coords = (x, y)
				best_buildable = buildable
				if buildable == 15 * 15:
					break

		for dy in xrange(15):
			for dx in xrange(15):
				coords = (best_coords[0] + dx, best_coords[1] + dy)
				if self._coords_usable(coords):
					self.village[coords] = self.island.ground_map[coords]

		for coords, tile in self.island.ground_map.iteritems():
			if coords not in self.village and self._coords_usable(coords):
				self.production[coords] = tile

	def display(self):
		village_colour = (255, 255, 255)
		production_colour = (255, 255, 0)
		renderer = self.island.session.view.renderer['InstanceRenderer']

		for tile in self.production.itervalues():
			renderer.addColored(tile._instance, *production_colour)

		for tile in self.village.itervalues():
			renderer.addColored(tile._instance, *village_colour)

decorators.bind_all(LandManager)
