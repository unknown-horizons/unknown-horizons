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

from horizons.util import Point, decorators

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

	@decorators.make_constants()
	def __call__(self, source, destination, path_nodes, blocked_coords = list(), \
				       diagonal = False, make_target_walkable = True):
		"""
		@param source: Rect, Point or BasicBuilding
		@param destination: Rect, Point or BasicBuilding
		@param path_nodes: dict { (x, y) = speed_on_coords }  or list [(x, y), ..]
		@param blocked_coords: temporarily blocked coords (e.g. by a unit) as list or dict of tuples
		@param diagonal: whether the unit is able to move diagonally
		@param make_target_walkable: whether we force the tiles of the target to be walkable,
		       even if they actually aren't (used e.g. when walking to a building)
		@return: list of coords as tuples that are part of the best path
		         (from first coord after source to first coord in destination)
						 or None if no path is found
		"""
		# assure correct call
		# commented out checks since BasicBuilding can't be imported here
		#assert(isinstance(source, (Rect, Point, BasicBuilding)))
		#assert(isinstance(destination, (Rect, Point, BasicBuilding)))
		assert(isinstance(path_nodes, (dict, list, set)))
		assert(isinstance(blocked_coords, (dict, list, set)))

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

	@decorators.make_constants()
	def setup(self):
		"""Sets up variables for execution of algorithm
		@return: bool, whether setup was successful"""
		# support for building
		if hasattr(self.source, 'position'):
			self.source = self.source.position
		if hasattr(self.destination, 'position'):
			self.destination = self.destination.position

		if isinstance(self.path_nodes, list) or isinstance(self.path_nodes, set):
			self.path_nodes = dict.fromkeys(self.path_nodes, 1.0)

		# check if target is blocked
		target_is_blocked = True
		for coord in self.destination.tuple_iter():
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

	@decorators.make_constants()
	def execute(self):
		"""Executes algorithm"""
		# nodes are the keys of the following dicts (x, y)
		# the val of the keys are: (previous node, distance to here,
		# distance to here + estimated distance to target)
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
			# TODO: distance internally has to find out the type of
			# destination each time due to the dynamicness of python.
			# Find out if this costs a significant amount of time,
			# and if so, try to resolve this here.
			source_to_dest_dist = Point(*c).distance(self.destination)
			to_check[c] = (None, 0, source_to_dest_dist)

		# if one of the dest_coords has been processed
		# (i.e. is in checked), a good path is found
		dest_coords = self.destination.get_coordinates()
		dest_coords = set(dest_coords)
		if not self.make_target_walkable:
			# restrict destination coords to walkable tiles, by default they are counted as walkable
			dest_coords = dest_coords.intersection(self.path_nodes)

		from heapq import heappush, heappop
		heap = []
		for coords, data in to_check.iteritems():
			heappush(heap, (data[2], coords))

		# pull dereferencing out of loop
		path_nodes = self.path_nodes
		blocked_coords = self.blocked_coords
		destination = self.destination

		# loop until we have no more nodes to check
		while to_check:

			# find next node to check, which is the one with best rating
			(_, cur_node_coords) = heappop(heap)
			cur_node_data = to_check[cur_node_coords]

			# shortcuts:
			x = cur_node_coords[0]
			y = cur_node_coords[1]

			# find possible neighbors
			# optimisation TODO: use data structures more suitable for contains-check
			if self.diagonal:
				# all relevant adjacent neighbors
				x_p1 = x+1
				x_m1 = x-1
				y_p1 = y+1
				y_m1 = y-1
				neighbors = ( i for i in ((x_m1, y_m1), (x_m1, y), (x_m1, y_p1), (x, y_m1), (x, y_p1), (x_p1, y_m1), (x_p1, y), (x_p1, y_p1) ) if
											i not in checked and \
											(i in path_nodes or \
											 i in source_coords or \
											 i in dest_coords) and\
											i not in blocked_coords ) # conditions are sorted by likelyhood in ship worst case
			else:
				# all relevant vertical and horizontal neighbors
				neighbors = ( i for i in ((x-1, y), (x+1, y), (x, y-1), (x, y+1) ) if \
											(i in path_nodes  or \
											 i in source_coords or \
											 i in dest_coords ) and \
											i not in checked and \
											i not in blocked_coords )

			# Profiling info: In the worst case, this for-loop takes 80% of the time.
			# Parts of this are actually spent in evaluating the generator expressions from the if above

			for neighbor_node in neighbors:
				if not neighbor_node in to_check:
					# add neighbor to list of reachable nodes to check

					# save previous node, calc distance to neighbor_node
					# and estimate from neighbor_node to destination
					dist_to_here = cur_node_data[1] + path_nodes.get(cur_node_coords, 0)

					total_dist_estimation = destination.distance_to_tuple(neighbor_node) + dist_to_here
					to_check[neighbor_node] = (cur_node_coords,
					                           dist_to_here,
					                           total_dist_estimation)

					heappush(heap, (total_dist_estimation, neighbor_node))

				else:
					# neighbor has been processed,
					# check if current node provides a better path to this neighbor
					distance_to_neighbor = cur_node_data[1] + path_nodes.get(cur_node_coords, 0)

					neighbor = to_check[neighbor_node]

					if neighbor[1] > distance_to_neighbor:
						# found better path to neighbor, update values
						neighbor = ( cur_node_coords, \
							           distance_to_neighbor, \
							           distance_to_neighbor + ( neighbor[2]-neighbor[1] ) )


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