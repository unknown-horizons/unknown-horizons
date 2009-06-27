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
import logging

from horizons.util import Point

class PathNodes(object):
	"""
	Abstract class; used to derive list of path nodes from, which is used for pathfinding.
	We encapsulate this code here to keep it centralised.
	"""
	log = logging.getLogger("world.pathfinding")
	def __init__(self):
		# store a collection of path_nodes here. the type of this var has to be supported
		# by the pathfinding algo
		pass

class ConsumerBuildingPathNodes(PathNodes):
	"""List of path nodes for a consumer, that is a building"""
	def __init__(self, consumerbuilding):
		super(ConsumerBuildingPathNodes, self).__init__()
		self.nodes = consumerbuilding.position.get_radius_coordinates( \
			consumerbuilding.radius)

class IslandPathNodes(PathNodes):
	"""List of path nodes for island"""
	def __init__(self, island):
		super(IslandPathNodes, self).__init__()

		self.island = weakref.ref(island)

		# generate list of walkable tiles
		# we keep this up to date, so that path finding can use it and we don't have
		# to calculate it every time (rather expensive!).
		self.walkable_nodes = []
		for i in self.island():
			if self.is_walkable(i, False):
				self.walkable_nodes.append(i)

		# nodes where a real road is built on.
		self.road_nodes = {}

	def register_road(self, road):
		# TODO: currently all paths have speed 1, since we don't have a real
		# velocity-system yet.
		for i in road.position:
			self.road_nodes[ (i.x, i.y) ] = 1

	def unregister_road(self, road):
		for i in road.position:
			del self.road_nodes[ (i.x, i.y) ]

	def is_walkable(self, coord, check_coord_is_on_island = True):
		"""Check if a unit may walk on the tile specified by coord
		@param coord: tuple: (x, y)
		@param check_coord_is_on_island: bool, wether to check if coord is on this island
		"""
		if check_coord_is_on_island:
			if not coord in self.island().get_coordinates():
				return False

		tile_object = self.island().get_tile(Point(*coord))
		# if it's not constructible, it is usually also not walkable
		# NOTE: this isn't really a clean implementation, but it works for now
		# it eliminates e.g. water and beaches, that shouldn't be walked on
		if not "constructible" in tile_object.classes:
			return False
		if tile_object.blocked and not tile_object.object.is_part_of_nature():
			return False
		return True

	def reset_tile_walkability(self, coord):
		"""Reset the status of the walkability of a coordinate in the list of walkable tiles
		of the island. Does not change the tile itself.
		You need to call this when a tile changes, e.g. when a building is built on it. this
		is currently done in add/remove_building
		@param coord: tuple: (x, y)"""
		acctually_walkable = self.is_walkable(coord)
		self.log.debug("reset tile walkability on %s %s to %s", \
									 coord[0], coord[1], acctually_walkable)
		in_list = (coord in self.walkable_nodes)
		if not in_list and acctually_walkable:
			self.walkable_nodes.append(coord)
		if in_list and not acctually_walkable:
			self.walkable_nodes.remove(coord)
