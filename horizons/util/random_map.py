# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

import hashlib
import random
import re
import string
import copy

from horizons.util.shapes import Circle, Point, Rect
from horizons.constants import GROUND

# this is how a random island id looks like (used for creation)
_random_island_id_template = "random:${creation_method}:${width}:${height}:${seed}:${island_x}:${island_y}"

# you can check for a random island id with this:
_random_island_id_regexp = r"^random:([0-9]+):([0-9]+):([0-9]+):([\-]?[0-9]+):([\-]?[0-9]+):([\-]?[0-9]+)$"


def create_random_island(map_db, island_id, id_string):
	"""Creates a random island as sqlite db.
	It is rather primitive; it places shapes on the dict.
	The coordinates of tiles will be 0 <= x < width and 0 <= y < height
	@param id_string: random island id string
	"""
	match_obj = re.match(_random_island_id_regexp, id_string)
	assert match_obj
	creation_method, width, height, seed, island_x, island_y = [long(i) for i in match_obj.groups()]
	assert creation_method == 2, 'The only supported island creation method is 2.'

	rand = random.Random(seed)
	map_set = set()

	# place this number of shapes
	for i in xrange(15 + width * height // 45):
		# place shape determined by shape_id on (x, y)
		add = True
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
			else:
				x = rand.randint(0, width)
				y = rand.randint(0, height)
			shape = Rect.init_from_topleft_and_size(x - 5, y - 5, rand.randint(2, 8), rand.randint(2, 8))
		else:
			# use a circle such that the radius is determined by shape_id
			radius = shape_id
			if not add and rand.randint(0, 6) < 5:
				x = rand.randint(-radius * 3 // 2, width + radius * 3 // 2)
				y = rand.randint(-radius * 3 // 2, height + radius * 3 // 2)
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
	map_db("BEGIN TRANSACTION")

	# set mountain tiles
	mountain_range = []
	neighbors = [(-1, 0), (0, -1), (0, 1), (1, 0)]
	all_neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]
	
	# checks for edge of map
	def dist_to_edge((x, y)):
		dist = 1
		real_dist = 1
		dist_found = False
		while not dist_found:
			# check tiles in diamond
			for dx in range(-dist, dist+1):
				absDx = abs(dx)
				dy = dist - absDx
				coords = (x+dx, y+dy)
				if coords not in map_set:
					real_dist = absDx+dy
					dist_found = True
				coords = (x+dx, y-dy)
				if coords not in map_set:
					real_dist = absDx+dy
					dist_found = True
			dist += 1
		return real_dist
	
	# checks for edge of map and mountain
	def dist_to_not_grass((x, y)):
		dist = 1
		real_dist = 1
		dist_found = False
		while not dist_found:
			# check tiles in diamond
			for dx in range(-dist, dist+1):
				absDx = abs(dx)
				dy = dist - absDx
				coords = (x+dx, y+dy)
				if coords not in map_set or coords in mountain_range:
					real_dist = absDx+dy
					dist_found = True
					break
				coords = (x+dx, y-dy)
				if coords not in map_set or coords in mountain_range:
					real_dist = absDx+dy
					dist_found = True
					break
			dist += 1
		return real_dist
	
	# find the tile with the largest distance to the edge of the map
	def largest_dist_to_edge(set):
		largest_dist = 0
		largest_dist_tile = (0, 0)
		for x, y in set:
			edge_dist = dist_to_edge((x, y))
			if edge_dist > largest_dist:
				largest_dist = edge_dist
				largest_dist_tile = (x, y)
		return largest_dist_tile
		
	# find the tile with the largest distance to the edge of the map or a mountain tile
	def largest_dist_to_not_grass(set):
		largest_dist = 0
		largest_dist_tile = (0, 0)
		for x, y in set:
			edge_dist = dist_to_not_grass((x, y))
			if edge_dist > largest_dist:
				largest_dist = edge_dist
				largest_dist_tile = (x, y)
		return largest_dist_tile
	
	# for a direction ('n') find the 2 adjacent directions ('nw', 'ne')
	def directions(centre_dir):
		new_dir = []
		new_dir.append(centre_dir)
		if centre_dir[0] == 0:
			new_dir.append((1, centre_dir[1]))
			new_dir.append((-1, centre_dir[1]))
		elif centre_dir[1] == 0:
			new_dir.append((centre_dir[0], 1))
			new_dir.append((centre_dir[0], -1))
		else:
			new_dir.append((0, centre_dir[1]))
			new_dir.append((centre_dir[0], 0))
		return new_dir
	
	mountain_ratio = 0.1
	min_dist = 6
	while True:
		# set initial mountain tile
		start_tile = largest_dist_to_not_grass(map_set)
		if dist_to_not_grass(start_tile) > min_dist:
			mountain_range.append(start_tile)
		else:
			break
	
		# grow mountain ranges
		for tile_dir in all_neighbors:
			previous_tile = mountain_range[0]
			# create list of possible movement directions
			dirs = directions(tile_dir)
			# initiate movement direction
			mountain_range.append((start_tile[0]+tile_dir[0], start_tile[1]+tile_dir[1]))
		
			while dist_to_edge(mountain_range[len(mountain_range)-1]) > min_dist and \
			 len(mountain_range) < (mountain_ratio*all_neighbors.index(tile_dir)*len(map_set))/8:
				positions = []
				if rand.randint(0, 1) == 0:
					direction = [tile_dir]
				else:
					direction = dirs
				for dx, dy in direction:
					positions.append((previous_tile[0] + dx, previous_tile[1] + dy))
				next_tile = largest_dist_to_edge(positions)
				mountain_range.append(next_tile)
				previous_tile = next_tile
	
	mountain_outline = []
	for x, y in mountain_range:
		for dx, dy in all_neighbors:
			coords = (x+dx, y+dy)
			if coords not in mountain_outline:
				mountain_outline.append(coords)
	
	# combine the central range with its outline
	mountain_tiles = list(set().union(*[mountain_range, mountain_outline]))
	
	# make some corrections to the mountain locations
	# by removing points that are missing certain neighbors
	consecutive_neighbor_corners = [
	[(-1, 0), (-1, 1), (0, 1)],
	[(0, 1), (1, 1), (1, 0)],
	[(1, 0), (1, -1), (0, -1)],
	[(0, -1), (-1, -1), (-1, 0)]
	]
	
	while True:
		still_corrections = False
		for x, y in mountain_tiles:
			tile_neighbors = False
			for neighbor_set in consecutive_neighbor_corners:
				consecutive_neighbors = True
				for dx, dy in neighbor_set:
					if (x+dx, y+dy) not in mountain_tiles:
						consecutive_neighbors = False
				if consecutive_neighbors:
					break
			if consecutive_neighbors:
				breaks = 0
				for a in range (0, 8):
					coord = (x+all_neighbors[a][0], y+all_neighbors[a][1])
					next_coord = (x+all_neighbors[(a+1)%8][0], y+all_neighbors[(a+1)%8][1])
					if coord in mountain_tiles and next_coord not in mountain_tiles:
						breaks += 1
					if coord not in mountain_tiles and next_coord in mountain_tiles:
						breaks += 1
				if breaks < 3:
					tile_neighbors = True
			if not tile_neighbors:
				still_corrections = True
				del mountain_tiles[mountain_tiles.index((x, y))]
				break
		if still_corrections == False:
			break
	
	# add grass tiles around mountain locations
	for x, y in map_set:
		if (x, y) not in mountain_tiles:
			map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)", island_id, island_x + x, island_y + y, *GROUND.DEFAULT_LAND)
			
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
	
	# get mountainsides
	def get_mountain_outline():
		"""
		@return: the points just inside the mountain as a dict
		"""
		result = set()
		for x, y in mountain_tiles:
			for dx, dy in all_neighbors:
				coords = (x + dx, y + dy)
				if coords not in mountain_tiles:
					result.add((x, y))
		return result
	
	# get mountain top
	def get_inner_mountain():
		result = set()
		mountain_edge = get_mountain_outline()
		for x, y in mountain_tiles:
			if (x, y) not in mountain_edge:
				result.add((x, y))
		return result
	
	# add mountain tiles to previously set locations
	mountain_edge = get_mountain_outline()
	inner_mountain = get_inner_mountain()
	for x, y in mountain_edge:
		filled = []
		for dir in sorted(all_moves):
			coords = (x + all_moves[dir][0], y + all_moves[dir][1])
			if coords not in mountain_tiles:
				filled.append(dir)
		
		tile = None
		mountain_set = set(filled)
		if len(filled) == 0:
			tile = GROUND.MOUNTAIN
		# straight
		elif 's' in mountain_set and 'w' not in mountain_set and 'nw' not in mountain_set and \
		 'n' not in mountain_set and 'ne' not in mountain_set and 'e' not in mountain_set:
			tile = GROUND.MOUNTAIN_SOUTH
		elif 'e' in mountain_set and 's' not in mountain_set and 'sw' not in mountain_set and \
		 'w' not in mountain_set and 'nw' not in mountain_set and 'n' not in mountain_set:
			tile = GROUND.MOUNTAIN_EAST
		elif 'n' in mountain_set and 'e' not in mountain_set and 'se' not in mountain_set and \
		 's' not in mountain_set and 'sw' not in mountain_set and 'w' not in mountain_set:
			tile = GROUND.MOUNTAIN_NORTH
		elif 'w' in mountain_set and 'n' not in mountain_set and 'ne' not in mountain_set and \
		 'e' not in mountain_set and 'se' not in mountain_set and 's' not in mountain_set:
			tile = GROUND.MOUNTAIN_WEST
		# inner corner
		elif filled == ['se']:
			tile = GROUND.MOUNTAIN_SOUTHEAST1
		elif filled == ['ne']:
			tile = GROUND.MOUNTAIN_NORTHEAST1
		elif filled == ['nw']:
			tile = GROUND.MOUNTAIN_NORTHWEST1
		elif filled == ['sw']:
			tile = GROUND.MOUNTAIN_SOUTHWEST1
		# outer corner
		elif 'e' in mountain_set and 'se' in mountain_set and 's' in mountain_set and \
		 'n' not in mountain_set and 'nw' not in mountain_set and 'w' not in mountain_set:
			tile = GROUND.MOUNTAIN_SOUTHEAST3
		elif 'n' in mountain_set and 'ne' in mountain_set and 'e' in mountain_set and \
		 'w' not in mountain_set and 'sw' not in mountain_set and 's' not in mountain_set:
			tile = GROUND.MOUNTAIN_NORTHEAST3
		elif 'w' in mountain_set and 'nw' in mountain_set and 'n' in mountain_set and \
		 's' not in mountain_set and 'se' not in mountain_set and 'e' not in mountain_set:
			tile = GROUND.MOUNTAIN_NORTHWEST3
		elif 's' in mountain_set and 'sw' in mountain_set and 'w' in mountain_set and \
		 'e' not in mountain_set and 'ne' not in mountain_set and 'n' not in mountain_set:
			tile = GROUND.MOUNTAIN_SOUTHWEST3
		else:
			print 'pew'
			print filled
			tile = GROUND.SAND

		assert tile
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)", island_id, island_x + x, island_y + y, *tile)
	map_set = map_set.union(mountain_edge)
	
	# add mountain tops
	for x, y in inner_mountain:
		filled = []
		for dir in sorted(all_moves):
			coords = (x + all_moves[dir][0], y + all_moves[dir][1])
			if coords in mountain_edge:
				filled.append(dir)
		
		tile = None
		mountain_set = set(filled)
		if len(filled) == 0:
			tile = GROUND.MOUNTAIN_TOP
		# mountain sides
		elif filled == ['s', 'se', 'sw'] or filled == ['s'] or filled == ['s', 'sw'] or filled == ['s', 'se']:
			tile = GROUND.MOUNTAIN_TOP_NORTH
		elif filled == ['e', 'ne', 'se'] or filled == ['e'] or filled == ['e', 'se'] or filled == ['e', 'ne']:
			tile = GROUND.MOUNTAIN_TOP_WEST
		elif filled == ['n', 'ne', 'nw'] or filled == ['n'] or filled == ['n', 'ne'] or filled == ['n', 'nw']:
			tile = GROUND.MOUNTAIN_TOP_SOUTH
		elif filled == ['nw', 'sw', 'w'] or filled == ['w'] or filled == ['nw', 'w'] or filled == ['sw', 'w']:
			tile = GROUND.MOUNTAIN_TOP_EAST
		
		# inner corner
		elif filled == ['se']:
			tile = GROUND.MOUNTAIN_TOP_NORTHWEST1
		elif filled == ['ne']:
			tile = GROUND.MOUNTAIN_TOP_SOUTHWEST1
		elif filled == ['nw']:
			tile = GROUND.MOUNTAIN_TOP_SOUTHEAST1
		elif filled == ['sw']:
			tile = GROUND.MOUNTAIN_TOP_NORTHEAST1
			
		# outer corner
		elif 'n' in mountain_set and 'e' in mountain_set and 's' not in mountain_set and 'w' not in mountain_set and 'sw' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_SOUTHEAST3
		elif 'e' in mountain_set and 's' in mountain_set and 'w' not in mountain_set and 'n' not in mountain_set and 'nw' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_NORTHEAST3
		elif 's' in mountain_set and 'w' in mountain_set and 'n' not in mountain_set and 'e' not in mountain_set and 'ne' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_NORTHWEST3
		elif 'w' in mountain_set and 'n' in mountain_set and 'e' not in mountain_set and 's' not in mountain_set and 'se' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_SOUTHWEST3
			
		# T into peak
		elif filled == ['ne', 'nw']:
			tile = GROUND.MOUNTAIN_TOP_PEAK_T_NORTH
		elif filled == ['nw', 'sw']:
			tile = GROUND.MOUNTAIN_TOP_PEAK_T_WEST
		elif filled == ['se', 'sw']:
			tile = GROUND.MOUNTAIN_TOP_PEAK_T_SOUTH
		elif filled == ['ne', 'se']:
			tile = GROUND.MOUNTAIN_TOP_PEAK_T_EAST
		
		# diagonal
		elif filled == ['ne', 'sw']:
			tile = GROUND.MOUNTAIN_TOP_NORTHEAST_SOUTHWEST
		elif filled == ['nw', 'se']:
			tile = GROUND.MOUNTAIN_TOP_NORTHWEST_SOUTHEAST
		
		# peak straights
		elif 'e' in mountain_set and 'w' in mountain_set and 'n' not in mountain_set and 's' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_STRAIGHT_EAST
		elif 'n' in mountain_set and 's' in mountain_set and 'e' not in mountain_set and 'w' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_STRAIGHT_NORTH
			
		# peak ends
		elif 'n' in mountain_set and 'e' in mountain_set and 's' in mountain_set and 'w' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_END_SOUTH
		elif 'e' in mountain_set and 's' in mountain_set and 'w' in mountain_set and 'n' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_END_WEST
		elif 's' in mountain_set and 'w' in mountain_set and 'n' in mountain_set and 'e' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_END_NORTH
		elif 'w' in mountain_set and 'n' in mountain_set and 'e' in mountain_set and 's' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_END_EAST
		
		# peak corners
		elif 'nw' in mountain_set and 'e' in mountain_set and 's' in mountain_set and 'n' not in mountain_set and 'w' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_CORNER_NORTH
		elif 'ne' in mountain_set and 's' in mountain_set and 'w' in mountain_set and 'e' not in mountain_set and 'n' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_CORNER_EAST
		elif 'se' in mountain_set and 'w' in mountain_set and 'n' in mountain_set and 's' not in mountain_set and 'e' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_CORNER_SOUTH
		elif 'sw' in mountain_set and 'n' in mountain_set and 'e' in mountain_set and 'w' not in mountain_set and 's' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_CORNER_WEST
			
		# L into peak (right)
		elif 'ne' in mountain_set and 'w' in mountain_set and 'n' not in mountain_set and 'e' not in mountain_set and 's' not in mountain_set and 'se' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_L_RIGHT_NORTH
		elif 'se' in mountain_set and 'n' in mountain_set and 'e' not in mountain_set and 's' not in mountain_set and 'w' not in mountain_set and 'sw' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_L_RIGHT_EAST
		elif 'sw' in mountain_set and 'e' in mountain_set and 's' not in mountain_set and 'w' not in mountain_set and 'n' not in mountain_set and 'nw' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_L_RIGHT_SOUTH
		elif 'nw' in mountain_set and 's' in mountain_set and 'w' not in mountain_set and 'n' not in mountain_set and 'e' not in mountain_set and 'ne' not in mountain_set:
			tile = GROUND.MOUNTAIN_TOP_PEAK_L_RIGHT_WEST
		
		# (left) and T_straight
		elif 'nw' in mountain_set and 'e' in mountain_set and 'n' not in mountain_set and 'w' not in mountain_set and 's' not in mountain_set:
			if 'sw' in mountain_set:
				tile = GROUND.MOUNTAIN_TOP_PEAK_T_STRAIGHT_NORTH
			else:
				tile = GROUND.MOUNTAIN_TOP_PEAK_L_LEFT_NORTH
		elif 'ne' in mountain_set and 's' in mountain_set and 'e' not in mountain_set and 'n' not in mountain_set and 'w' not in mountain_set:
			if 'nw' in mountain_set:
				tile = GROUND.MOUNTAIN_TOP_PEAK_T_STRAIGHT_EAST
			else:
				tile = GROUND.MOUNTAIN_TOP_PEAK_L_LEFT_EAST
		elif 'se' in mountain_set and 'w' in mountain_set and 's' not in mountain_set and 'e' not in mountain_set and 'n' not in mountain_set:
			if 'ne' in mountain_set:
				tile = GROUND.MOUNTAIN_TOP_PEAK_T_STRAIGHT_SOUTH
			else:
				tile = GROUND.MOUNTAIN_TOP_PEAK_L_LEFT_SOUTH
		elif 'sw' in mountain_set and 'n' in mountain_set and 'w' not in mountain_set and 's' not in mountain_set and 'e' not in mountain_set:
			if 'se' in mountain_set:
				tile = GROUND.MOUNTAIN_TOP_PEAK_T_STRAIGHT_WEST
			else:
				tile = GROUND.MOUNTAIN_TOP_PEAK_L_LEFT_WEST
				
		# single peak
		elif 'n' in mountain_set and 'e' in mountain_set and 's' in mountain_set and 'w' in mountain_set:
				tile = GROUND.MOUNTAIN_TOP_PEAK
		
		# into 2 peaks
		elif filled == ['ne', 'se', 'sw']:
			tile = GROUND.MOUNTAIN_TOP_NORTHEAST_SOUTHEAST_SOUTHWEST
		elif filled == ['ne', 'nw', 'se']:
			tile = GROUND.MOUNTAIN_TOP_NORTHWEST_NORTHEAST_SOUTHEAST
		elif filled == ['ne', 'nw', 'sw']:
			tile = GROUND.MOUNTAIN_TOP_SOUTHWEST_NORTHWEST_NORTHEAST
		elif filled == ['nw', 'se', 'sw']:
			tile = GROUND.MOUNTAIN_TOP_SOUTHEAST_SOUTHWEST_NORTHWEST
		
		elif filled == ['ne', 'nw', 'se', 'sw']:
			tile = GROUND.MOUNTAIN_TOP_PEAK_ALL
		
		
		else:
			print 'dewd'
			print filled
			tile = GROUND.SAND
				
		
		assert tile
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)", island_id, island_x + x, island_y + y, *tile)
	map_set = map_set.union(inner_mountain)
				

	def fill_tiny_spaces(tile):
		"""Fills 1 tile gulfs and straits with the specified tile
		@param tile: ground tile to fill with
		"""

		all_neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
		neighbors = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		corners = [(-1, -1), (-1, 1)]
		knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
		bad_configs = set([0, 1 << 0, 1 << 1, 1 << 2, 1 << 3, (1 << 0) | (1 << 3), (1 << 1) | (1 << 2)])

		edge_set = copy.copy(map_set)
		reduce_edge_set = True

		while True:
			to_fill = set()
			to_ignore = set()
			
			for x, y in edge_set:
				# ignore the tiles with no empty neighbors
				if reduce_edge_set:
					is_edge = False
					for x_offset, y_offset in all_neighbors:
						if (x + x_offset, y + y_offset) not in map_set:
							is_edge = True
							break
					if not is_edge:
						to_ignore.add((x, y))
						continue

				for x_offset, y_offset in neighbors:
					x2 = x + x_offset
					y2 = y + y_offset
					if (x2, y2) in map_set:
						continue
					# (x2, y2) is now a point just off the island

					neighbors_dirs = 0
					for i in xrange(len(neighbors)):
						x3 = x2 + neighbors[i][0]
						y3 = y2 + neighbors[i][1]
						if (x3, y3) not in map_set:
							neighbors_dirs |= (1 << i)
					if neighbors_dirs in bad_configs:
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
						y2 = y + y_offset // 2
						if (x2, y2) in map_set or (x, y2) in map_set:
							continue
					else:
						x2 = x + x_offset // 2
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
					map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)", island_id, island_x + x, island_y + y, *tile)

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
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)", island_id, island_x + x, island_y + y, *tile)
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
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)", island_id, island_x + x, island_y + y, *tile)
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
		map_db("INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)", island_id, island_x + x, island_y + y, *tile)

	map_db("COMMIT")

def _simplify_seed(seed):
	"""
	Return the simplified seed value. The goal of this is to make it easier for users to convey the seeds orally.

	This function also makes sure its return value fits into a 32bit integer. That is
	necessary because otherwise the hash of the value could be different between
	32 and 64 bit python interpreters. That would cause a map with seed X to be different
	depending on the platform which we don't want to happen.
	"""

	seed = str(seed).lower().strip()
	h = hashlib.md5(seed)
	h.update(seed)
	return int('0x' + h.hexdigest(), 16) % 1000000007

def generate_random_map(seed, map_size, water_percent, max_island_size,
                        preferred_island_size, island_size_deviation):
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
	min_island_separation = 3 + map_size // 100 # minimum distance between two islands
	max_island_side_coefficient = 4 # maximum value of island's max(side length) / min(side length)

	islands = []
	estimated_land = 0
	max_land_amount = map_size * map_size * (100 - water_percent) // 100

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
				if existing_island.distance(rect) < min_island_separation:
					blocked = True
					break
			if not blocked:
				islands.append(rect)
				estimated_land += size
				trial_number = 0
				break

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

	island_strings = []
	for rect in islands:
		# The bounds must be platform independent to make sure the same maps are generated on all platforms.
		island_seed = rand.randint(-2147483648, 2147483647)
		island_params = {'creation_method': 2, 'seed': island_seed, 'width': rect.width,
						 'height': rect.height, 'island_x': rect.left, 'island_y': rect.top}
		island_string = string.Template(_random_island_id_template).safe_substitute(island_params)
		island_strings.append(island_string)
	return island_strings

def generate_random_seed(seed):
	rand = random.Random(seed)
	if rand.randint(0, 1) == 0:
		# generate a random string of 1-5 letters a-z with a dash if there are 4 or more letters
		seq = ''
		for i in xrange(rand.randint(1, 5)):
			seq += chr(97 + rand.randint(0, 25))
		if len(seq) > 3:
			split = rand.randint(2, len(seq) - 2)
			seq = seq[:split] + '-' + seq[split:]
		return unicode(seq)
	else:
		# generate a numeric seed
		fields = rand.randint(1, 3)
		if fields == 1:
			# generate a five digit integer
			return unicode(rand.randint(10000, 99999))
		else:
			# generate a sequence of 2 or 3 dash separated fields of integers 10-9999
			parts = []
			for i in xrange(fields):
				power = rand.randint(1, 3)
				parts.append(str(rand.randint(10 ** power, 10 ** (power + 1) - 1)))
			return unicode('-'.join(parts))

def generate_map_from_seed(seed):
	"""
	Generates a random map with the given seed and default parameters.

	@param seed: random number generator seed
	@return: filename of the SQLite database containing the map
	"""

	return generate_random_map(seed, 150, 50, 70, 70, 30)

def generate_huge_map_from_seed(seed):
	"""Same as generate_map_from_seed, but making it as big as it is still reasonable"""
	return generate_random_map(seed, 250, 20, 70, 70, 5)
