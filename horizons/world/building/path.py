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

from fife import fife

from horizons.constants import LAYERS, BUILDINGS
from horizons.world.building.building import BasicBuilding
from horizons.world.building.buildable import BuildableLine
from horizons.scheduler import Scheduler
from horizons.component.componentholder import ComponentHolder


class Path(ComponentHolder):
	"""Object with path functionality"""
	walkable = True

	# no __init__

	def load(self, db, worldid):
		super(Path, self).load(db, worldid)

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
		super(Path, self).remove()
		self.island.path_nodes.unregister_road(self)
		self.recalculate_surrounding_tile_orientation()

	def recalculate_surrounding_tile_orientation(self):
		for tile in self.island.get_surrounding_tiles(self.position):
			if tile is not None and tile.object is not None and \
			   self.island.path_nodes.is_road(tile.x, tile.y):
				tile.object.recalculate_orientation()

	def recalculate_orientation(self):
		# orientation is a string containing a, b, c and/or d
		# corresponding actions are saved in the db
		action = ''
		origin = self.position.origin
		path_nodes = self.island.path_nodes

		for action_part in sorted(BUILDINGS.ACTION.action_offset_dict): # order is important here
			offset = BUILDINGS.ACTION.action_offset_dict[action_part]
			tile = self.island.get_tile(origin.offset(*offset))
			if tile is not None and tile.object is not None and \
			   path_nodes.is_road(tile.x, tile.y) and \
			   self.owner == tile.object.owner:
				action += action_part
		if action == '':
			action = 'single' # single trail piece with no neighbours

		location = self._instance.getLocation()
		location.setLayerCoordinates(fife.ModelCoordinate(int(origin.x + 1), int(origin.y), 0))
		self.act(action, location, True)

class Road(Path, BasicBuilding, BuildableLine):
	"""Actual buildable road."""
	layer = LAYERS.FIELDS