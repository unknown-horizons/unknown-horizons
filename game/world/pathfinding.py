# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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


from game.util import Rect, Point
from game.world.building.building import Building
import game.main
import weakref
import exceptions

# for speed testing:
import time

class PathBlockedError(exceptions.Exception):
	pass

class Movement:
	"""Saves walkable tiles according to unit in a seperate namespace
	SOLDIER_MOVEMENT: move directly on any walkable tile (except water, buildings, natural obstacles such as mountains
	STORAGE_CARRIAGE_MOVEMENT: move on roads
	CARRIAGE_MOVEMENT: move within the radius of a building
	SHIP_MOVEMENT: move on water
	"""
	(SOLDIER_MOVEMENT, STORAGE_CARRIAGE_MOVEMENT, SHIP_MOVEMENT, CARRIAGE_MOVEMENT) = xrange(0,4)

def check_path(path):
	""" debug function to check if a path is valid """
	i = iter(path)
	prev = i.next()

	err = False
	while True:
		try: cur = i.next()
		except StopIteration: break

		dist = Point(cur[0], cur[1]).distance(Point(prev[0], prev[1]))

		# check if it's a horizontal or vertical or diagonal movement
		# (all else is an error)
		if dist != 1 and int((dist)*100) != 141:
			err = True
			print 'PATH ERROR FROM', prev, 'TO', cur,' DIST: ', dist
		prev = cur

	if err:
		assert False, 'Encountered errors when testing pathfinding'
	return True

def findPath(source, destination, path_nodes, blocked_coords = [], diagonal = False):
	""" Finds best path from source to destination via a*-algo
	"best path" means path with shortest travel time, which
	is not necessarily the shortest path (cause roads have different speeds)
	@param source: Rect, Point or Building
	@param destination: Rect, Point or Building
	@param path_nodes: dict { (x,y) = speed_on_coords }  or list [(x,y), ..]
	@param blocked_coords: temporarily blocked coords (e.g. by a unit)
	@param diagonal: wether the unit is able to move diagonally
	@return: list of coords that are part of the best path (from first coord after source to last coord before destination) or None if no path is found
	"""
	#t0 = time.time()

	# assurce correct call
	assert(isinstance(source, (Rect, Point, Building)))
	assert(isinstance(destination, (Rect, Point, Building)))
	assert(isinstance(path_nodes, (dict, list)))
	assert(isinstance(blocked_coords, list))
	assert(isinstance(diagonal, (bool)))

	# support for building
	if isinstance(source, Building):
		source = source.position
	if isinstance(destination, Building):
		destination = destination.position

	if destination in blocked_coords:
		return None

	# if path_nodes is a list, turn it into a dict
	if isinstance(path_nodes, list):
		path_nodes = dict.fromkeys(path_nodes, 1.0)

	# nodes are the keys of the following dicts (x,y)
	# the val of the keys are: [previous node, distance to this node from source, distance to destination, sum of the last two elements]

	# values of distance is usually measured in speed
	# since you can't calculate the speed to the destination,
	# these distances are measured in space
	# this might become a problem, but i (totycro) won't fix it, until
	# the values of speed or slowness and such is defined

	# nodes that weren't processed but will be processed:
	to_check = {}
	# nodes that have been processed:
	checked = {}

	source_coords = source.get_coordinates()
	for c in source_coords:
		source_to_dest_dist = Point(c).distance(destination)
		to_check[c] = [None, 0, source_to_dest_dist, source_to_dest_dist]
		path_nodes[c] = 0

	# if one of the dest_coords is in checked, a good path is found
	dest_coords = destination.get_coordinates()

	# make source and target walkable
	for c in dest_coords:
		if not c in path_nodes:
			path_nodes[c] = 0

	while to_check:

		min = 99999
		cur_node_coords = None
		cur_node_data = None

		# find next node to check, which is the one with best rating

		for (node_coords, node_data) in to_check.items():
			if node_data[3] < min:
				min = node_data[3]
				cur_node_coords = node_coords
				cur_node_data = node_data

		#print 'NEXT_NODE', cur_node_coords, ":", cur_node_data

		# shortcuts:
		x = cur_node_coords[0]
		y = cur_node_coords[1]

		if diagonal:
			neighbors = [ (xx,yy) for xx in xrange(x-1, x+2) for yy in xrange(y-1, y+2) if (xx,yy) in path_nodes and not (xx,yy) in checked and (xx,yy) != (x,y) and (xx,yy) not in blocked_coords ]
		else:
			neighbors = [ i for i in [(x-1,y), (x+1,y), (x,y-1), (x,y+1) ] if i in path_nodes and not i in checked and i not in blocked_coords ]

		for neighbor_node in neighbors:
			#print 'NEW NODE', neighbor_node

			if not neighbor_node in to_check:
				# save previous, calc distance to neighbor_node and from neighbor_node to destination
				to_check[neighbor_node] = [cur_node_coords, cur_node_data[1]+path_nodes[cur_node_coords], destination.distance(neighbor_node) ]
				to_check[neighbor_node].append(to_check[(neighbor_node)][1] + to_check[(neighbor_node)][2])
				#print 'NEW',neighbor_node, ':', to_check[neighbor_node]
			else:
				distance_to_neighbor = cur_node_data[1]+path_nodes[cur_node_coords]

				# shortcut:
				neighbor = to_check[neighbor_node]

				# if cur_node provides a better path to neighbor_node, use it
				if neighbor[1] > distance_to_neighbor:
					neighbor[0] = cur_node_coords
					neighbor[1] = distance_to_neighbor
					neighbor[3] = distance_to_neighbor + neighbor[2]
					#print 'OLD',neighbor_node,':', to_check[neighbor_node]

		checked[cur_node_coords] = cur_node_data
		del to_check[cur_node_coords]

		if cur_node_coords in dest_coords:
			# found best path
			path = [ cur_node_coords ]
			previous_node = cur_node_data[0]
			while previous_node is not None:
				# maybe always append here and call list.reverse afterwards (depends on speed test results)
				path.insert(0, previous_node)
				previous_node = checked[previous_node][0]

			#t1 = time.time()
			#print 'PATH FINDING TIME', t1-t0
			print 'PATH FROM',source,'TO', destination,':', path
			#if len(path_nodes) < 20:
			#	print 'PATH NODES', path_nodes

			if __debug__:
				check_path(path)

			return path

	else:
		#t1 = time.time()
		#print 'PATH FINDING TIME', t1-t0
		print '_NO_ PATH FROM',source,'TO', destination
		#if len(path_nodes) < 20:
			#	print 'PATH NODES', path_nodes
		#sys.stdout = real_stdout
		return None

class Pather(object):
	"""Interface for pathfinding. To be inherited by Unit"""
	def __init__(self, unit):
		self.move_diagonal = False
		self.blocked_coords = []
		if unit.__class__.movement == Movement.STORAGE_CARRIAGE_MOVEMENT:
			island = game.main.session.world.get_island(unit.position.x, unit.position.y)
			self.path_nodes = island.path_nodes
		elif unit.__class__.movement == Movement.CARRIAGE_MOVEMENT:
			self.move_diagonal = True
		elif unit.__class__.movement == Movement.SHIP_MOVEMENT:
			self.move_diagonal = True
			self.path_nodes = game.main.session.world.water
			self.blocked_coords = game.main.session.world.ship_map
		elif unit.__class__.movement == Movement.SOLDIER_MOVEMENT:
			# TODO
			pass
		else:
			assert False, 'Invalid way of movement'

		self.unit = weakref.ref(unit)

		self.cur = None

	def calc_path(self, destination, destination_in_building = False, check_only = False):
		"""Calculates a path to destination
		@param destination: a destination supported by find_path
		@param destination_in_building: bool, wether destination is in a building. this makes the unit
		@param check_only: if True the path isn't saved,
		@return: False if movement is impossible, else True"""

		# this can't be initalized at construction time
		if self.unit().__class__.movement == Movement.CARRIAGE_MOVEMENT:
			self.path_nodes = self.unit().home_building().radius_coords

		if not check_only:
			self.source_in_building = False
		source = self.unit().position
		if self.unit().is_moving():
			source = Point(self.path[self.cur])
		else:
			island = game.main.session.world.get_island(self.unit().position.x, self.unit().position.y)
			if island is not None:
				building = island.get_building(self.unit().position.x, self.unit().position.y)
				if building is not None:
					print 'SRC IN BUILDING:', building.position
					source = building
					if not check_only:
						self.source_in_building = True

		blocked_coords = self.blocked_coords if isinstance(self.blocked_coords, list) else self.blocked_coords.keys()
		path = findPath(source, destination, self.path_nodes, blocked_coords, self.move_diagonal)
		if not check_only:
			self.path = path
			if self.unit().is_moving():
				self.cur = 0
			else:
				self.cur = -1
			self.destination_in_building = destination_in_building

		if path == None:
			return False
		else:
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
		if self.cur == len(self.path):
			self.cur = None
			return None

		if self.path[self.cur] in self.blocked_coords:
			# path is suddenly blocked, find another path
			blocked_coords = self.blocked_coords if isinstance(self.blocked_coords, list) else dict.fromkeys(self.blocked_coords, 1.0)
			self.path = findPath(self.path[self.cur-1], self.path[-1], self.path_nodes, blocked_coords, self.move_diagonal)
			if self.path is None:
				raise PathBlockedError
			self.cur = 1

		if self.destination_in_building and self.cur == len(self.path)-1:
			self.destination_in_building = False
			self.unit().hide()
		elif self.source_in_building and self.cur == 2:
			self.source_in_building = False
			print 'SHOW AT', self.path[self.cur]
			self.unit().show()

		return Point(self.path[self.cur])


