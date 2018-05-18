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

import logging
import os
import os.path
import sqlite3
from collections import deque

from horizons.command.unit import RemoveUnit
from horizons.constants import EDITOR
from horizons.editor.intermediatemap import IntermediateMap
from horizons.entities import Entities
from horizons.gui.widgets.minimap import Minimap
from horizons.scheduler import Scheduler
from horizons.util.dbreader import DbReader
from horizons.util.python.callback import Callback


class WorldEditor:
	def __init__(self, world):
		super().__init__() # TODO: check whether this call is needed
		self.world = world
		self.session = world.session
		self.intermediate_map = IntermediateMap(world)
		self._remove_unnecessary_objects()
		self._center_view()

		self.brush_size = EDITOR.DEFAULT_BRUSH_SIZE

		self._tile_delete_set = set()

		self.log = logging.getLogger("gui")

	def _remove_unnecessary_objects(self):
		# Delete all ships.
		for ship in (ship for ship in self.world.ships):
			RemoveUnit(ship).execute(self.session)

	def _center_view(self):
		min_x = min(list(zip(*self.world.full_map.keys()))[0])
		max_x = max(list(zip(*self.world.full_map.keys()))[0])
		min_y = min(list(zip(*self.world.full_map.keys()))[1])
		max_y = max(list(zip(*self.world.full_map.keys()))[1])
		self.session.view.center((min_x + max_x) // 2, (min_y + max_y) // 2)

	def _iter_islands(self):
		ground = {}
		for coords, tile in self.world.full_map.items():
			if tile.id <= 0:
				continue
			ground[coords] = None

		moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

		n = 0
		for coords in sorted(ground.keys()):
			if ground[coords] is not None:
				continue

			coords_list = [coords]
			ground[coords] = n
			queue = deque([coords])
			while queue:
				x, y = queue.popleft()
				for dx, dy in moves:
					coords2 = (x + dx, y + dy)
					if coords2 in ground and ground[coords2] is None:
						ground[coords2] = n
						queue.append(coords2)
						coords_list.append(coords2)
			yield (n, coords_list)
			n += 1

	def save_map(self, path, prefix):
		map_file = os.path.join(path, prefix + '.sqlite')
		if os.path.exists(map_file):
			os.unlink(map_file) # the process relies on having an empty file

		db = DbReader(map_file)
		with open('content/map-template.sql') as map_template:
			db.execute_script(map_template.read())

		save_successful = True
		try:
			db('BEGIN')
			for island_id, coords_list in self._iter_islands():
				for x, y in coords_list:
					tile = self.world.full_map[(x, y)]
					db('INSERT INTO ground VALUES(?, ?, ?, ?, ?, ?)', island_id, x, y, tile.id, tile.shape, tile.rotation)
			db('COMMIT')
		except sqlite3.Error as e:
			self.log.debug('Error: {error}'.format(error=e.args[0]))
			save_successful = False
		finally:
			db.close()

		return save_successful

	def _delete_tile_instance(self, old_tile):
		self._tile_delete_set.remove(old_tile)
		instance = old_tile._instance
		layer = instance.getLocation().getLayer()
		layer.deleteInstance(instance)
		old_tile._instance = None

	def set_tile(self, coords, tile_details):
		if coords not in self.world.full_map:
			return

		old_tile = self.world.full_map[coords]
		if old_tile and old_tile.id != -1 and old_tile._instance and old_tile not in self._tile_delete_set:
			if (old_tile.id, old_tile.shape, old_tile.rotation) == tile_details:
				return
			self._tile_delete_set.add(old_tile)
			Scheduler().add_new_object(Callback(self._delete_tile_instance, old_tile), self, run_in=0)

		(ground_id, shape, rotation) = tile_details
		if ground_id != 0:
			ground = Entities.grounds['{:d}-{}'.format(ground_id, shape)](self.session, *coords)
			ground.act(rotation)
			self.world.full_map[coords] = ground
		else:
			self.world.full_map[coords] = self.world.fake_tile_map[coords]
		Minimap.update(coords)

		# update cam, that's necessary because of the static layer WATER
		self.session.view.cam.refresh()
