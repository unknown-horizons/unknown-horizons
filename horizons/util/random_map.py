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
import random
import tempfile
import sys
import shutil
import re
import string
import time

from horizons.util import Circle, Rect, Point, DbReader
from horizons.constants import GROUND, PATHS
from horizons.ext.enum import Enum

# this is how a random island id looks like (used for creation)
_random_island_id_template = "random:${creation_method}:${width}:${height}:${seed}"

# you can check for a random island id with this:
_random_island_id_regexp = r"random:([0-9]+):([0-9]+):([0-9]+):([\-]?[0-9]+)"


def is_random_island_id_string(id_string):
	"""Returns whether id_string is an instance of a random island id string"""
	return bool(re.match(_random_island_id_regexp, id_string))

def create_random_island(id_string):
	"""Creates a random island as sqlite db.
	It is rather primitive; it places shapes on the dict.
	@param id_string: random island id string
	@return: sqlite db reader containing island
	"""
	# NOTE: the tilesystem will be redone soon, so constants indicating grounds are temporary
	# here and will have to be changed anyways.
	match_obj = re.match(_random_island_id_regexp, id_string)
	assert match_obj
	creation_method, width, height, seed = [ long(i) for i in match_obj.groups() ]

	rand = random.Random(seed)

	map_dict = {}
	groundTypes = Enum('ground', 'coast')

	# creation_method 0 - standard small island for the 3x3 grid
	# creation_method 1 - large island

	# place this number of shapes
	for i in xrange( int(float(width+height)/2 * 1.5) ):
		x = rand.randint(4, width-4)
		y = rand.randint(4, height -4)

		# place shape determined by shape_id on (x, y)
		if creation_method == 0:
			shape_id = rand.randint(3, 5)
		elif creation_method == 1:
			shape_id = rand.randint(5, 8)

		if rand.randint(1,4) == 1:
			# use a rect
			if creation_method == 0:
				for shape_coord in Rect.init_from_topleft_and_size(x-3, y-3, 5, 5).tuple_iter():
					map_dict[shape_coord] = groundTypes.ground
			elif creation_method == 1:
				for shape_coord in Rect.init_from_topleft_and_size(x-5, y-5, 8, 8).tuple_iter():
					map_dict[shape_coord] = groundTypes.ground

		else:
			# use a circle, where radius is determined by shape_id
			for shape_coord in Circle(Point(x, y), shape_id).tuple_iter():
				map_dict[shape_coord] = groundTypes.ground

	# remove 1 tile peninsulas
	neighbours = [(-1, 0), (0, -1), (0, 1), (1, 0)]
	bad_configs = set([0, 1 << 0, 1 << 1, 1 << 2, 1 << 3, (1 << 0) | (1 << 3), (1 << 1) | (1 << 2)])
	while True:
		to_delete = []
		for x, y in map_dict.iterkeys():
			neighbours_dirs = 0
			for i in range(len(neighbours)):
				if (x + neighbours[i][0], y + neighbours[i][1]) in map_dict:
					neighbours_dirs |= (1 << i)
			if neighbours_dirs in bad_configs:
				to_delete.append((x, y))
		if to_delete:
			for coords in to_delete:
				del map_dict[coords]
		else:
			break

	# write values to db
	map_db = DbReader(":memory:")
	map_db("CREATE TABLE ground(x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL)")
	map_db("CREATE TABLE island_properties(name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)")
	map_db("BEGIN TRANSACTION")

	# assign these characters, if a coastline is found in this offset
	offset_coastline = {
		'sw' : (-1, -1),
		'w'  : (-1, 0),
		'nw' : (-1, 1),
		's'  : (0, -1),
		'n'  : (0, 1),
		'se' : (1, -1),
		'e'  : (1, 0),
		'ne' : (1, 1)
		}

	# mark the coast, construct a border around the island
	deep_water_dict = {}
	for x, y in map_dict.iterkeys():
		for dir in offset_coastline:
			x2 = x + offset_coastline[dir][1]
			y2 = y + offset_coastline[dir][0]
			if (x2, y2) not in map_dict:
				map_dict[(x, y)] = groundTypes.coast
				deep_water_dict[(x2, y2)] = True

	# add the shallow water to deep water tiles
	for x, y in deep_water_dict.iterkeys():
		coastline = []
		for dir in sorted(offset_coastline):
			coords = (x + offset_coastline[dir][1], y + offset_coastline[dir][0])
			if coords not in map_dict and coords not in deep_water_dict:
				coastline.append(dir)

		tile = GROUND.SHALLOW_WATER
		# straight coast or 1 tile U-shaped gulfs
		if coastline == ['s', 'se', 'sw'] or coastline == ['s']:
			tile = GROUND.DEEP_WATER_SOUTH
		elif coastline == ['e', 'ne', 'se'] or coastline == ['e']:
			tile = GROUND.DEEP_WATER_EAST
		elif coastline == ['n', 'ne', 'nw'] or coastline == ['n']:
			tile = GROUND.DEEP_WATER_NORTH
		elif coastline == ['nw', 'sw', 'w'] or coastline == ['w']:
			tile = GROUND.DEEP_WATER_WEST
		# slight turn (looks best with straight coast)
		elif coastline == ['e', 'se'] or coastline == ['e', 'ne']:
			tile = GROUND.DEEP_WATER_EAST
		elif coastline == ['n', 'ne'] or coastline == ['n', 'nw']:
			tile = GROUND.DEEP_WATER_NORTH
		elif coastline == ['nw', 'w'] or coastline == ['sw', 'w']:
			tile = GROUND.DEEP_WATER_WEST
		elif coastline == ['s', 'sw'] or coastline == ['s', 'se']:
			tile = GROUND.DEEP_WATER_SOUTH
		# mostly shallow corner
		elif coastline == ['se']:
			tile = GROUND.DEEP_WATER_SOUTHWEST3
		elif coastline == ['ne']:
			tile = GROUND.DEEP_WATER_NORTHWEST3
		elif coastline == ['nw']:
			tile = GROUND.DEEP_WATER_NORTHEAST3
		elif coastline == ['sw']:
			tile = GROUND.DEEP_WATER_SOUTHEAST3
		# mostly deep corner
		elif 3 <= len(coastline) <= 5:
			coast_set = set(coastline)
			if 'e' in coast_set and 'se' in coast_set and 's' in coast_set:
				tile = GROUND.DEEP_WATER_SOUTHEAST1
			elif 's' in coast_set and 'sw' in coast_set and 'w' in coast_set:
				tile = GROUND.DEEP_WATER_SOUTHWEST1
			elif 'w' in coast_set and 'nw' in coast_set and 'n' in coast_set:
				tile = GROUND.DEEP_WATER_NORTHWEST1
			elif 'n' in coast_set and 'ne' in coast_set and 'e' in coast_set:
				tile = GROUND.DEEP_WATER_NORTHEAST1

		map_db("INSERT INTO ground VALUES(?, ?, ?)", x, y, tile)

	for x, y in map_dict.iterkeys():
		if map_dict[(x, y)] == groundTypes.coast:
			# add sand to shallow water tile
			coastline = []
			for dir in sorted(offset_coastline):
				if (x + offset_coastline[dir][1], y + offset_coastline[dir][0]) not in map_dict:
					coastline.append(dir)

			tile = GROUND.SHALLOW_WATER
			# straight coast or 1 tile U-shaped gulfs
			if coastline == ['s', 'se', 'sw'] or coastline == ['s']:
				tile = GROUND.COAST_SOUTH
			elif coastline == ['e', 'ne', 'se'] or coastline == ['e']:
				tile = GROUND.COAST_EAST
			elif coastline == ['n', 'ne', 'nw'] or coastline == ['n']:
				tile = GROUND.COAST_NORTH
			elif coastline == ['nw', 'sw', 'w'] or coastline == ['w']:
				tile = GROUND.COAST_WEST
			# slight turn (looks best with straight coast)
			elif coastline == ['e', 'se'] or coastline == ['e', 'ne']:
				tile = GROUND.COAST_EAST
			elif coastline == ['n', 'ne'] or coastline == ['n', 'nw']:
				tile = GROUND.COAST_NORTH
			elif coastline == ['nw', 'w'] or coastline == ['sw', 'w']:
				tile = GROUND.COAST_WEST
			elif coastline == ['s', 'sw'] or coastline == ['s', 'se']:
				tile = GROUND.COAST_SOUTH
			# sandy corner
			elif coastline == ['se']:
				tile = GROUND.COAST_SOUTHWEST3
			elif coastline == ['ne']:
				tile = GROUND.COAST_NORTHWEST3
			elif coastline == ['nw']:
				tile = GROUND.COAST_NORTHEAST3
			elif coastline == ['sw']:
				tile = GROUND.COAST_SOUTHEAST3
			# watery corner
			elif 3 <= len(coastline) <= 5:
				coast_set = set(coastline)
				if 'e' in coast_set and 'se' in coast_set and 's' in coast_set:
					tile = GROUND.COAST_SOUTHEAST1
				elif 's' in coast_set and 'sw' in coast_set and 'w' in coast_set:
					tile = GROUND.COAST_SOUTHWEST1
				elif 'w' in coast_set and 'nw' in coast_set and 'n' in coast_set:
					tile = GROUND.COAST_NORTHWEST1
				elif 'n' in coast_set and 'ne' in coast_set and 'e' in coast_set:
					tile = GROUND.COAST_NORTHEAST1

			map_db("INSERT INTO ground VALUES(?, ?, ?)", x, y, tile)
		else:
			# add grass to sand tile or just the ground
			coastline = []
			for dir in sorted(offset_coastline):
				if map_dict[(x + offset_coastline[dir][1], y + offset_coastline[dir][0])] == groundTypes.coast:
					coastline.append(dir)

			if coastline:
				# add grass to sand tile
				tile = GROUND.SAND
				# straight coast or 1 tile U-shaped gulfs
				if coastline == ['s', 'se', 'sw'] or coastline == ['s']:
					tile = GROUND.SAND_SOUTH
				elif coastline == ['e', 'ne', 'se'] or coastline == ['e']:
					tile = GROUND.SAND_EAST
				elif coastline == ['n', 'ne', 'nw'] or coastline == ['n']:
					tile = GROUND.SAND_NORTH
				elif coastline == ['nw', 'sw', 'w'] or coastline == ['w']:
					tile = GROUND.SAND_WEST
				# slight turn (looks best with straight coast)
				elif coastline == ['e', 'se'] or coastline == ['e', 'ne']:
					tile = GROUND.SAND_EAST
				elif coastline == ['n', 'ne'] or coastline == ['n', 'nw']:
					tile = GROUND.SAND_NORTH
				elif coastline == ['nw', 'w'] or coastline == ['sw', 'w']:
					tile = GROUND.SAND_WEST
				elif coastline == ['s', 'sw'] or coastline == ['s', 'se']:
					tile = GROUND.SAND_SOUTH
				# grassy corner
				elif coastline == ['se']:
					tile = GROUND.SAND_SOUTHWEST3
				elif coastline == ['ne']:
					tile = GROUND.SAND_NORTHWEST3
				elif coastline == ['nw']:
					tile = GROUND.SAND_NORTHEAST3
				elif coastline == ['sw']:
					tile = GROUND.SAND_SOUTHEAST3
				# sandy corner
				elif 3 <= len(coastline) <= 5:
					coast_set = set(coastline)
					if 'e' in coast_set and 'se' in coast_set and 's' in coast_set:
						tile = GROUND.SAND_SOUTHEAST1
					elif 's' in coast_set and 'sw' in coast_set and 'w' in coast_set:
						tile = GROUND.SAND_SOUTHWEST1
					elif 'w' in coast_set and 'nw' in coast_set and 'n' in coast_set:
						tile = GROUND.SAND_NORTHWEST1
					elif 'n' in coast_set and 'ne' in coast_set and 'e' in coast_set:
						tile = GROUND.SAND_NORTHEAST1

				map_db("INSERT INTO ground VALUES(?, ?, ?)", x, y, tile)
			else:
				# add grass tile
				map_db("INSERT INTO ground VALUES(?, ?, ?)", x, y, GROUND.DEFAULT_LAND)

	map_db("COMMIT")
	return map_db


def generate_map(seed = None) :
	"""Generates a whole map.
	@param seed: argument passed to random.seed
	@return filename to the sqlite db containing the new map"""
	rand = random.Random(seed)

	filename = tempfile.mkstemp()[1]
	shutil.copyfile(PATHS.SAVEGAME_TEMPLATE, filename)

	db = DbReader(filename)

	island_space = (35, 35)
	island_min_size = (25, 25)
	island_max_size = (28, 28)

	method = rand.randint(0, 1) # choose map creation method

	if method == 0:
		# generate up to 9 islands
		number_of_islands = 0
		for i in Rect.init_from_topleft_and_size(0, 0, 2, 2):
			if rand.randint(0, 2) != 0: # 2/3 chance for an island here
				number_of_islands = number_of_islands + 1
				x = int( i.x * island_space[0] * (rand.random()/6 + 0.90) )
				y = int( i.y * island_space[1] *  (rand.random()/6 + 0.90) )
				island_seed = rand.randint(-sys.maxint, sys.maxint)
				island_params = {'creation_method': 0, 'seed': island_seed, \
								 'width': rand.randint(island_min_size[0], island_max_size[0]), \
								 'height': rand.randint(island_min_size[1], island_max_size[1])}

				island_string = string.Template(_random_island_id_template).safe_substitute(island_params)

				db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", x, y, island_string)

		# if there is 1 or 0 islands created, it places 1 large island in the centre
		if number_of_islands == 0:
			x = 20
			y = 20
			island_seed = rand.randint(-sys.maxint, sys.maxint)
			island_params = {'creation_method': 1, 'seed': island_seed, \
							 'width': rand.randint(island_min_size[0] * 2, island_max_size[0] * 2), \
							 'height': rand.randint(island_min_size[1] * 2, island_max_size[1] * 2)}
			island_string = string.Template(_random_island_id_template).safe_substitute(island_params)

			db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", x, y, island_string)

		elif number_of_islands == 1:
			db("DELETE FROM island")

			x = 20
			y = 20
			island_seed = rand.randint(-sys.maxint, sys.maxint)
			island_params = {'creation_method': 1, 'seed': island_seed, \
							 'width': rand.randint(island_min_size[0] * 2, island_max_size[0] * 2), \
							 'height': rand.randint(island_min_size[1] * 2, island_max_size[1] * 2)}

			island_string = string.Template(_random_island_id_template).safe_substitute(island_params)

			db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", x, y, island_string)

	elif method == 1:
		# places 1 large island in the centre
		x = 20
		y = 20
		island_seed = rand.randint(-sys.maxint, sys.maxint)
		island_params = {'creation_method': 1, 'seed': island_seed, \
						 'width': rand.randint(island_min_size[0] * 2, island_max_size[0] * 2), \
						 'height': rand.randint(island_min_size[1] * 2, island_max_size[1] * 2)}
		island_string = string.Template(_random_island_id_template).safe_substitute(island_params)

		db("INSERT INTO island (x, y, file) VALUES(?, ?, ?)", x, y, island_string)

	return filename

