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

import fife

import horizons.main

from horizons.util import Changelistener, Point

class Minimap(Changelistener):
	"""Draws Minimap to a specified location."""
	water_id, island_id, player_id, cam_border = range(0, 4)
	colors = { 0: (0,   0, 255),
	           1: (0, 255,   0),
	           2: (255, 0,   0),
	           3: (1,   1,   1) }

	def __init__(self, rect, renderer):
		"""
		@param rect: a Rect, where we will draw to
		@param renderer: renderer to be used. Only fife.GenericRenderer is explicitly supported.
		"""
		self.location = rect
		self.renderer = renderer

		self.coords_data = {} # save what should be displayed at (x,y) in self.location. (x, y) -> id.

		# save all GenericRendererNodes here, so they don't need to be constructed multiple times
		self.renderernodes = {}
		# pull dereferencing out of loop
		GRN = fife.GenericRendererNode
		FP = fife.Point
		for i in self.location.tupel_iter():
			self.renderernodes[ i ] = GRN( FP( *i ) )


	def draw(self, world = None):
		"""Recalculates and draws minimap of horizons.main.session.world or world"""
		# <DEBUG>
		if not horizons.main.unstable_features:
			return
		# </DEBUG>

		if world is None:
			world = horizons.main.session.world

		if not world.inited:
			return # don't draw while loading

		self.world = world # use this from now on, until next redrawing

		if not horizons.main.session.view.has_change_listener(self.update):
			horizons.main.session.view.add_change_listener(self.update)

		self._recalculate()
		self._redraw()

	def update(self):
		"""Redraw volatile elements of minimap without recalculation. Just cam view is updated."""
		self.renderer.removeAll("minimap_cam_border")
		# draw rect for current screen
		displayed_area = horizons.main.session.view.get_displayed_area()
		# TODO: consider rotation of cam
		minimap_corners_as_renderer_node = []
		for corner in displayed_area.get_corners():
			corner = list(corner)
			if corner[0] > self.world.max_x:
				corner[0] = self.world.max_x
			if corner[0] < self.world.min_x:
				corner[0] = self.world.min_x
			if corner[1] > self.world.max_y:
				corner[1] = self.world.max_y
			if corner[1] < self.world.min_y:
				corner[1] = self.world.min_y
			corner = tuple(corner)
			minimap_coords = self._world_coord_to_minimap_coord(corner)
			minimap_corners_as_renderer_node.append( fife.GenericRendererNode( \
			  fife.Point(*minimap_coords) ) )
		for i in xrange(0, 3):
			self.renderer.addLine("minimap_cam_border", minimap_corners_as_renderer_node[i], \
			                 minimap_corners_as_renderer_node[i+1], *self.colors[self.cam_border])
		# close the rect
		self.renderer.addLine("minimap_cam_border", minimap_corners_as_renderer_node[3], \
			                minimap_corners_as_renderer_node[0], *self.colors[self.cam_border])

	def _recalculate(self):
		"""Calculate which pixel of the minimap should display what. This gets saved in coords_data"""
		# calculate which area of the real map is mapped to which pixel on the minimap
		pixel_per_coord_x, pixel_per_coord_y = self._get_world_to_minimap_ratio()

		# calculate values here so we don't have to do it in the loop
		pixel_per_coord_x_half_as_int = int(pixel_per_coord_x/2)
		pixel_per_coord_y_half_as_int = int(pixel_per_coord_y/2)

		real_map_point = Point(0, 0)
		location_left = self.location.left
		location_top = self.location.top
		world_min_x = self.world.min_x
		world_min_y = self.world.min_y
		get_island = self.world.get_island
		water_id, island_id, player_id = self.water_id, self.island_id, self.player_id

		for x in xrange(0, self.location.width+1):
			for y in xrange(0, self.location.height+1):

				"""
				This code should be here, but since python can't do inlining, we have to inline
				ourselves for performance reasons (see below)
				covered_area = Rect.init_from_topleft_and_size(
				  int(x * pixel_per_coord_x)+world_min_x, \
				  int(y * pixel_per_coord_y)+world_min_y), \
				  int(pixel_per_coord_x), int(pixel_per_coord_y))
				real_map_point = covered_area.center()
				"""
				real_map_point.x = int(x*pixel_per_coord_x)+world_min_x + \
				                            pixel_per_coord_x_half_as_int
				real_map_point.y = int(y*pixel_per_coord_y)+world_min_y + \
				                            pixel_per_coord_y_half_as_int

				minimap_point = ( location_left + x, location_top + y)

				# check what's at the covered_area

				assert self.world.map_dimensions.contains(real_map_point)
				island = get_island(real_map_point)
				if island is not None:
					# this pixel is an island
					settlement = island.get_settlement(real_map_point)
					if settlement is None:
						# island without settlement
						self.coords_data[ minimap_point ] = island_id
					else:
						# pixel belongs to a player
						self.coords_data[ minimap_point ] = player_id
				else:
					self.coords_data[ minimap_point ] = water_id


	def _redraw(self):
		"""Just draws the data from coords_data"""
		colors = self.colors
		renderer = self.renderer
		renderer.removeAll("minimap") # remove old pixels

		# draw each pixel
		for tup, val in self.coords_data.iteritems():
			renderer.addPoint("minimap", self.renderernodes[tup], *colors[val])

		self.update()

	def _get_world_to_minimap_ratio(self):
		world_height = self.world.map_dimensions.height
		world_width = self.world.map_dimensions.width
		minimap_height = self.location.height
		minimap_width = self.location.width
		pixel_per_coord_x = float(world_width) / minimap_width
		pixel_per_coord_y = float(world_height) / minimap_height
		return (pixel_per_coord_x, pixel_per_coord_y)

	def _world_coord_to_minimap_coord(self, tup):
		"""Calculates which pixel in the minimap contains a coord in the real map.
		@param tup: (x, y) as ints
		@return tuple"""
		pixel_per_coord_x, pixel_per_coord_y = self._get_world_to_minimap_ratio()
		return ( int(float(tup[0] - self.world.min_x)/pixel_per_coord_x) + self.location.left, \
		         int(float(tup[1] - self.world.min_y)/pixel_per_coord_y) + self.location.top )

