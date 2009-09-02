# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import sys
import logging

from horizons.util import Rect, Point
from horizons.world.building.building import BasicBuilding

from horizons.world.pathfinding import PathBlockedError

"""
This file contains only the pathfinding algorithm. It is implemented in a callable class
called FindPath. You should never ever use this class directly, just through the Pather
interface.
"""

class FindPath(object):
	""" Finds best path from source to destination via a*-algo
	"best path" means path with shortest travel time, which
	is not necessarily the shortest path (cause roads have different speeds)
	"""
	log = logging.getLogger("world.pathfinding")

	def __call__(self, source, destination, path_nodes, blocked_coords = list(), \
							 diagonal = False, make_target_walkable = True):
		"""
		@param source: Rect, Point or BasicBuilding
		@param destination: Rect, Point or BasicBuilding
		@param path_nodes: dict { (x, y) = speed_on_coords }  or list [(x, y), ..]
		@param blocked_coords: temporarily blocked coords (e.g. by a unit) as list or dict of
		@param diagonal: whether the unit is able to move diagonally
		@param make_target_walkable: whether we force the tiles of the target to be walkable,
		       even if they actually aren't (used e.g. when walking to a building)
		@return: list of coords as tuples that are part of the best path
		         (from first coord after source to first coord in destination)
						 or None if no path is found
		"""
		# assure correct call
		assert(isinstance(source, (Rect, Point, BasicBuilding)))
		assert(isinstance(destination, (Rect, Point, BasicBuilding)))
		assert(isinstance(path_nodes, (dict, list)))
		assert(isinstance(blocked_coords, (dict, list)))

		# save args
		self.source = source
		self.destination = destination
		self.path_nodes = path_nodes
		self.blocked_coords = blocked_coords
		self.diagonal = diagonal
		self.make_target_walkable = make_target_walkable

		#self.log.debug('searching path from %s to %s. blocked: %s', \
		#							 source, destination, blocked_coords)

		# prepare args
		if not self.setup():
			return None

		# execute algorithm on the args
		path = self.execute()
		self.log.debug('found path: %s', path)
		return path

	def setup(self):
		"""Sets up variables for execution of algorithm
		@return: bool, whether setup was successful"""
		# support for building
		if isinstance(self.source, BasicBuilding):
			self.source = self.source.position
		if isinstance(self.destination, BasicBuilding):
			self.destination = self.destination.position

		if isinstance(self.path_nodes, list):
			self.path_nodes = dict.fromkeys(self.path_nodes, 1.0)

		if isinstance(self.blocked_coords, dict):
			self.blocked_coords = self.blocked_coords.keys()

		# check if target is blocked
		target_is_blocked = True
		for coord in self.destination:
			if not coord in self.blocked_coords:
				target_is_blocked = False
		if target_is_blocked:
			#self.log.debug("FindPath: target is blocked")
			return False

		# check if target is walkable
		if not self.make_target_walkable:
			target_is_walkable = False
			for coord in self.destination:
				if coord.to_tuple() in self.path_nodes:
					target_is_walkable = True
					break
			if not target_is_walkable:
				#self.log.debug("FindPath: target is not walkable")
				return False

		return True

	def execute(self):
		"""Executes algorithm"""
		# nodes are the keys of the following dicts (x, y)
		# the val of the keys are: [previous node, distance to this node from source,
		# distance to destination, sum of the last two elements]
		# we use this data structure out of speed consideration,
		# using a class would admittedly be more readable

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

		# loop until we have no more nodes to check
		while to_check:

			minimum = sys.maxint
			cur_node_coords = None
			cur_node_data = None

			# find next node to check, which is the one with best rating
			# optimization note: this is faster than min(to_check, key=lambda k : to_check[k][3])
			# optimization note2: the values could be kept in a dict, or a structure
			#					that can easily be sorted/minimumed by a value
			for (node_coords, node_data) in to_check.iteritems():
				if node_data[3] < minimum:
					minimum = node_data[3]
					cur_node_coords = node_coords
					cur_node_data = node_data

			# shortcuts:
			x = cur_node_coords[0]
			y = cur_node_coords[1]

			# find possible neighbors
			if self.diagonal:
				# all relevant adjacent neighbors
				neighbors = [ i for i in [(xx, yy) for xx in xrange(x-1, x+2) for yy in xrange(y-1, y+2)] if \
											(i in self.path_nodes or \
											 i in source_coords or \
											 i in dest_coords) and\
											i not in checked and \
											i != (x, y) and \
											i not in self.blocked_coords ]
			else:
				# all relevant vertical and horizontal neighbors
				neighbors = [ i for i in [(x-1, y), (x+1, y), (x, y-1), (x, y+1) ] if \
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
				# insert steps of path to a list and return it
				path = [ cur_node_coords ]
				previous_node = cur_node_data[0]
				while previous_node is not None:
					path.insert(0, previous_node)
					previous_node = checked[previous_node][0]

				return path

		else:
			return None



"""
def check_path(path, blocked_coords):
	"" debug function to check if a path is valid ""
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
"""
