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

import os
import os.path

from collections import deque

from horizons.constants import GROUND
from horizons.command.unit import RemoveUnit
from horizons.entities import Entities
from horizons.gui.util import load_uh_widget
from horizons.util.dbreader import DbReader
from horizons.util.python.callback import Callback
from horizons.util.shapes import Rect
from horizons.util.uhdbaccessor import read_savegame_template

class WorldEditor(object):
	def __init__(self, world):
		super(WorldEditor, self).__init__()
		self.world = world
		self.session = world.session
		self._remove_unnecessary_objects()
		self._center_view()

		self.brush_size = 1
		self._show_settings()
		self._change_brush_size(1)

		self._create_intermediate_map()

	def _show_settings(self):
		"""Display settings widget to change brush size."""
		self.widget = load_uh_widget('editor_settings.xml')
		for i in range(1, 4):
			b = self.widget.findChild(name='size_%d' % i)
			b.capture(Callback(self._change_brush_size, i))
		self.widget.show()

	def _change_brush_size(self, size):
		"""Change the brush size and update the gui."""
		images = {
		  'box_highlighted': 'content/gui/icons/ship/smallbutton_a.png',
		  'box': 'content/gui/icons/ship/smallbutton.png',
		}

		b = self.widget.findChild(name='size_%d' % self.brush_size)
		b.up_image = images['box']

		self.brush_size = size
		b = self.widget.findChild(name='size_%d' % self.brush_size)
		b.up_image = images['box_highlighted']

	def _remove_unnecessary_objects(self):
		# Delete all ships.
		for ship in (ship for ship in self.world.ships):
			RemoveUnit(ship).execute(self.session)

	def _center_view(self):
		min_x = min(zip(*self.world.full_map.keys())[0])
		max_x = max(zip(*self.world.full_map.keys())[0])
		min_y = min(zip(*self.world.full_map.keys())[1])
		max_y = max(zip(*self.world.full_map.keys())[1])
		self.session.view.center((min_x + max_x) // 2, (min_y + max_y) // 2)

	def _get_double_repr(self, coords):
		if coords in self.world.full_map:
			tile = self.world.full_map[coords]
			if tile.id <= 0:
				# deep water
				return (0, 0, 0, 0)
			elif tile.id == 1:
				# shallow water
				return (1, 1, 1, 1)
			elif tile.id == 6:
				# sand
				return (2, 2, 2, 2)
			elif tile.id == 3:
				# grass
				return (3, 3, 3, 3)
			else:
				offset = 0 if tile.id == 2 else (1 if tile.id == 5 else 2)
				rot = tile._instance.getRotation() // 90
				if tile._action == 'straight':
					# 2 low, 2 high
					if rot == 0:
						return (offset, offset + 1, offset, offset + 1)
					elif rot == 1:
						return (offset + 1, offset + 1, offset, offset)
					elif rot == 2:
						return (offset + 1, offset, offset + 1, offset)
					else:
						return (offset, offset, offset + 1, offset + 1)
				elif tile._action == 'curve_in':
					# 1 low, 3 high
					if rot == 0:
						return (offset, offset + 1, offset + 1, offset + 1)
					elif rot == 1:
						return (offset + 1, offset + 1, offset, offset + 1)
					elif rot == 2:
						return (offset + 1, offset + 1, offset + 1, offset)
					else:
						return (offset + 1, offset, offset + 1, offset + 1)
				else:
					# 3 low, 1 high
					if rot == 0:
						return (offset, offset, offset, offset + 1)
					elif rot == 1:
						return (offset, offset + 1, offset, offset)
					elif rot == 2:
						return (offset + 1, offset, offset, offset)
					else:
						return (offset, offset, offset + 1, offset)
		else:
			return (0, 0, 0, 0)

	def _create_intermediate_map(self):
		double_map = {}
		width = self.world.max_x - self.world.min_x + 1
		height = self.world.max_y - self.world.min_y + 1
		for dy in xrange(height + 2):
			orig_y = dy + self.world.min_y - 1
			for dx in xrange(width + 2):
				orig_x = dx + self.world.min_x - 1
				double_repr = self._get_double_repr((orig_x, orig_y))
				double_map[(2 * dx, 2 * dy)] = None #double_repr[0]
				double_map[(2 * dx + 1, 2 * dy)] = None #double_repr[1]
				double_map[(2 * dx, 2 * dy + 1)] = None #double_repr[2]
				double_map[(2 * dx + 1, 2 * dy + 1)] = double_repr[3]

		self._intermediate_map = {}
		for dy in xrange(1, 2 * height + 4, 2):
			s = ''
			for dx in xrange(1, 2 * width + 4, 2):
				self._intermediate_map[(dx // 2, dy // 2)] = double_map[(dx, dy)]
				s += str(double_map[(dx, dy)])
		self._print_intermediate_map()

	def _print_intermediate_map(self):
		width = self.world.max_x - self.world.min_x + 1
		height = self.world.max_y - self.world.min_y + 1
		for dy in xrange(1, 2 * height + 4, 2):
			s = ''
			for dx in xrange(1, 2 * width + 4, 2):
				s += str(self._intermediate_map[(dx // 2, dy // 2)])
			print s
		print

	def get_tile_details(self, coords):
		if coords in self.world.full_map:
			tile = self.world.full_map[coords]
			if tile.id == -1:
				return GROUND.WATER
			else:
				return (tile.id, tile._action, tile._instance.getRotation() + 45)
		else:
			return GROUND.WATER

	def _iter_islands(self):
		ground = {}
		for coords, tile in self.world.full_map.iteritems():
			if tile.id <= 0:
				continue
			ground[coords] = None

		moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

		n = 0
		for coords in sorted(ground.iterkeys()):
			if ground[coords] is not None:
				continue

			coords_list = [coords]
			ground[coords] = n
			queue = deque([coords])
			while queue:
				x, y = queue[0]
				queue.popleft()
				for dx, dy in moves:
					coords2 = (x + dx, y + dy)
					if coords2 in ground and ground[coords2] is None:
						ground[coords2] = n
						queue.append(coords2)
						coords_list.append(coords2)
			n += 1
			yield coords_list

	def _save_islands(self, db, path, prefix):
		for coords_list in self._iter_islands():
			min_x, min_y = 1000000000, 1000000000
			for x, y in coords_list:
				if x < min_x:
					min_x = x
				if y < min_y:
					min_y = y
	
			island_name = '%s_island_%d_%d.sqlite' % (prefix, min_x, min_y)
			island_db_path = os.path.join(path, island_name)
			if os.path.exists(island_db_path):
				os.unlink(island_db_path) # the process relies on having an empty file
			db('INSERT INTO island (x, y, file) VALUES(?, ?, ?)', min_x, min_y, 'content/islands/' + island_name)

			island_db = DbReader(island_db_path)
			island_db('CREATE TABLE ground(x INTEGER NOT NULL, y INTEGER NOT NULL, ground_id INTEGER NOT NULL, action_id TEXT NOT NULL, rotation INTEGER NOT NULL)')
			island_db('CREATE TABLE island_properties(name TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)')
			island_db('BEGIN')
			for x, y in coords_list:
				tile = self.world.full_map[(x, y)]
				island_db('INSERT INTO ground VALUES(?, ?, ?, ?, ?)', x - min_x, y - min_y, tile.id, tile._action, tile._instance.getRotation() + 45)
			island_db('COMMIT')
			island_db.close()

	def save_map(self, path, prefix):
		map_file = os.path.join(path, prefix + '.sqlite')
		if os.path.exists(map_file):
			os.unlink(map_file) # the process relies on having an empty file
		db = DbReader(map_file)
		read_savegame_template(db)
		db('BEGIN')
		self._save_islands(db, path, prefix)
		db('COMMIT')
		db.close()

	def _get_intermediate_coords(self, coords):
		return (coords[0] - self.world.min_x, coords[1] - self.world.min_y)

	def _update_intermediate_coords(self, coords, new_type):
		if self._intermediate_map[coords] == new_type:
			return
		self._intermediate_map[coords] = new_type

	def set_tile_from_intermediate(self, x, y):
		if (x, y) not in self._intermediate_map:
			return
		if (x + 1, y + 1) not in self._intermediate_map:
			return

		data = []
		for dy in xrange(2):
			for dx in xrange(2):
				data.append(self._intermediate_map[(x + dx, y + dy)])
		coords = (x + self.world.min_x, y + self.world.min_y)

		mi = min(data)
		for i in xrange(4):
			data[i] -= mi
		if max(data) == 0:
			# the same tile
			if mi == 0:
				self.set_tile(coords, GROUND.WATER)
			elif mi == 1:
				self.set_tile(coords, GROUND.SHALLOW_WATER)
			elif mi == 2:
				self.set_tile(coords, GROUND.SAND)
			elif mi == 3:
				self.set_tile(coords, GROUND.DEFAULT_LAND)
		else:
			assert max(data) == 1
			type = 2 if mi == 0 else (5 if mi == 1 else 4)
			if data == [0, 1, 0, 1]:
				self.set_tile(coords, (type, 'straight', 45))
			elif data == [1, 1, 0, 0]:
				self.set_tile(coords, (type, 'straight', 135))
			elif data == [1, 0, 1, 0]:
				self.set_tile(coords, (type, 'straight', 225))
			elif data == [0, 0, 1, 1]:
				self.set_tile(coords, (type, 'straight', 315))
			elif data == [0, 1, 1, 1]:
				self.set_tile(coords, (type, 'curve_in', 45))
			elif data == [1, 1, 0, 1]:
				self.set_tile(coords, (type, 'curve_in', 135))
			elif data == [1, 1, 1, 0]:
				self.set_tile(coords, (type, 'curve_in', 225))
			elif data == [1, 0, 1, 1]:
				self.set_tile(coords, (type, 'curve_in', 315))
			elif data == [0, 0, 0, 1]:
				self.set_tile(coords, (type, 'curve_out', 45))
			elif data == [0, 1, 0, 0]:
				self.set_tile(coords, (type, 'curve_out', 135))
			elif data == [1, 0, 0, 0]:
				self.set_tile(coords, (type, 'curve_out', 225))
			elif data == [0, 0, 1, 0]:
				self.set_tile(coords, (type, 'curve_out', 315))
			else:
				self.set_tile(coords, GROUND.SAND)

	def set_south_east_corner(self, coords, tile_details):
		x, y = coords
		if not (self.world.min_x <= x < self.world.max_x and self.world.min_y <= y < self.world.max_y):
			return

		dx, dy = self._get_intermediate_coords(coords)
		new_type = tile_details[0] if tile_details[0] != 6 else 2
		if self._intermediate_map[(dx, dy)] == new_type:
			return
		updated_coords_set = set()
		self._update_intermediate_coords((dx, dy), new_type)

		rect = Rect.init_from_topleft_and_size(dx, dy, 1, 1)
		for dist in xrange(2):
			for coords2 in rect.get_surrounding():
				if coords2 not in self._intermediate_map:
					continue
				cur_type = self._intermediate_map[coords2]
				best_new_type = cur_type
				best_dist = 10
				for new_type2 in xrange(4):
					if best_dist <= abs(new_type2 - cur_type):
						continue
					suitable = True
					for updated_coords in rect.tuple_iter():
						if abs(updated_coords[0] - coords2[0]) > 1 or abs(updated_coords[1] - coords2[1]) > 1:
							continue
						if abs(self._intermediate_map[updated_coords] - new_type2) > 1:
							suitable = False
							break
					if not suitable:
						continue
					best_new_type = new_type2
					best_dist = abs(new_type2 - cur_type)
				self._update_intermediate_coords(coords2, best_new_type)
			rect = Rect.init_from_topleft_and_size(dx - 1, dy - 1, 3, 3)
		#self._print_intermediate_map()

		for x2 in xrange(dx - 4, dx + 4):
			for y2 in xrange(dy - 4, dy + 4):
				self.set_tile_from_intermediate(x2, y2)

	def set_tile(self, coords, tile_details):
		if coords in self.world.full_map:
			if coords in self.world.full_map:
				old_tile = self.world.full_map[coords]
				if old_tile.id != -1:
					instance = old_tile._instance
					layer = instance.getLocation().getLayer()
					layer.deleteInstance(instance)

			(ground_id, action_id, rotation) = tile_details
			ground = Entities.grounds[ground_id](self.session, *coords)
			ground.act(action_id, rotation)
			self.world.full_map[coords] = ground
			# TODO: update the minimap
