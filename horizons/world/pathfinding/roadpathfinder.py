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

import heapq

from horizons.util.python import decorators

class RoadPathFinder(object):
	"""Finds the shortest path that should be most preferred by human players."""

	def __call__(self, path_nodes, source, destination):
		"""
		Return the path from the source to the destination or None if it is impossible.

		@param path_nodes: {(x, y): unused value, ...}
		@param source: (x, y)
		@param destination: (x, y)
		"""

		if source not in path_nodes or destination not in path_nodes:
			return None
		if source == destination:
			return [source]

		distance = {}
		heap = []
		for dir in xrange(2): # 0 -> changed x, 1 -> changed y
			# NOTE: all distances are in the form (actual distance, number of turns)
			real_distance = (1, 0)
			expected_distance = (((source[0] - destination[0]) ** 2 + (source[1] - destination[1]) ** 2) ** 0.5, 0)
			key = (source[0], source[1], dir)
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
			if (key[0], key[1]) == destination:
				final_key = key
				break

			for dir in xrange(4):
				coords = (key[0] + moves[dir][0], key[1] + moves[dir][1])
				if coords not in path_nodes:
					continue
				reduced_dir = 0 if moves[dir][0] != 0 else 1
				next_key = (coords[0], coords[1], reduced_dir)
				# NOTE: all distances are in the form (actual distance, number of turns)
				real_distance = (distance_so_far[0] + 1, distance_so_far[1] + (0 if reduced_dir == key[2] else 1))
				expected_distance = (real_distance[0] + ((coords[0] - destination[0]) ** 2 + (coords[1] - destination[1]) ** 2) ** 0.5, real_distance[1])
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

decorators.bind_all(RoadPathFinder)
