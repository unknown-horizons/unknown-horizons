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

import logging

class PathNodes(object):
	"""
	Abstract class; used to derive list of path nodes from, which is used for pathfinding.
	We encapsulate this code here to keep it centralised.
	"""
	log = logging.getLogger("world.pathfinding")

	# TODO: currently all paths have speed 1, since we don't have a real velocity-system yet.
	NODE_DEFAULT_SPEED = 1.0

	def __init__(self):
		# store a collection of path_nodes here. the type of this var has to be supported
		# by the pathfinding algo
		pass

class ConsumerBuildingPathNodes(PathNodes):
	"""List of path nodes for a consumer, that is a building
	Interface:
	self.nodes: {(x, y): speed, ...} of the home_building, where the collectors can walk
	"""
	def __init__(self, consumerbuilding):
		super(ConsumerBuildingPathNodes, self).__init__()
		ground_map = consumerbuilding.island.ground_map
		self.nodes = {}
		for coords in consumerbuilding.position.get_radius_coordinates(consumerbuilding.radius, include_self=False):
			if coords in ground_map and not 'coastline' in ground_map[coords].classes:
				self.nodes[coords] = self.NODE_DEFAULT_SPEED


class IslandPathNodes(PathNodes):
	"""List of path nodes for island
	Interface:
	self.nodes: List of nodes on island, where the terrain allows to be walked on
	self.road_nodes: dictionary of nodes, where a road is built on

	(un)register_road has to be called for each coord, where a road is built on (destroyed)
	reset_tile_walkablity has to be called when the terrain changes the walkability
	(e.g. building construction, a flood, or whatever)
	is_walkable rechecks the walkability status of a coordinate
	"""
	def __init__(self, island):
		super(IslandPathNodes, self).__init__()

		self.island = island

		# generate list of walkable tiles
		# we keep this up to date, so that path finding can use it and we don't have
		# to calculate it every time (rather expensive!).
		self.nodes = {}
		for coord in self.island:
			if self.is_walkable(coord):
				self.nodes[coord] = self.NODE_DEFAULT_SPEED

		# nodes where a real road is built on.
		self.road_nodes = {}

	def register_road(self, road):
		for i in road.position:
			self.road_nodes[ (i.x, i.y) ] = self.NODE_DEFAULT_SPEED

	def unregister_road(self, road):
		for i in road.position:
			del self.road_nodes[ (i.x, i.y) ]

	def is_road(self, x, y):
		"""Return if there is a road on (x, y)"""
		return (x, y) in self.road_nodes

	def is_walkable(self, coord):
		"""Check if a unit may walk on the tile specified by coord on land
		NOTE: nature tiles (trees..) are considered to be walkable (or else they could be used as
		      walls against enemies)
		@param coord: tuple: (x, y)
		"""
		tile_object = self.island.get_tile_tuple(coord)

		if tile_object is None:
			# tile is water
			return False

		# if it's not constructable, it is usually also not walkable
		# NOTE: this isn't really a clean implementation, but it works for now
		# it eliminates e.g. water and beaches, that shouldn't be walked on
		if not "constructible" in tile_object.classes:
			return False
		if tile_object.blocked and not tile_object.object.walkable:
			return False
		# every test is passed, tile is walkable
		return True

	def reset_tile_walkability(self, coord):
		"""Reset the status of the walkability of a coordinate in the list of walkable tiles
		of the island. Does not change the tile itself.
		You need to call this when a tile changes, e.g. when a building is built on it. this
		is currently done in add/remove_building
		@param coord: tuple: (x, y)"""
		actually_walkable = self.is_walkable(coord)
		# TODO: this lookup on a list is O(n), use different data structure here
		in_list = (coord in self.nodes)
		if not in_list and actually_walkable:
			self.nodes[coord] = self.NODE_DEFAULT_SPEED
		if in_list and not actually_walkable:
			del self.nodes[coord]
