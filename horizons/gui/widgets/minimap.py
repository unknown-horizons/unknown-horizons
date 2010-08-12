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

from fife import fife

from horizons.util import Point, Rect
from horizons.scheduler import Scheduler
from horizons.util.python.decorators import make_constants

class Minimap(object):
	"""A basic minimap"""
	water_id, island_id, cam_border = range(0, 3)
	colors = { 0: (190, 175, 152),
	           1: (137, 117, 87),
	           2: (1,   1,   1) }

	SHIP_DOT_UPDATE_INTERVAL = 0.5 # seconds

	@make_constants()
	def __init__(self, rect, session, renderer):
		"""
		@param rect: a Rect, where we will draw to
		@param renderer: renderer to be used. Only fife.GenericRenderer is explicitly supported.
		"""
		self.location = rect
		self.renderer = renderer
		self.session = session

		# save all GenericRendererNodes here, so they don't need to be constructed multiple times
		self.renderernodes = {}
		# pull dereferencing out of loop
		GenericRendererNode = fife.GenericRendererNode
		fife_Point = fife.Point
		for i in self.location.tuple_iter():
			self.renderernodes[ i ] = GenericRendererNode( fife_Point( *i ) )

		self.world = None

	def end(self):
		self.world = None
		self.renderernodes = None
		self.session = None
		self.renderer = None

	def draw(self, world = None):
		"""Recalculates and draws the whole minimap of self.session.world or world.
		The world you specified is reused for every operation until the next draw().
		"""
		if world is None:
			world = self.session.world
		if not world.inited:
			return # don't draw while loading
		self.world = world # use this from now on, until next redrawing

		# update cam when view updates
		if not self.session.view.has_change_listener(self.update_cam):
			self.session.view.add_change_listener(self.update_cam)

		self._recalculate()

		Scheduler().rem_all_classinst_calls(self)
		Scheduler().add_new_object(self._timed_update, self, \
		                           Scheduler().get_ticks(self.SHIP_DOT_UPDATE_INTERVAL), -1)

	def update_cam(self):
		"""Redraw camera border."""
		if self.world is None or not self.world.inited:
			return # don't draw while loading
		self.renderer.removeAll("minimap_cam_border")
		# draw rect for current screen
		displayed_area = self.session.view.get_displayed_area()
		minimap_corners_as_renderer_node = []
		for corner in displayed_area.get_corners():
			# check if the corners are outside of the screen
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

	def update(self, tup):
		"""Recalculate and redraw minimap for real world coord tup
		@param tup: (x, y)"""
		if self.world is None or not self.world.inited:
			return # don't draw while loading
		minimap_point = self._world_coord_to_minimap_coord(tup)
		world_to_minimap = self._get_world_to_minimap_ratio()
		rect = Rect.init_from_topleft_and_size(minimap_point[0], minimap_point[1], \
		                                       int(round(1/world_to_minimap[0])), \
		                                       int(round(1/world_to_minimap[1])))
		self._recalculate(rect)

	def use_overlay_icon(self, icon):
		"""Configures icon so that clicks get mapped here.
		The current gui requires, that the minimap is drawn behind an icon."""
		self.overlay_icon = icon
		icon.mapEvents({ \
		  icon.name + '/mouseClicked' : self.on_click, \
		  icon.name + '/mouseDragged' : self.on_click \
		})

	def on_click(self, event):
		"""Scrolls screen to the point, where the cursor points to on the minimap"""
		icon_pos = Point(*self.overlay_icon.getAbsolutePos())
		mouse_position = Point(event.getX(), event.getY())
		abs_mouse_position = icon_pos + mouse_position
		if not self.location.contains(abs_mouse_position):
			# mouse click was on icon but not acctually on minimap
			return
		map_coord = self._minimap_coord_to_world_coord(abs_mouse_position.to_tuple())
		self.session.view.center(*map_coord)

	@make_constants()
	def _recalculate(self, where = None):
		"""Calculate which pixel of the minimap should display what and draw it
		@param where: Rect of minimap coords. Defaults to self.location"""
		if where is None:
			where = self.location

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
		water_col, island_col = \
		         [ self.colors[i] for i in [self.water_id, self.island_id] ]
		color = None

		# loop through map coordinates, assuming (0, 0) is the origin of the minimap
		# this faciliates calculating the real world coords
		for x in xrange(where.left-self.location.left, where.left+where.width-self.location.left):
			for y in xrange(where.top-self.location.top, where.top+where.height-self.location.top):

				"""
				This code should be here, but since python can't do inlining, we have to inline
				ourselves for performance reasons
				covered_area = Rect.init_from_topleft_and_size(
				  int(x * pixel_per_coord_x)+world_min_x, \
				  int(y * pixel_per_coord_y)+world_min_y), \
				  int(pixel_per_coord_x), int(pixel_per_coord_y))
				real_map_point = covered_area.center()
				"""
				# use center of the rect that the pixel covers
				real_map_point.x = int(x*pixel_per_coord_x)+world_min_x + \
				                            pixel_per_coord_x_half_as_int
				real_map_point.y = int(y*pixel_per_coord_y)+world_min_y + \
				                            pixel_per_coord_y_half_as_int
				# we changed the minimap coords, so change back here
				minimap_point = ( location_left + x, location_top + y)

				# check what's at the covered_area
				assert self.world.map_dimensions.contains(real_map_point)
				island = get_island(real_map_point)
				if island is not None:
					# this pixel is an island
					settlement = island.get_settlement(real_map_point)
					if settlement is None:
						# island without settlement
						color = island_col
					else:
						# pixel belongs to a player
						color = settlement.owner.color.to_tuple()
				else:
					color = water_col

				self.renderer.addPoint("minimap", self.renderernodes[minimap_point], *color)

	def _timed_update(self):
		"""Regular updates for domains we can't or don't want to keep track of."""
		# update ship dots
		self.renderer.removeAll("minimap_ship")
		for ship in self.world.ship_map.itervalues():
			coord = self._world_coord_to_minimap_coord( ship().position.to_tuple() )
			color = ship().owner.color.to_tuple()
			area_to_color = Rect.init_from_topleft_and_size(coord[0], coord[1], 2, 2)
			for tup in area_to_color.tuple_iter():
				try:
					self.renderer.addPoint("minimap_ship", self.renderernodes[tup], *color)
				except KeyError:
					# this happens in rare cases, when the ship is at the border of the map,
					# and since we color an area, that's bigger than a point, it can exceed the
					# minimap's dimensions.
					pass


	## CALC UTILITY
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
		return ( \
		  int(round(float(tup[0] - self.world.min_x)/pixel_per_coord_x))+self.location.left, \
		  int(round(float(tup[1] - self.world.min_y)/pixel_per_coord_y))+self.location.top \
		)

	def _minimap_coord_to_world_coord(self, tup):
		"""Inverse to _world_coord_to_minimap_coord"""
		pixel_per_coord_x, pixel_per_coord_y = self._get_world_to_minimap_ratio()
		return ( \
		  int(round( (tup[0] - self.location.left) * pixel_per_coord_x))+self.world.min_x, \
		  int(round( (tup[1] - self.location.top)* pixel_per_coord_y))+self.world.min_y \
		)
