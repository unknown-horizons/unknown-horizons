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


from game.util import Rect, Point, WorldObject
from game.world.building.building import Building
import game.main
import weakref
import copy
import sys

# for speed testing:
#import time

class PathBlockedError(Exception):
	pass

class Movement:
	"""Saves walkable tiles according to unit in a seperate namespace
	SOLDIER_MOVEMENT: move directly on any walkable tile
	                  (except water, buildings, natural obstacles such as mountains)
	STORAGE_COLLECTOR_MOVEMENT: move on roads
	COLLECTOR_MOVEMENT: move within the radius of a building
	SHIP_MOVEMENT: move on water
	"""
	(SOLDIER_MOVEMENT, STORAGE_COLLECTOR_MOVEMENT, \
	 SHIP_MOVEMENT, COLLECTOR_MOVEMENT) = xrange(0,4)

def check_path(path, blocked_coords):
	""" debug function to check if a path is valid """
	i = iter(path)
	prev = i.next()

	err = False
	while True:
		try: cur = i.next()
		except StopIteration: break

		if cur in blocked_coords:
			#print 'PATH ERROR: node', cur, ' is blocked'
			err = True

		dist = Point(cur[0], cur[1]).distance(Point(prev[0], prev[1]))

		# check if it's a horizontal or vertical or diagonal movement
		# (everything else is an error)
		if dist != 1 and int((dist)*100) != 141:
			err = True
			#print 'PATH ERROR FROM', prev, 'TO', cur,' DIST: ', dist
		prev = cur

	if err:
		assert False, 'Encountered errors when testing pathfinding'
	return True


class FindPath(object):
	""" Finds best path from source to destination via a*-algo
	"best path" means path with shortest travel time, which
	is not necessarily the shortest path (cause roads have different speeds)
	"""

	def __call__(self, source, destination, path_nodes, blocked_coords = [], diagonal = False):
		"""
		@param source: Rect, Point or Building
		@param destination: Rect, Point or Building
		@param path_nodes: dict { (x,y) = speed_on_coords }  or list [(x,y), ..]
		@param blocked_coords: temporarily blocked coords (e.g. by a unit) as list or dict of
		@param diagonal: wether the unit is able to move diagonally
		@return: list of coords as tuples that are part of the best path
		         (from first coord after source to first coord in destination)
						 or None if no path is found
		"""
		# assurce correct call
		assert(isinstance(source, (Rect, Point, Building)))
		assert(isinstance(destination, (Rect, Point, Building)))
		assert(isinstance(path_nodes, (dict, list)))
		assert(isinstance(blocked_coords, (dict, list)))
		assert(isinstance(diagonal, (bool)))

		# save args
		self.source = source
		self.destination = destination
		self.path_nodes = path_nodes
		self.blocked_coords = blocked_coords
		self.diagonal = diagonal

		if game.main.debug:
			print 'SEARCHING path from',source,'to',destination,'. blocked: ',blocked_coords

		# prepare args
		if not self.setup():
			return None

		# execute algorithm on the args
		if not __debug__:
			return self.execute()
		else:
			p = self.execute()
			#print 'FOUND PATH', p
			return p

	def setup(self):
		"""Sets up variables for execution of algorithm
		@return: bool, wether setup was successful"""
		# support for building
		if isinstance(self.source, Building):
			self.source = self.source.position
		if isinstance(self.destination, Building):
			self.destination = self.destination.position

		if self.destination in self.blocked_coords:
			return False

		if isinstance(self.path_nodes, list):
			self.path_nodes = dict.fromkeys(self.path_nodes, 1.0)

		if isinstance(self.blocked_coords, dict):
			self.blocked_coords = self.blocked_coords.keys()

		return True

	def execute(self):
		"""Executes algorithm"""
		# nodes are the keys of the following dicts (x,y)
		# the val of the keys are: [previous node, distance to this node from source,
		# distance to destination, sum of the last two elements]

		# values of distance is usually measured in speed
		# since you can't calculate the speed to the destination,
		# these distances are measured in space
		# this might become a problem, but this can just be fixed when
		# the values of speed or slowness and such are defined

		# nodes that weren't processed but will be processed:
		to_check = {}
		# nodes that have been processed:
		checked = {}

		source_coords = self.source.get_coordinates()
		for c in source_coords:
			source_to_dest_dist = Point(*c).distance(self.destination)
			to_check[c] = [None, 0, source_to_dest_dist, source_to_dest_dist]

		# if one of the dest_coords has been processed
		# (i.e. is in checked), a good path is found
		dest_coords = self.destination.get_coordinates()

		while to_check:

			min = sys.maxint
			cur_node_coords = None
			cur_node_data = None

			# find next node to check, which is the one with best rating
			for (node_coords, node_data) in to_check.items():
				if node_data[3] < min:
					min = node_data[3]
					cur_node_coords = node_coords
					cur_node_data = node_data

			# shortcuts:
			x = cur_node_coords[0]
			y = cur_node_coords[1]

			# find possible neighbors
			if self.diagonal:
				# all relevant ajacent neighbors
				neighbors = [ i for i in [(xx,yy) for xx in xrange(x-1, x+2) for yy in xrange(y-1, y+2)] if \
											(i in self.path_nodes or \
											 i in source_coords or \
											 i in dest_coords) and\
											i not in checked and \
											i != (x,y) and \
											i not in self.blocked_coords ]
			else:
				# all relevant vertical and horizontal neighbors
				neighbors = [ i for i in [(x-1,y), (x+1,y), (x,y-1), (x,y+1) ] if \
											(i in self.path_nodes  or \
											 i in source_coords or \
											 i in dest_coords ) and \
											i not in checked and \
											i not in self.blocked_coords ]

			for neighbor_node in neighbors:

				if not neighbor_node in to_check:
					# add neighbor to list of reachable nodes to check

					# save previous node, calc distance to neighbor_node
					# and estimate from neighbor_node to destination
					to_check[neighbor_node] = [cur_node_coords, \
																		 cur_node_data[1] + \
																		 self.path_nodes.get(cur_node_coords, 0), \
																		 self.destination.distance(neighbor_node) ]
					# append sum of last to values  (i.e. complete path duration estimation) as cache
					to_check[neighbor_node].append( \
						to_check[(neighbor_node)][1] + to_check[(neighbor_node)][2])

				else:
					# neighbor has been processed,
					# check if current node provides a better path to this neighbor

					distance_to_neighbor = cur_node_data[1]+self.path_nodes.get(cur_node_coords, 0)

					neighbor = to_check[neighbor_node]

					if neighbor[1] > distance_to_neighbor:
						# found better path to neighbor, update values
						neighbor[0] = cur_node_coords
						neighbor[1] = distance_to_neighbor
						neighbor[3] = distance_to_neighbor + neighbor[2]

			# done processing cur_node
			checked[cur_node_coords] = cur_node_data
			del to_check[cur_node_coords]

			# check if cur_node is at the destination
			if cur_node_coords in dest_coords:
				# we're done.
				# insert steps of past to a list and return it
				path = [ cur_node_coords ]
				previous_node = cur_node_data[0]
				while previous_node is not None:
					path.insert(0, previous_node)
					previous_node = checked[previous_node][0]

				if __debug__:
					check_path(path, self.blocked_coords)

				return path

		else:
			return None


class Pather(object):
	"""Interface for pathfinding for use by Unit.
	"""
	def __init__(self, unit):
		self.move_diagonal = False
		self.blocked_coords = []
		if unit.__class__.movement == Movement.STORAGE_COLLECTOR_MOVEMENT:
			island = game.main.session.world.get_island(unit.position.x, unit.position.y)
			self.path_nodes = island.path_nodes
		elif unit.__class__.movement == Movement.COLLECTOR_MOVEMENT:
			self.move_diagonal = True
		elif unit.__class__.movement == Movement.SHIP_MOVEMENT:
			self.move_diagonal = True
			self.path_nodes = game.main.session.world.water
			self.blocked_coords = game.main.session.world.ship_map
		elif unit.__class__.movement == Movement.SOLDIER_MOVEMENT:
			# TODO
			assert False, 'Pathfinding for soldiers isn\'t implemented yet'
		else:
			assert False, 'Invalid way of movement'

		self.unit = weakref.ref(unit)

		self.destination_in_building = False
		self.source_in_building = False

		self.path = None
		self.cur = None

	def calc_path(self, destination, destination_in_building = False, check_only = False):
		"""Calculates a path to destination
		@param destination: a destination supported by pathfinding
		@param destination_in_building: bool, wether destination is in a building.
		                                this makes the unit "enter the building"
		@param check_only: if True the path isn't saved
		@return: False if movement is impossible, else True"""

		# workaround, this can't be initalized at construction time
		if self.unit().__class__.movement == Movement.COLLECTOR_MOVEMENT:
			self.path_nodes = self.unit().home_building().radius_coords

		if not check_only:
			self.source_in_building = False
		source = self.unit().position
		if self.unit().is_moving() and self.path is not None:
			source = Point(*self.path[self.cur])
		else:
			island = game.main.session.world.get_island(self.unit().position.x, self.unit().position.y)
			if island is not None:
				building = island.get_building(self.unit().position)
				if building is not None:
					source = building
					if not check_only:
						self.source_in_building = True

		path = FindPath()(source, destination, self.path_nodes, self.blocked_coords, self.move_diagonal)

		if path is None:
			return False

		if not check_only:
			self.path = path
			if self.unit().is_moving():
				self.cur = 0
			else:
				self.cur = -1
			self.destination_in_building = destination_in_building

		return True

	def revert_path(self, destination_in_building):
		"""Moves back to the source of last movement, using same path"""
		self.cur = -1
		self.destination_in_building = destination_in_building
		self.path.reverse()

	def get_next_step(self):
		"""Returns the next step in the current movement
		@return: Point"""
		self.cur += 1
		if self.path is None or self.cur == len(self.path):
			self.cur = None
			return None

		path_blocked_by_unit = False

		if self.unit().__class__.movement == Movement.SHIP_MOVEMENT:
			# for ship: check if another ship is blocking the way
			path_blocked_by_unit = self.path[self.cur] in game.main.session.world.ship_map and \
														 game.main.session.world.ship_map[self.path[self.cur]]() is not self

		if self.path[self.cur] in self.blocked_coords or path_blocked_by_unit:
			# path is suddenly blocked, find another path
			self.cur -= 1 # reset, since move is not possible
			if not self.calc_path(Point(*self.path[-1]), self.destination_in_building):
				raise PathBlockedError

		if self.destination_in_building and self.cur == len(self.path)-1:
			self.destination_in_building = False
			self.unit().hide()
		elif self.source_in_building and self.cur == 2:
			self.source_in_building = False
			self.unit().show()

		return Point(*self.path[self.cur])

	def get_move_target(self):
		"""Returns the point where the path leads
		@return: Point or None if no path has been calculated"""
		return None if self.path is None else Point(*self.path[-1])

	def end_move(self):
		"""Pretends that the path is finished in order to make the unit stop"""
		del self.path[self.cur+1:]

	def save(self, db, unitid):
		if self.path is not None:
			for step in xrange(len(self.path)):
				db("INSERT INTO unit_path(`unit`, `index`, `x`, `y`) VALUES(?, ?, ?, ?)", \
					 unitid, step, self.path[step][0], self.path[step][1])

	def load(self, db, worldid):
		"""
		@return: Bool, wether a path was loaded
		"""
		path_steps = db("SELECT x, y FROM unit_path WHERE unit = ? ORDER BY `index`", worldid)
		if len(path_steps) == 0:
			return False
		else:
			self.path = []
			for step in path_steps:
				self.path.append(step) # the sql statement orders the steps
			self.cur = self.path.index(self.unit().position.get_coordinates()[0])
			return True
