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

from horizons.component.componentholder import ComponentHolder
from horizons.constants import LAYERS
from horizons.scheduler import Scheduler
from horizons.util.tile_orientation import get_tile_alignment_action
from horizons.world.building.buildable import BuildableLine
from horizons.world.building.building import BasicBuilding


class Path(ComponentHolder):
	"""Object with path functionality"""
	walkable = True

	# no __init__

	def load(self, db, worldid):
		super().load(db, worldid)

	def init(self):
		# this does not belong in __init__, it's just here that all the data should be consistent
		self.__init()

	def __init(self):
		self.island.path_nodes.register_road(self)
		if self.session.world.inited:
			self.recalculate_surrounding_tile_orientation()
			self.recalculate_orientation()
		else:
			# don't always recalculate while loading, we'd recalculate too often.
			# do it once when everything is finished.
			Scheduler().add_new_object(self.recalculate_orientation, self, run_in=0)

	def remove(self):
		super().remove()
		self.island.path_nodes.unregister_road(self)
		self.recalculate_surrounding_tile_orientation()

	def is_road(self, tile):
		return (tile is not None and
		        tile.object is not None and
		        self.island.path_nodes.is_road(tile.x, tile.y) and
		        tile.object.owner == self.owner)

	def recalculate_surrounding_tile_orientation(self):
		for tile in self.island.get_surrounding_tiles(self.position):
			if self.is_road(tile):
				tile.object.recalculate_orientation()

	def recalculate_orientation(self):
		def is_similar_tile(position):
			tile = self.island.get_tile(position)
			return self.is_road(tile)

		origin = self.position.origin
		action = get_tile_alignment_action(origin, is_similar_tile)

		location = self._instance.getLocation()
		self.act(action, location, True)


class Road(Path, BasicBuilding, BuildableLine):
	"""Actual buildable road."""
	layer = LAYERS.FIELDS
