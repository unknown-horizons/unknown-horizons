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
from horizons.util.dbreader import DbReader
from horizons.util.uhdbaccessor import read_savegame_template

class WorldEditor(object):
	def __init__(self, world):
		super(WorldEditor, self).__init__()
		self.world = world
		self.session = world.session
		self._remove_unnecessary_objects()
		self._center_view()

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
