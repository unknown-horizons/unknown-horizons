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

from typing import Dict, Tuple

from fife import fife

import horizons.globals
from horizons.constants import GROUND
from horizons.util.loaders.tilesetloader import TileSetLoader
from horizons.util.shapes import Circle, Point

from .navigationtool import NavigationTool


class TileLayingTool(NavigationTool):
	"""Tool to lay ground tiles."""
	HIGHLIGHT_COLOR = (0, 200, 90)

	tile_images = {} # type: Dict[Tuple[int, str, int], fife.SharedImagePointer]

	def __init__(self, session, tile_details):
		super().__init__(session)
		self.renderer = session.view.renderer['InstanceRenderer']
		self._tile_details = (None, None, None)
		if tile_details[0] in [0, 2]:
			self._tile_details = GROUND.WATER
		elif tile_details[0] in [1, 5]:
			self._tile_details = GROUND.SHALLOW_WATER
		elif tile_details[0] in [6, 4]:
			self._tile_details = GROUND.SAND
		else:
			self._tile_details = GROUND.DEFAULT_LAND
		self._set_cursor_image()

	def _set_cursor_image(self):
		"""Replace the cursor with an image of the selected tile."""
		# FIXME the water tile is too big to use as cursor
		if self._tile_details[0] == 0:
			return

		tile = tuple(self._tile_details)
		image = TileLayingTool.tile_images.get(tile)
		if not image:
			tile_sets = TileSetLoader.get_sets()

			ground_id, action_id, rotation = tile
			set_id = horizons.globals.db.get_random_tile_set(ground_id)
			filename = list(tile_sets[set_id][action_id][rotation].keys())[0]

			image = horizons.globals.fife.imagemanager.load(filename)
			TileLayingTool.tile_images[tile] = image

		horizons.globals.fife.cursor.set(image)

	def remove(self):
		self._remove_coloring()
		horizons.globals.fife.set_cursor_image('default')
		super().remove()

	def on_escape(self):
		self.session.ingame_gui.set_cursor()

	def mouseMoved(self, evt):
		if evt.isConsumedByWidgets():
			self._remove_coloring()
		else:
			self.update_coloring(evt)

	def _place_tile(self, coords):
		brush = Circle(Point(*coords), self.session.world_editor.brush_size - 1)
		self.session.world_editor.intermediate_map.set_south_east_corner(brush.tuple_iter(), self._tile_details)

	def get_world_location(self, evt):
		screenpoint = self._get_screenpoint(evt)
		mapcoords = self.session.view.cam.toMapCoordinates(screenpoint, False)
		return self._round_map_coords(mapcoords.x + 0.5, mapcoords.y + 0.5)

	def mousePressed(self, evt):
		if evt.getButton() == fife.MouseEvent.LEFT and not evt.isConsumedByWidgets():
			coords = self.get_world_location(evt).to_tuple()
			self._place_tile(coords)
			evt.consume()
		elif evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
			evt.consume()
		else:
			super().mouseClicked(evt)

	def mouseDragged(self, evt):
		"""Allow placing tiles continusly while moving the mouse."""
		if evt.getButton() == fife.MouseEvent.LEFT:
			coords = self.get_world_location(evt).to_tuple()
			self._place_tile(coords)
			self.update_coloring(evt)
			evt.consume()

	def update_coloring(self, evt):
		self._remove_coloring()
		self._add_coloring(self.get_world_location(evt).to_tuple())

	def _add_coloring(self, pos):
		brush = Circle(Point(*pos), self.session.world_editor.brush_size - 1)
		for p in brush.tuple_iter():
			if p not in self.session.world.full_map:
				continue

			tile = self.session.world.full_map[p]
			if hasattr(tile, '_instance'):
				self.renderer.addColored(tile._instance, *self.HIGHLIGHT_COLOR)

	def _remove_coloring(self):
		self.renderer.removeAllColored()
