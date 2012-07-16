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

import heapq

from horizons.util.python import decorators

class RoadPlanner(object):
	"""
	Finds the most reasonable road between two areas.

	This class uses the A* algorithm to find a path that would look nice as a road.
	Penalties are give for the following:
	* not an existing road
	* close to an existing road
	* not straight
	* not close to boundaries (coast, mountains, etc.)
	"""

	def __call__(self, personality, source, destination, destination_beacon, path_nodes, blocked_coords=None):
		"""
		Return the path from the source to the destination or None if it is impossible.

		@param personality: the personality class that contains the relevant personality bits
		@param source: list of tuples [(x, y), ...]
		@param destination: list of tuples [(x, y), ...]
		@param destination_beacon: object with a defined distance_to_tuple function (must contain all of destination)
		@param path_nodes: dict {(x, y): penalty}
		@param blocked_coords: temporarily blocked coordinates set([(x, y), ...])
		"""
		blocked_coords = blocked_coords or set()
		target_blocked = True
		for coords in destination:
			if coords not in blocked_coords and coords in path_nodes:
				target_blocked = False
				break
		if target_blocked:
			return None

		distance = {}
		heap = []
		for coords in source:
			if coords not in blocked_coords and coords in path_nodes:
				for dir in xrange(2): # 0 -> changed x, 1 -> changed y
					real_distance = path_nodes[coords]
					expected_distance = destination_beacon.distance_to_tuple(coords)
					key = (coords[0], coords[1], dir)
					# the value is (real distance so far, previous key)
					distance[key] = (real_distance, None)
					# (expected distance to the destination, current real distance, key)
					heap.append((expected_distance, real_distance, key))
		heapq.heapify(heap)

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		final_key = None

		# perform A*
		while heap:
			(_, distance_so_far, key) = heapq.heappop(heap)
			if distance[key] < distance_so_far:
				continue
			if (key[0], key[1]) in destination:
				final_key = key
				break

			for dir in xrange(4):
				coords = (key[0] + moves[dir][0], key[1] + moves[dir][1])
				if coords not in path_nodes or coords in blocked_coords:
					continue
				reduced_dir = 0 if moves[dir][0] != 0 else 1
				next_key = (coords[0], coords[1], reduced_dir)
				real_distance = distance_so_far + path_nodes[coords] + (0 if reduced_dir == key[2] else personality.turn_penalty)
				expected_distance = real_distance + destination_beacon.distance_to_tuple(coords)
				if next_key not in distance or distance[next_key][0] > real_distance:
					distance[next_key] = (real_distance, key)
					heapq.heappush(heap, (expected_distance, real_distance, next_key))

		# save path
		if final_key is not None:
			path = []
			while final_key is not None:
				path.append((final_key[0], final_key[1]))
				final_key = distance[final_key][1]
			return path
		return None

decorators.bind_all(RoadPlanner)
