# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.constants import GROUND

DEEP_WATER = 0
SHALLOW_WATER = 1
SAND = 2
GRASS = 3


class IntermediateMap:

	def __init__(self, world):
		self.world = world
		self.session = world.session
		self._init_map()

	def _get_tile_repr(self, coords):
		if coords not in self.world.full_map:
			return 0

		tile = self.world.full_map[coords]
		if tile.id <= 0:
			return DEEP_WATER
		elif tile.id == 1:
			return SHALLOW_WATER
		elif tile.id == 6:
			return SAND
		elif tile.id == 3:
			return GRASS
		else:
			offset = 0 if tile.id == 2 else (1 if tile.id == 5 else 2)
			rotation = tile.rotation // 90
			if tile.shape == 'straight':
				return offset + (1, 0, 0, 1)[rotation] # 2 low, 2 high
			elif tile.shape == 'curve_in':
				return offset + (1, 1, 0, 1)[rotation] # 1 low, 3 high
			else:
				return offset + (1, 0, 0, 0)[rotation] # 3 low, 1 high

	def _init_map(self):
		self._map = {}
		width = self.world.max_x - self.world.min_x + 1
		height = self.world.max_y - self.world.min_y + 1
		for y in range(height + 2):
			orig_y = y + self.world.min_y - 1
			for x in range(width + 2):
				orig_x = x + self.world.min_x - 1
				self._map[(x, y)] = self._get_tile_repr((orig_x, orig_y))

		self.max_x = width - 1
		self.max_y = height - 1

	def _get_intermediate_coords(self, coords):
		return (coords[0] - self.world.min_x, coords[1] - self.world.min_y)

	def distance_from_edge(self, coords):
		x, y = coords
		return min(min(x, self.max_x - x), min(y, self.max_y - y))

	def _update_intermediate_coords(self, coords, new_type):
		if self._map[coords] == new_type:
			return
		self._map[coords] = min(new_type, self.distance_from_edge(coords))

	def _fix_map(self, coords_list, new_type):
		changes = True
		while changes:
			changes = False
			for x, y in coords_list:
				top_left = (x, y)
				if top_left not in self._map:
					continue
				bottom_right = (x + 1, y + 1)
				if bottom_right not in self._map:
					continue
				if self._map[top_left] != self._map[bottom_right]:
					continue
				bottom_left = (x, y + 1)
				top_right = (x + 1, y)
				if self._map[bottom_left] != self._map[top_right]:
					continue
				diff = self._map[top_left] - self._map[top_right]
				if diff == 0:
					continue

				lower_corner = top_right if diff == 1 else top_left
				higher_corner = top_left if diff == 1 else top_right
				mi = self._map[lower_corner]
				if new_type <= mi:
					self._set_tiles([higher_corner], mi)
				else:
					self._set_tiles([lower_corner], mi + 1)
				changes = True

	def set_south_east_corner(self, raw_coords_list, tile_details):
		new_type = tile_details[0] if tile_details[0] != 6 else 2
		coords_list = []
		for coords in raw_coords_list:
			if coords not in self.world.fake_tile_map:
				continue

			coords2 = self._get_intermediate_coords(coords)
			assert coords2 in self._map
			if self._map[coords2] != new_type:
				coords_list.append(coords2)

		if coords_list:
			self._set_tiles(coords_list, new_type)

	def _get_surrounding_coords(self, current_coords_list):
		all_neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
		current_coords_set = set(current_coords_list)
		result = set()
		for x, y in current_coords_list:
			for dx, dy in all_neighbors:
				coords2 = (x + dx, y + dy)
				if coords2 in self._map and coords2 not in current_coords_set:
					result.add(coords2)
		return sorted(result)

	def _set_tiles(self, initial_coords_list, new_type):
		last_coords_list = []
		for coords in initial_coords_list:
			last_coords_list.append(coords)
			self._update_intermediate_coords(coords, new_type)

		for _ in range(3):
			surrounding_coords_list = self._get_surrounding_coords(last_coords_list)
			for coords2 in surrounding_coords_list:
				if coords2 not in self._map:
					continue

				cur_type = self._map[coords2]
				best_new_type = cur_type
				best_dist = 10
				for new_type2 in range(4):
					if best_dist <= abs(new_type2 - cur_type):
						continue

					suitable = True
					for updated_coords in last_coords_list:
						if abs(updated_coords[0] - coords2[0]) > 1 or abs(updated_coords[1] - coords2[1]) > 1:
							continue
						if abs(self._map[updated_coords] - new_type2) > 1:
							suitable = False
							break
					if not suitable:
						continue

					best_new_type = new_type2
					best_dist = abs(new_type2 - cur_type)
				self._update_intermediate_coords(coords2, best_new_type)
				last_coords_list.append(coords2)

		self._fix_map(last_coords_list, new_type)
		for coords in last_coords_list:
			self._update_tile(*coords)

	def _update_tile(self, x, y):
		if (x, y) not in self._map:
			return
		if (x + 1, y + 1) not in self._map:
			return

		data = []
		for dy in range(2):
			for dx in range(2):
				data.append(self._map[(x + dx, y + dy)])
		coords = (x + self.world.min_x, y + self.world.min_y)

		minimum = min(data)
		for i in range(4):
			data[i] -= minimum

		if max(data) == 0:
			ground_class = {
				DEEP_WATER: GROUND.WATER,
				SHALLOW_WATER: GROUND.SHALLOW_WATER,
				SAND: GROUND.SAND,
				GRASS: GROUND.DEFAULT_LAND,
			}[minimum]
			self.session.world_editor.set_tile(coords, ground_class)
		else:
			assert max(data) == 1, 'This should never happen'
			tile_type = 2 if minimum == 0 else (5 if minimum == 1 else 4)
			tile_def = {
				(0, 1, 0, 1): (tile_type, 'straight', 45),
				(1, 1, 0, 0): (tile_type, 'straight', 135),
				(1, 0, 1, 0): (tile_type, 'straight', 225),
				(0, 0, 1, 1): (tile_type, 'straight', 315),
				(0, 1, 1, 1): (tile_type, 'curve_in', 45),
				(1, 1, 0, 1): (tile_type, 'curve_in', 135),
				(1, 1, 1, 0): (tile_type, 'curve_in', 225),
				(1, 0, 1, 1): (tile_type, 'curve_in', 315),
				(0, 0, 0, 1): (tile_type, 'curve_out', 45),
				(0, 1, 0, 0): (tile_type, 'curve_out', 135),
				(1, 0, 0, 0): (tile_type, 'curve_out', 225),
				(0, 0, 1, 0): (tile_type, 'curve_out', 315),
			}[tuple(data)]
			self.session.world_editor.set_tile(coords, tile_def)

	def __str__(self):
		res = ''
		width = self.world.max_x - self.world.min_x + 1
		height = self.world.max_y - self.world.min_y + 1
		for y in range(height + 2):
			for x in range(width + 2):
				res += str(self._map[(x, y)])
			res += '\n'
		return res
