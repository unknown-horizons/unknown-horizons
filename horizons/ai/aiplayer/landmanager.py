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

import math

from horizons.constants import AI, BUILDINGS
from horizons.util.python import decorators
from horizons.util import WorldObject

class LandManager(WorldObject):
	"""
	Divides the given land into parts meant for different purposes.
	"""

	class purpose:
		production = 0
		village = 1

	def __init__(self, island, owner, feeder_island):
		super(LandManager, self).__init__()
		self.__init(island, owner, feeder_island)
		if self.feeder_island:
			self._prepare_feeder_island()
		else:
			self._divide_island()

	def _divide_island(self):
		min_side = 18
		max_side = 22

		min_x, max_x = None, None
		min_y, max_y = None, None
		land = 0
		for (x, y), tile in self.island.ground_map.iteritems():
			if 'constructible' not in tile.classes:
				continue
			if tile.object is not None and not tile.object.buildable_upon:
				continue
			if tile.settlement is not None:
				continue

			land += 1
			if min_x is None or x < min_x:
				min_x = x
			if max_x is None or x > max_x:
				max_x = x
			if min_y is None or y < min_y:
				min_y = y
			if max_y is None or y > max_y:
				max_y = y
		width = max_x - min_x + 1
		height = max_y - min_y + 1

		village_area = 0.28
		if land > 40 * 40:
			village_area = 0.3
		elif land > 50 * 50:
			village_area = 0.32
		elif land > 60 * 60:
			village_area = 0.35
		village_area *= 2.5
		chosen_area = max(9 * 9, int(round(land * village_area)))

		side = int(math.floor(math.sqrt(chosen_area)))
		if side <= max_side:
			side = min(side, width)
			self._divide(side, chosen_area // side)
		else:
			best_sections = 1000
			best_side1 = None
			best_side2 = None

			for side1 in xrange(9, max(10, chosen_area // 9 + 1)):
				real_side1 = min(side1, width)
				real_side2 = min(chosen_area // real_side1, height)
				horizontal_sections = int(math.ceil(float(real_side1) / max_side))
				vertical_sections = int(math.ceil(float(real_side2) / max_side))
				sections = horizontal_sections * vertical_sections
				if best_sections > sections or (best_sections == sections and abs(real_side1 - real_side2) < abs(best_side1 - best_side2)):
					best_sections = sections
					best_side1 = real_side1
					best_side2 = real_side2
			self._divide(best_side1, best_side2)

	def __init(self, island, owner, feeder_island):
		self.island = island
		self.settlement = None
		self.owner = owner
		self.feeder_island = feeder_island
		self.session = self.island.session
		self.production = {}
		self.village = {}
		self.roads = set() # set((x, y), ...) of coordinates where road can be built independent of the area purpose
		self.resource_deposits = {}
		self.resource_deposits[BUILDINGS.CLAY_DEPOSIT_CLASS] = self._get_buildings_by_id(BUILDINGS.CLAY_DEPOSIT_CLASS)
		self.resource_deposits[BUILDINGS.MOUNTAIN_CLASS] = self._get_buildings_by_id(BUILDINGS.MOUNTAIN_CLASS)

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

	def _get_buildings_by_id(self, building_id):
		result = []
		for coords in self.island.ground_map:
			object = self.island.ground_map[coords].object
			if object is not None and object.id == building_id:
				result.append(object)
		return result

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

	def _get_usability_map(self, extra_space):
		map = {}
		for coords, tile in self.island.ground_map.iteritems():
			if 'constructible' not in tile.classes:
				continue
			if tile.object is not None and not tile.object.buildable_upon:
				continue
			if tile.settlement is None or tile.settlement.owner == self.owner:
				map[coords] = 1

		xs, ys = zip(*map.iterkeys())
		min_x = min(xs) - extra_space
		max_x = max(xs)
		min_y = min(ys) - extra_space
		max_y = max(ys)

		for x in xrange(min_x, max_x + 1):
			for y in xrange(min_y, max_y + 1):
				coords = (x, y)
				if coords not in map:
					map[coords] = 0

		return (map, min_x, max_x, min_y, max_y)

	def _divide(self, side1, side2):
		"""
		Divides the area of the island so that there is a large lump for the village
		and the rest for production.
		"""
		usability_map, min_x, max_x, min_y, max_y = self._get_usability_map(max(side1, side2))

		best_coords = (0, 0)
		best_buildable = 0
		best_sides = (None, None)

		sizes = [(side1, side2)]
		if side1 != side2:
			sizes.append((side2, side1))

		for width, height in sizes:
			horizontal_strip = {} # (x, y): number of usable tiles from (x - width + 1, y) to (x, y)
			usable_area = {} # (x, y): number of usable tiles from (x - width + 1, y - height + 1) to (x, y)
			for x in xrange(min_x, max_x + 1):
				for dy in xrange(height):
					horizontal_strip[(x, min_y + dy)] = 0
					usable_area[(x, min_y + dy)] = 0
			for y in xrange(min_y, max_y + 1):
				for dx in xrange(width):
					horizontal_strip[(min_x +dx, y)] = 0
					usable_area[(min_x + dx, y)] = 0

			for y in xrange(min_y + height, max_y + 1):
				for x in xrange(min_x + width, max_x + 1):
					horizontal_strip[(x, y)] = horizontal_strip[(x - 1, y)] + usability_map[(x, y)] - usability_map[(x - width, y)]

			for x in xrange(min_x + width, max_x + 1):
				for y in xrange(min_y + height, max_y + 1):
					coords = (x, y)
					usable_area[coords] = usable_area[(x, y - 1)] + horizontal_strip[(x, y)] - horizontal_strip[(x, y - height)]

					if usable_area[coords] > best_buildable:
						best_coords = (x - width + 1, y - height + 1)
						best_buildable = usable_area[coords]
						best_sides = (width, height)

		self.production = {}
		self.village = {}

		for dx in xrange(best_sides[0]):
			for dy in xrange(best_sides[1]):
				coords = (best_coords[0] + dx, best_coords[1] + dy)
				if usability_map[coords] == 1:
					self.village[coords] = self.island.ground_map[coords]

		for coords, tile in self.island.ground_map.iteritems():
			if coords not in self.village and self._coords_usable(coords):
				self.production[coords] = tile

	def _prepare_feeder_island(self):
		self.production = {}
		self.village = {}
		for coords, tile in self.island.ground_map.iteritems():
			if self._coords_usable(coords):
				self.production[coords] = tile

	def add_to_production(self, coords):
		self.production[coords] = self.village[coords]
		del self.village[coords]

	def display(self):
		if not AI.HIGHLIGHT_PLANS:
			return

		village_colour = (255, 255, 255)
		production_colour = (255, 255, 0)
		renderer = self.island.session.view.renderer['InstanceRenderer']

		for tile in self.production.itervalues():
			renderer.addColored(tile._instance, *production_colour)

		for tile in self.village.itervalues():
			renderer.addColored(tile._instance, *village_colour)

decorators.bind_all(LandManager)
