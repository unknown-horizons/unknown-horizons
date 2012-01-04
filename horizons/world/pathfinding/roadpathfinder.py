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

class RoadPathFinder(object):
	"""Finds the shortest path that should be most preferred by human players."""

	# the values are based on the configurations of the first two of the three sets of relative coordinates (previous, current, next)
	__counterclockwise_turns = [((0, 0), (0, 1)), ((0, 1), (1, 1)), ((1, 0), (0, 0)), ((1, 1), (1, 0))]

	@classmethod
	def __is_preferred_turn(cls, previous_coords, current_coords, next_coords, clockwise):
		"""Returns True if and only if the turn is in the preferred direction."""
		min_x = min(previous_coords[0], current_coords[0], next_coords[0])
		min_y = min(previous_coords[1], current_coords[1], next_coords[1])
		relative_previous_coords = (previous_coords[0] - min_x, previous_coords[1] - min_y)
		relative_current_coords = (current_coords[0] - min_x, current_coords[1] - min_y)
		return ((relative_previous_coords, relative_current_coords) in cls.__counterclockwise_turns) ^ clockwise

	def __call__(self, path_nodes, source, destination, clockwise = True):
		"""
		Return the path from the source to the destination or None if it is impossible.

		@param path_nodes: {(x, y): unused value, ...}
		@param source: (x, y)
		@param destination: (x, y)
		@param clockwise: bool; whether to try finding the path clockwise or counterclockwise
		"""

		if source not in path_nodes or destination not in path_nodes:
			return None
		if source == destination:
			return [source]

		distance = {}
		heap = []
		for dir in xrange(2): # 0 -> changed x, 1 -> changed y
			# NOTE: all distances are in the form (actual distance, number of turns, number of non-preferred turns)
			real_distance = (1, 0, 0)
			expected_distance = (((source[0] - destination[0]) ** 2 + (source[1] - destination[1]) ** 2) ** 0.5, 0, 0)
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

				# determine whether this is a turn and if so then whether it is in the preferred direction
				turn = reduced_dir != key[2]
				if turn and distance[key][1] is None:
					continue # disallow turning as the first step; doesn't affect the ability to find the best path
				good_turn = self.__is_preferred_turn(distance[key][1][:2], key[:2], coords, clockwise) if turn else True

				# NOTE: all distances are in the form (actual distance, number of turns, number of non-preferred turns)
				real_distance = (distance_so_far[0] + 1, distance_so_far[1] + (1 if turn else 0), distance_so_far[2] + (0 if good_turn else 1))
				expected_distance = (real_distance[0] + ((coords[0] - destination[0]) ** 2 + (coords[1] - destination[1]) ** 2) ** 0.5, real_distance[1], real_distance[2])
				if next_key not in distance or distance[next_key][0] > real_distance:
					distance[next_key] = (real_distance, key)
					heapq.heappush(heap, (expected_distance, real_distance, next_key))

		# save path
		if final_key is not None:
			path = []
			while final_key is not None:
				path.append(final_key[:2])
				final_key = distance[final_key][1]
			return path
		return None

decorators.bind_all(RoadPathFinder)
