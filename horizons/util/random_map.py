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

import os
import random
import tempfile
import sys
import re
import string
import copy

from horizons.util import Circle, Rect, Point, DbReader
from horizons.util.uhdbaccessor import read_savegame_template
from horizons.constants import GROUND

# this is how a random island id looks like (used for creation)
_random_island_id_template = "random:${creation_method}:${width}:${height}:${seed}"

# you can check for a random island id with this:
_random_island_id_regexp = r"^random:([0-9]+):([0-9]+):([0-9]+):([\-]?[0-9]+)$"


def is_random_island_id_string(id_string):
	"""Returns whether id_string is an instance of a random island id string"""
	return bool(re.match(_random_island_id_regexp, id_string))

def create_random_island(id_string):
	"""Creates a random island as sqlite db.
	It is rather primitive; it places shapes on the dict.
	The coordinates of tiles will be 0 <= x < width and 0 <= y < height
	@param id_string: random island id string
	@return: sqlite db reader containing island
	"""
	# NOTE: the tilesystem will be redone soon, so constants indicating grounds are temporary
	# here and will have to be changed anyways.
	match_obj = re.match(_random_island_id_regexp, id_string)
	assert match_obj
	creation_method, width, height, seed = [ long(i) for i in match_obj.groups() ]

	rand = random.Random(seed)

	map_set = set()

	# TODO: remove support for creation_method 0 and 1 (they have not been used for new maps since 2011-07-24)
	# creation_method 0 - standard small island for the 3x3 grid
	# creation_method 1 - large island
	# creation_method 2 - a number of randomly sized and placed islands

	# place this number of shapes
	for i in xrange(15 + width * height / 45):
		# place shape determined by shape_id on (x, y)
		add = True
		rect_chance = 6
		if creation_method == 0:
			shape_id = rand.randint(3, 5)
		elif creation_method == 1:
			shape_id = rand.randint(5, 8)
		elif creation_method == 2:
			shape_id = rand.randint(2, 8)
			rect_chance = 29
			if rand.randint(0, 4) == 0:
				rect_chance = 13
				add = False

		shape = None
		if rand.randint(1, rect_chance) == 1:
			# use a rect
			if add:
				x = rand.randint(8, width - 7)
				y = rand.randint(8, height - 7)
				if creation_method == 0:
					shape = Rect.init_from_topleft_and_size(x - 3, y - 3, 5, 5)
				elif creation_method == 1:
					shape = Rect.init_from_topleft_and_size(x - 5, y - 5, 8, 8)
				elif creation_method == 2:
					shape = Rect.init_from_topleft_and_size(x - 5, y - 5, rand.randint(2, 8), rand.randint(2, 8))
			else:
				x = rand.randint(0, width)
				y = rand.randint(0, height)
				shape = Rect.init_from_topleft_and_size(x - 5, y - 5, rand.randint(2, 8), rand.randint(2, 8))
		else:
			# use a circle, where radius is determined by shape_id
			radius = shape_id
			if not add and rand.randint(0, 6) < 5:
				x = rand.randint(-radius * 3 / 2, width + radius * 3 / 2)
				y = rand.randint(-radius * 3 / 2, height + radius * 3 / 2)
				shape = Circle(Point(x, y), shape_id)
			elif width - radius - 4 >= radius + 3 and height - radius - 4 >= radius + 3:
				x = rand.randint(radius + 3, width - radius - 4)
				y = rand.randint(radius + 3, height - radius - 4)
				shape = Circle(Point(x, y), shape_id)

		if shape:
			for shape_coord in shape.tuple_iter():
				if add:
					map_set.add(shape_coord)
				elif shape_coord in map_set:
					map_set.discard(shape_coord)

	# write values to db
	map_db = DbReader(":memory:")
	map_db("CREATE TABLE ground(x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL, action_id TEXT NOT NULL, rotation INTEGER NOT NULL)")
	map_db("CREATE TABLE island_properties(name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")
	map_db("BEGIN TRANSACTION")

	# add grass tiles
	for x, y in map_set:
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?)", x, y, *GROUND.DEFAULT_LAND)

	def fill_tiny_spaces(tile):
		"""Fills 1 tile gulfs and straits with the specified tile
		@param tile: ground tile to fill with
		"""

		all_neighbours = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
		neighbours = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		corners = [(-1, -1), (-1, 1)]
		knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
		bad_configs = set([0, 1 << 0, 1 << 1, 1 << 2, 1 << 3, (1 << 0) | (1 << 3), (1 << 1) | (1 << 2)])

		edge_set = copy.copy(map_set)
		reduce_edge_set = True

		while True:
			to_fill = set()
			to_ignore = set()
			for x, y in edge_set:
				# ignore the tiles with no empty neighbours
				if reduce_edge_set:
					is_edge = False
					for x_offset, y_offset in all_neighbours:
						if (x + x_offset, y + y_offset) not in map_set:
							is_edge = True
							break
					if not is_edge:
						to_ignore.add((x, y))
						continue

				for x_offset, y_offset in neighbours:
					x2 = x + x_offset
					y2 = y + y_offset
					if (x2, y2) in map_set:
						continue
					# (x2, y2) is now a point just off the island

					neighbours_dirs = 0
					for i in xrange(len(neighbours)):
						x3 = x2 + neighbours[i][0]
						y3 = y2 + neighbours[i][1]
						if (x3, y3) not in map_set:
							neighbours_dirs |= (1 << i)
					if neighbours_dirs in bad_configs:
						# part of a straight 1 tile gulf
						to_fill.add((x2, y2))
					else:
						for x_offset, y_offset in corners:
							x3 = x2 + x_offset
							y3 = y2 + y_offset
							x4 = x2 - x_offset
							y4 = y2 - y_offset
							if (x3, y3) in map_set and (x4, y4) in map_set:
								# part of a diagonal 1 tile gulf
								to_fill.add((x2, y2))
								break

				# block 1 tile straits
				for x_offset, y_offset in knight_moves:
					x2 = x + x_offset
					y2 = y + y_offset
					if (x2, y2) not in map_set:
						continue
					if abs(x_offset) == 1:
						y2 = y + y_offset / 2
						if (x2, y2) in map_set or (x, y2) in map_set:
							continue
					else:
						x2 = x + x_offset / 2
						if (x2, y2) in map_set or (x2, y) in map_set:
							continue
					to_fill.add((x2, y2))

				# block diagonal 1 tile straits
				for x_offset, y_offset in corners:
					x2 = x + x_offset
					y2 = y + y_offset
					x3 = x + 2 * x_offset
					y3 = y + 2 * y_offset
					if (x2, y2) not in map_set and (x3, y3) in map_set:
						to_fill.add((x2, y2))
					elif (x2, y2) in map_set and (x2, y) not in map_set and (x, y2) not in map_set:
						to_fill.add((x2, y))

			if to_fill:
				for x, y in to_fill:
					map_set.add((x, y))
					map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?)", x, y, *tile)

				old_size = len(edge_set)
				edge_set = edge_set.difference(to_ignore).union(to_fill)
				reduce_edge_set = old_size - len(edge_set) > 50
			else:
				break

	# possible movement directions
	all_moves = {
		'sw' : (-1, -1),
		'w'  : (-1, 0),
		'nw' : (-1, 1),
		's'  : (0, -1),
		'n'  : (0, 1),
		'se' : (1, -1),
		'e'  : (1, 0),
		'ne' : (1, 1)
		}

	def get_island_outline():
		"""
		@return: the points just off the island as a dict
		"""
		result = set()
		for x, y in map_set:
			for offset_x, offset_y in all_moves.itervalues():
				coords = (x + offset_x, y + offset_y)
				if coords not in map_set:
					result.add(coords)
		return result

	# add grass to sand tiles
	fill_tiny_spaces(GROUND.DEFAULT_LAND)
	outline = get_island_outline()
	for x, y in outline:
		filled = []
		for dir in sorted(all_moves):
			coords = (x + all_moves[dir][1], y + all_moves[dir][0])
			if coords in map_set:
				filled.append(dir)

		tile = None
		# straight coast or 1 tile U-shaped gulfs
		if filled == ['s', 'se', 'sw'] or filled == ['s']:
			tile = GROUND.SAND_NORTH
		elif filled == ['e', 'ne', 'se'] or filled == ['e']:
			tile = GROUND.SAND_WEST
		elif filled == ['n', 'ne', 'nw'] or filled == ['n']:
			tile = GROUND.SAND_SOUTH
		elif filled == ['nw', 'sw', 'w'] or filled == ['w']:
			tile = GROUND.SAND_EAST
		# slight turn (looks best with straight coast)
		elif filled == ['e', 'se'] or filled == ['e', 'ne']:
			tile = GROUND.SAND_WEST
		elif filled == ['n', 'ne'] or filled == ['n', 'nw']:
			tile = GROUND.SAND_SOUTH
		elif filled == ['nw', 'w'] or filled == ['sw', 'w']:
			tile = GROUND.SAND_EAST
		elif filled == ['s', 'sw'] or filled == ['s', 'se']:
			tile = GROUND.SAND_NORTH
		# sandy corner
		elif filled == ['se']:
			tile = GROUND.SAND_NORTHWEST1
		elif filled == ['ne']:
			tile = GROUND.SAND_SOUTHWEST1
		elif filled == ['nw']:
			tile = GROUND.SAND_SOUTHEAST1
		elif filled == ['sw']:
			tile = GROUND.SAND_NORTHEAST1
		# grassy corner
		elif 3 <= len(filled) <= 5:
			coast_set = set(filled)
			if 'e' in coast_set and 'se' in coast_set and 's' in coast_set:
				tile = GROUND.SAND_NORTHEAST3
			elif 's' in coast_set and 'sw' in coast_set and 'w' in coast_set:
				tile = GROUND.SAND_NORTHWEST3
			elif 'w' in coast_set and 'nw' in coast_set and 'n' in coast_set:
				tile = GROUND.SAND_SOUTHWEST3
			elif 'n' in coast_set and 'ne' in coast_set and 'e' in coast_set:
				tile = GROUND.SAND_SOUTHEAST3

		assert tile
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?)", x, y, *tile)
	map_set = map_set.union(outline)

	# add sand to shallow water tiles
	fill_tiny_spaces(GROUND.SAND)
	outline = get_island_outline()
	for x, y in outline:
		filled = []
		for dir in sorted(all_moves):
			coords = (x + all_moves[dir][1], y + all_moves[dir][0])
			if coords in map_set:
				filled.append(dir)

		tile = None
		# straight coast or 1 tile U-shaped gulfs
		if filled == ['s', 'se', 'sw'] or filled == ['s']:
			tile = GROUND.COAST_NORTH
		elif filled == ['e', 'ne', 'se'] or filled == ['e']:
			tile = GROUND.COAST_WEST
		elif filled == ['n', 'ne', 'nw'] or filled == ['n']:
			tile = GROUND.COAST_SOUTH
		elif filled == ['nw', 'sw', 'w'] or filled == ['w']:
			tile = GROUND.COAST_EAST
		# slight turn (looks best with straight coast)
		elif filled == ['e', 'se'] or filled == ['e', 'ne']:
			tile = GROUND.COAST_WEST
		elif filled == ['n', 'ne'] or filled == ['n', 'nw']:
			tile = GROUND.COAST_SOUTH
		elif filled == ['nw', 'w'] or filled == ['sw', 'w']:
			tile = GROUND.COAST_EAST
		elif filled == ['s', 'sw'] or filled == ['s', 'se']:
			tile = GROUND.COAST_NORTH
		# mostly wet corner
		elif filled == ['se']:
			tile = GROUND.COAST_NORTHWEST1
		elif filled == ['ne']:
			tile = GROUND.COAST_SOUTHWEST1
		elif filled == ['nw']:
			tile = GROUND.COAST_SOUTHEAST1
		elif filled == ['sw']:
			tile = GROUND.COAST_NORTHEAST1
		# mostly dry corner
		elif 3 <= len(filled) <= 5:
			coast_set = set(filled)
			if 'e' in coast_set and 'se' in coast_set and 's' in coast_set:
				tile = GROUND.COAST_NORTHEAST3
			elif 's' in coast_set and 'sw' in coast_set and 'w' in coast_set:
				tile = GROUND.COAST_NORTHWEST3
			elif 'w' in coast_set and 'nw' in coast_set and 'n' in coast_set:
				tile = GROUND.COAST_SOUTHWEST3
			elif 'n' in coast_set and 'ne' in coast_set and 'e' in coast_set:
				tile = GROUND.COAST_SOUTHEAST3

		assert tile
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?)", x, y, *tile)
	map_set = map_set.union(outline)

	# add shallow water to deep water tiles
	fill_tiny_spaces(GROUND.SHALLOW_WATER)
	outline = get_island_outline()
	for x, y in outline:
		filled = []
		for dir in sorted(all_moves):
			coords = (x + all_moves[dir][1], y + all_moves[dir][0])
			if coords in map_set:
				filled.append(dir)

		tile = None
		# straight coast or 1 tile U-shaped gulfs
		if filled == ['s', 'se', 'sw'] or filled == ['s']:
			tile = GROUND.DEEP_WATER_NORTH
		elif filled == ['e', 'ne', 'se'] or filled == ['e']:
			tile = GROUND.DEEP_WATER_WEST
		elif filled == ['n', 'ne', 'nw'] or filled == ['n']:
			tile = GROUND.DEEP_WATER_SOUTH
		elif filled == ['nw', 'sw', 'w'] or filled == ['w']:
			tile = GROUND.DEEP_WATER_EAST
		# slight turn (looks best with straight coast)
		elif filled == ['e', 'se'] or filled == ['e', 'ne']:
			tile = GROUND.DEEP_WATER_WEST
		elif filled == ['n', 'ne'] or filled == ['n', 'nw']:
			tile = GROUND.DEEP_WATER_SOUTH
		elif filled == ['nw', 'w'] or filled == ['sw', 'w']:
			tile = GROUND.DEEP_WATER_EAST
		elif filled == ['s', 'sw'] or filled == ['s', 'se']:
			tile = GROUND.DEEP_WATER_NORTH
		# mostly deep corner
		elif filled == ['se']:
			tile = GROUND.DEEP_WATER_NORTHWEST1
		elif filled == ['ne']:
			tile = GROUND.DEEP_WATER_SOUTHWEST1
		elif filled == ['nw']:
			tile = GROUND.DEEP_WATER_SOUTHEAST1
		elif filled == ['sw']:
			tile = GROUND.DEEP_WATER_NORTHEAST1
		# mostly shallow corner
		elif 3 <= len(filled) <= 5:
			coast_set = set(filled)
			if 'e' in coast_set and 'se' in coast_set and 's' in coast_set:
				tile = GROUND.DEEP_WATER_NORTHEAST3
			elif 's' in coast_set and 'sw' in coast_set and 'w' in coast_set:
				tile = GROUND.DEEP_WATER_NORTHWEST3
			elif 'w' in coast_set and 'nw' in coast_set and 'n' in coast_set:
				tile = GROUND.DEEP_WATER_SOUTHWEST3
			elif 'n' in coast_set and 'ne' in coast_set and 'e' in coast_set:
				tile = GROUND.DEEP_WATER_SOUTHEAST3

		assert tile
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?)", x, y, *tile)

	map_db("COMMIT")
	return map_db

def _simplify_seed(seed):
	"""Return the simplified seed value. The goal of this is to make it easier for users to convey the seeds orally."""
	return str(seed).lower().strip()

def generate_map(seed, map_size, water_percent, max_island_size, preferred_island_size, island_size_deviation):
	"""
	Generates a random map.

	@param seed: random number generator seed
	@param map_size: maximum map side length
	@param water_percent: minimum percent of map covered with water
	@param max_island_size: maximum island side length
	@param preferred_island_size: mean of island side lengths
	@param island_size_deviation: deviation of island side lengths
	@return: filename of the SQLite database containing the map
	"""
	max_island_size = min(max_island_size, map_size)
	rand = random.Random(_simplify_seed(seed))
	min_island_size = 20 # minimum chosen island side length (the real size my be smaller)
	min_island_separation = 3 + map_size / 100 # minimum distance between two islands
	max_island_side_coefficient = 4 # maximum value of island's max(side length) / min(side length)

	islands = []
	estimated_land = 0
	max_land_amount = map_size * map_size * (100 - water_percent) / 100

	trial_number = 0
	while trial_number < 100:
		trial_number += 1
		width = max(min_island_size, min(max_island_size, int(round(rand.gauss(preferred_island_size, island_size_deviation)))))
		side_coefficient = min(1 + abs(rand.gauss(0, 0.2)), max_island_side_coefficient)
		side_coefficient = side_coefficient if rand.randint(0, 1) else 1.0 / side_coefficient
		height = max(min_island_size, min(max_island_size, int(round(width * side_coefficient))))
		size = width * height
		if estimated_land + size > max_land_amount:
			continue

		for _ in xrange(13):
			x = rand.randint(0, map_size - width)
			y = rand.randint(0, map_size - height)

			rect = Rect.init_from_topleft_and_size(x, y, width, height)
			blocked = False
			for existing_island in islands:
				if existing_island.distance_to_rect(rect) < min_island_separation:
					blocked = True
					break
			if not blocked:
				islands.append(rect)
				estimated_land += size
				trial_number = 0
				break

	handle, filename = tempfile.mkstemp()
	os.close(handle)
	db = DbReader(filename)
	read_savegame_template(db)

	# move some of the islands to stretch the map to the right size
	if len(islands) > 1:
		min_top = min(rect.top for rect in islands)
		rect = rand.choice([rect for rect in islands if rect.top == min_top])
		islands[islands.index(rect)] = Rect.init_from_borders(rect.left, rect.top - min_top, rect.right, rect.bottom - min_top)

		max_bottom = max(rect.bottom for rect in islands)
		rect = rand.choice([rect for rect in islands if rect.bottom == max_bottom])
		shift = map_size - max_bottom - 1
		islands[islands.index(rect)] = Rect.init_from_borders(rect.left, rect.top + shift, rect.right, rect.bottom + shift)

		min_left = min(rect.left for rect in islands)
		rect = rand.choice([rect for rect in islands if rect.left == min_left])
		islands[islands.index(rect)] = Rect.init_from_borders(rect.left - min_left, rect.top, rect.right - min_left, rect.bottom)

		max_right = max(rect.right for rect in islands)
		rect = rand.choice([rect for rect in islands if rect.right == max_right])
		shift = map_size - max_right - 1
		islands[islands.index(rect)] = Rect.init_from_borders(rect.left + shift, rect.top, rect.right + shift, rect.bottom)

	for rect in islands:
		island_seed = rand.randint(-sys.maxint, sys.maxint)
		island_params = {'creation_method': 2, 'seed': island_seed, 'width': rect.width, 'height': rect.height}
		island_string = string.Template(_random_island_id_template).safe_substitute(island_params)
		db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", rect.left, rect.top, island_string)

	return filename

def generate_map_from_seed(seed):
	"""
	Generates a random map with the given seed and default parameters.

	@param seed: random number generator seed
	@return: filename of the SQLite database containing the map
	"""

	return generate_map(seed, 150, 50, 70, 70, 30)

def generate_huge_map_from_seed(seed):
	"""Same as generate_map_from_seed, but making it as big as it is still reasonable"""
	return generate_map(seed, 250, 20, 70, 70, 5)
