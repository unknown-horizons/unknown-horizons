# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import weakref
import fife

import horizons.main

from building import BasicBuilding
from buildable import BuildableLine, BuildableSingle
from horizons.constants import LAYERS

class Path(BasicBuilding, BuildableLine):
	walkable = True

	def init(self):
		super(Path, self).init()
		self.__init()
		self.recalculate_surrounding_tile_orientation()

	def load(self, db, worldid):
		super(Path, self).load(db, worldid)
		self.__init()

	def __init(self):
		self.island().path_nodes.register_road(self)
		self.recalculate_orientation()

	def remove(self):
		super(Path, self).remove()
		self.island().path_nodes.unregister_road(self)
		self.recalculate_surrounding_tile_orientation()

	def recalculate_surrounding_tile_orientation(self):
		for tile in self.island().get_surrounding_tiles(self.position.origin):
			if tile is not None and self.island().path_nodes.is_road(tile.x, tile.y):
				tile.object.recalculate_orientation()

	action_offset_dict = {
		'a' : (0, -1),
		'b' : (1, 0),
		'c' : (0, 1),
		'd' : (-1, 0)
		}
	def recalculate_orientation(self):
		"""
		"""
		# orientation is a string containing a, b, c and/or d
		# corresponding actions are saved in the db
		action = ''
		origin = self.position.origin
		path_nodes = self.island().path_nodes

		for action_part in sorted(self.action_offset_dict): # order is important here
			offset = self.action_offset_dict[action_part]
			tile = self.island().get_tile(origin.offset(*offset))
			if tile is not None and path_nodes.is_road(tile.x, tile.y):
				action += action_part
		if action == '':
			action = 'ac' # default

		location = self._instance.getLocation()
		location.setLayerCoordinates(fife.ModelCoordinate(int(origin.x + 1), int(origin.y), 0))
		self.act(action, location, True)

	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = LAYERS.GROUND
		return super(Path, cls).getInstance(*args, **kwargs)

class Bridge(BasicBuilding, BuildableSingle):
	#@classmethod
	#def getInstance(cls, x, y, action=None, **trash):
	#	super(Bridge, cls).getInstance(x = x, y = y, action = 'default', **trash)

	def init(self):
		super(Bridge, self).init()
		origin = self.position.origin
		self.island = weakref.ref(horizons.main.session.world.get_island(origin))
		for tile in self.island().get_surrounding_tiles(origin):
			if tile is not None and self.island().path_nodes.is_road(tile.x, tile.y):
				tile.object.recalculate_orientation()

	@classmethod
	def getInstance(cls, *args, **kwargs):
		kwargs['layer'] = LAYERS.GROUND
		return super(Bridge, cls).getInstance(*args, **kwargs)
