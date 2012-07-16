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

import math
import logging

from collections import defaultdict

from horizons.constants import AI, BUILDINGS, RES
from horizons.util.python import decorators
from horizons.util import WorldObject
from horizons.component.storagecomponent import StorageComponent

class LandManager(WorldObject):
	"""
	Divides and manages the division of the land of one island.

	The idea is that the LandManager object divides the land of the island between
	different purposes (currently the production area and on non-feeder islands the
	village area) and from that point on the different area managers are limited to that
	land unless they decide to give some of it up (currently happens with the village area).
	"""

	log = logging.getLogger("ai.aiplayer.land_manager")

	class purpose:
		production = 0
		village = 1

	def __init__(self, island, owner, feeder_island):
		"""
		@param island: Island instance
		@param owner: AIPlayer instance
		@param feeder_island: boolean showing whether this is a feeder island (no village area)
		"""

		super(LandManager, self).__init__()
		self.__init(island, owner, feeder_island)
		if self.feeder_island:
			self._prepare_feeder_island()
		else:
			self._divide_island()

	def __init(self, island, owner, feeder_island):
		self.island = island
		self.settlement = None
		self.owner = owner
		self.feeder_island = feeder_island
		self.session = self.island.session
		self.production = {}
		self.village = {}
		self.roads = set() # set((x, y), ...) of coordinates where road can be built independent of the area purpose
		self.coastline = self._get_coastline() # set((x, y), ...) of coordinates which coastal buildings could use in the production area
		self.personality = self.owner.personality_manager.get('LandManager')
		self.refresh_resource_deposits()

	def save(self, db):
		super(LandManager, self).save(db)
		db("INSERT INTO ai_land_manager(rowid, owner, island, feeder_island) VALUES(?, ?, ?, ?)", self.worldid,
			self.owner.worldid, self.island.worldid, self.feeder_island)
		for (x, y) in self.production:
			db("INSERT INTO ai_land_manager_coords(land_manager, x, y, purpose) VALUES(?, ?, ?, ?)",
				self.worldid, x, y, self.purpose.production)
		for (x, y) in self.village:
			db("INSERT INTO ai_land_manager_coords(land_manager, x, y, purpose) VALUES(?, ?, ?, ?)",
				self.worldid, x, y, self.purpose.village)

	@classmethod
	def load(cls, db, owner, worldid):
		self = cls.__new__(cls)
		self._load(db, owner, worldid)
		return self

	def _load(self, db, owner, worldid):
		super(LandManager, self).load(db, worldid)
		island_id, feeder_island = db("SELECT island, feeder_island FROM ai_land_manager WHERE rowid = ?", worldid)[0]
		self.__init(WorldObject.get_object_by_id(island_id), owner, feeder_island)

		for x, y, purpose in db("SELECT x, y, purpose FROM ai_land_manager_coords WHERE land_manager = ?", self.worldid):
			coords = (x, y)
			if purpose == self.purpose.production:
				self.production[coords] = self.island.ground_map[coords]
			elif purpose == self.purpose.village:
				self.village[coords] = self.island.ground_map[coords]

	def _get_coastline(self):
		result = set()
		for coords in self.island.ground_map:
			tile = self.island.ground_map[coords]
			if 'coastline' not in tile.classes:
				continue
			if tile.object is not None and not tile.object.buildable_upon:
				continue
			if tile.settlement is not None and tile.settlement.owner is not self.owner:
				continue
			result.add(coords)
		return result

	def refresh_resource_deposits(self):
		self.resource_deposits = defaultdict(lambda: []) # {resource_id: [tile, ...]} all resource deposits of a type on the island
		for resource_id, building_ids in {RES.RAW_CLAY: [BUILDINGS.CLAY_DEPOSIT, BUILDINGS.CLAY_PIT], RES.RAW_IRON: [BUILDINGS.MOUNTAIN, BUILDINGS.IRON_MINE]}.iteritems():
			for building in self.island.buildings:
				if building.id in building_ids:
					if building.get_component(StorageComponent).inventory[resource_id] > 0:
						self.resource_deposits[resource_id].append(self.island.ground_map[building.position.origin.to_tuple()])

	def _divide_island(self):
		"""Divide the whole island between the purposes. The proportions depend on the personality."""
		min_x, max_x = None, None
		min_y, max_y = None, None
		land = 0
		for x, y in self.island.ground_map:
			if self.coords_usable((x, y)):
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
		self.log.info('%s island width %d, height %d', self, width, height)

		village_area = self.personality.village_area_small
		if land > 60 * 60:
			village_area = self.personality.village_area_60
		elif land > 50 * 50:
			village_area = self.personality.village_area_50
		elif land > 40 * 40:
			village_area = self.personality.village_area_40
		chosen_area = max(self.personality.min_village_size, int(round(land * village_area)))
		min_village_area = int(round(chosen_area * self.personality.min_village_proportion))
		self.log.info('%s land %d, village area %.2f, chosen area %d, minimum preliminary village area %d', self, land, village_area, chosen_area, min_village_area)

		side = int(math.floor(math.sqrt(chosen_area)))
		if side <= self.personality.max_section_side:
			side = min(side, width)
			self._divide(side, chosen_area // side)
		else:
			best_sections = 1000
			best_side1 = None
			best_side2 = None

			for side1 in xrange(9, max(10, chosen_area // 9 + 1)):
				real_side1 = min(side1, width)
				real_side2 = min(chosen_area // real_side1, height)
				if real_side1 * real_side2 < min_village_area:
					continue

				horizontal_sections = int(math.ceil(float(real_side1) / self.personality.max_section_side))
				vertical_sections = int(math.ceil(float(real_side2) / self.personality.max_section_side))
				sections = horizontal_sections * vertical_sections
				if best_sections > sections or (best_sections == sections and abs(real_side1 - real_side2) < abs(best_side1 - best_side2)):
					best_sections = sections
					best_side1 = real_side1
					best_side2 = real_side2
			self._divide(best_side1, best_side2)

	def coords_usable(self, coords):
		"""Return a boolean showing whether the land on the given coordinate is usable for a normal building."""
		if coords in self.island.ground_map:
			tile = self.island.ground_map[coords]
			if 'constructible' not in tile.classes:
				return False
			if tile.object is not None and not tile.object.buildable_upon:
				return False
			return tile.settlement is None or tile.settlement.owner is self.owner
		return False

	def legal_for_production(self, rect):
		"""Return a boolean showing whether every tile in the Rect is either in the production area or on the coast."""
		for coords in rect.tuple_iter():
			if coords in self.village:
				return False
		return True

	def _get_usability_map(self, extra_space):
		"""
		Return a tuple describing the usability of the island.

		The return format is ({x, y): usable, ..}, min_x - extra_space, max_x, min_y - extra_space, max_y)
		where the dict contains ever key for x in [min_x, max_x] and y in [min_y, max_y] and the
		usability value says whether we can use that part of the land for normal buildings.
		"""

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
		"""Divide the total land area between different purposes trying to achieve a side1 x side2 rectangle for the village."""
		usability_map, min_x, max_x, min_y, max_y = self._get_usability_map(max(side1, side2))
		self.log.info('%s divide %d x %d', self, side1, side2)

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
			if coords not in self.village and self.coords_usable(coords):
				self.production[coords] = tile

	def _prepare_feeder_island(self):
		"""Assign all the usable land of the island to the production area."""
		self.production = {}
		self.village = {}
		for coords, tile in self.island.ground_map.iteritems():
			if self.coords_usable(coords):
				self.production[coords] = tile

	def add_to_production(self, coords):
		"""Assign a current village tile to the production area."""
		self.production[coords] = self.village[coords]
		del self.village[coords]

	def handle_lost_area(self, coords_list):
		"""Handle losing the potential land in the given coordinates list."""
		# reduce the areas for the village, production, roads, and coastline
		for coords in coords_list:
			if coords in self.village:
				del self.village[coords]
			elif coords in self.production:
				del self.production[coords]
			self.roads.discard(coords)
			self.coastline.discard(coords)

	def display(self):
		"""Show the plan on the map unless it is disabled in the settings."""
		if not AI.HIGHLIGHT_PLANS:
			return

		village_colour = (255, 255, 255)
		production_colour = (255, 255, 0)
		coastline_colour = (0, 0, 255)
		renderer = self.island.session.view.renderer['InstanceRenderer']

		for tile in self.production.itervalues():
			renderer.addColored(tile._instance, *production_colour)

		for tile in self.village.itervalues():
			renderer.addColored(tile._instance, *village_colour)

		for coords in self.coastline:
			renderer.addColored(self.island.ground_map[coords]._instance, *coastline_colour)

	def __str__(self):
		return '%s LandManager(%s)' % (self.owner if hasattr(self, 'owner') else 'unknown player', self.worldid if hasattr(self, 'worldid') else 'none')

decorators.bind_all(LandManager)
