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

from horizons.util import Changelistener, Rect, Point

class Minimap(Changelistener):
	"""Draws Minimap to a specified location."""

	def __init__(self, rect, renderer):
		"""
		@param rect: a Rect, where we will draw to
		@param renderer: renderer to be used. Only fife.GenericRenderer is explicitly supported.
		"""
		self.location = rect
		self.renderer = renderer

	def draw(self, world = None):
		"""Draws minimap of horizons.main.session.world or world"""
		# <DEBUG>
		if not horizons.main.unstable_features:
			return
		# </DEBUG>

		if world is None:
			world = horizons.main.session.world

		# calculate which area of the real map is mapped to which pixel on the minimap
		world_height = world.map_dimensions.height
		world_width = world.map_dimensions.width

		minimap_height = self.location.height
		minimap_width = self.location.width

		pixel_per_coord_x = float(world_width) / minimap_width
		pixel_per_coord_y = float(world_height) / minimap_height

		for x in xrange(0, self.location.width):
			for y in xrange(0, self.location.height):
				# point in the minimap covers covered_area in the real map
				covered_area = Rect( Point(int(x * pixel_per_coord_x)+world.min_x, \
				                           int(y * pixel_per_coord_y)+world.min_y), \
				                     int(pixel_per_coord_x), int(pixel_per_coord_y))

				# check what's at the covered_area
				color = ( 150, 150, 150 )

				for real_map_point in covered_area:
					assert world.map_dimensions.contains(real_map_point)
					if world.get_island(real_map_point) is not None:
						# this pixel is an island
						color = ( 255, 0, 0 )

						settlement = world.get_settlement(real_map_point)
						if settlement is not None:
							# pixel belongs to a player
							color = ( 0, 255, 0 )
						break

				# draw the point
				point = Point( self.location.left + x, self.location.bottom + y)
				node = fife.GenericRendererNode(point.to_fife_point())
				self.renderer.addPoint("minimap", node, *color)
