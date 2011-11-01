# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import horizons.main
from fife import fife

from horizons.util import Point, Rect
from horizons.scheduler import Scheduler
from horizons.util.python.decorators import bind_all

import math
from math import sin, cos

class Minimap(object):
	"""A basic minimap.

	NOTE: Rendered images are sorted by name, so use minimap_${X}_foo,
				where X of {a, b, ..} indicating the z-order
	"""
	island_id, cam_border = range(0, 2)
	# the color of the water is determined by the MINIMAP_BASE_IMAGE
	colors = { 0: (137, 117,  87),
	           1: (  1,   1,   1) }

	SHIP_DOT_UPDATE_INTERVAL = 0.5 # seconds

	MINIMAP_BASE_IMAGE = "content/gfx/misc/minmap_water.png"

	__next_minimap_id = 0
	
	def __init__(self, rect, session, renderer, targetrenderer):
		"""
		@param rect: a Rect, where we will draw to
		@param renderer: renderer to be used. Only fife.GenericRenderer is explicitly supported.
		@param targetrenderer: target renderer to be used to draw directly into an image
		"""
		self.location = rect
		self.renderer = renderer
		self.session = session
		self.rotation = 0

		self.world = None
		self.location_center = self.location.center()

		self._id = str(self.__class__.__next_minimap_id) # internal identifier, used for allocating resources
		self.__class__.__next_minimap_id += 1

		self.minimap_image = _MinimapImage( targetrenderer, horizons.main.fife.imagemanager, \
											self.MINIMAP_BASE_IMAGE )


	def end(self):
		self.world = None
		self.session = None
		self.renderer = None

	def draw(self):
		"""Recalculates and draws the whole minimap of self.session.world or world.
		The world you specified is reused for every operation until the next draw().
		"""
		if not self.world:
			self.world = self.session.world # use this from now on
		if not self.world.inited:
			return # don't draw while loading

		# update cam when view updates
		if not self.session.view.has_change_listener(self.update_cam):
			self.session.view.add_change_listener(self.update_cam)
		self.update_cam()

		# reset image
		self.renderer.removeAll("minimap_a_image"+self._id)
		self.minimap_image.reset()
		node = fife.RendererNode( fife.Point(self.location.center().x, self.location.center().y) )
		self.renderer.addImage("minimap_a_image"+self._id, node, self.minimap_image.image, False)

		self._recalculate()
		self._timed_update()

		Scheduler().rem_all_classinst_calls(self)
		Scheduler().add_new_object(self._timed_update, self, \
		                           Scheduler().get_ticks(self.SHIP_DOT_UPDATE_INTERVAL), -1)


	def update_cam(self):
		"""Redraw camera border."""
		if self.world is None or not self.world.inited:
			return # don't draw while loading
		self.renderer.removeAll("minimap_b_cam_border"+self._id)
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
			minimap_coords = self._get_rotated_coords( self._world_coord_to_minimap_coord(corner))
			minimap_corners_as_renderer_node.append( fife.RendererNode( \
			  fife.Point(*minimap_coords) ) )
		for i in xrange(0, 4):
			self.renderer.addLine("minimap_b_cam_border"+self._id, minimap_corners_as_renderer_node[i], \
			                 minimap_corners_as_renderer_node[ (i+1) % 4], *self.colors[self.cam_border])

	def update(self, tup):
		"""Recalculate and redraw minimap for real world coord tup
		@param tup: (x, y)"""
		if self.world is None or not self.world.inited:
			return # don't draw while loading
		minimap_point = self._get_rotated_coords(self._world_coord_to_minimap_coord(tup))
		world_to_minimap = self._get_world_to_minimap_ratio()
		rect = Rect.init_from_topleft_and_size(minimap_point[0], minimap_point[1], \
		                                       int(round(1/world_to_minimap[0])) + 1, \
		                                       int(round(1/world_to_minimap[1])) + 1)
		self._recalculate(rect)

	def use_overlay_icon(self, icon):
		"""Configures icon so that clicks get mapped here.
		The current gui requires, that the minimap is drawn behind an icon."""
		self.overlay_icon = icon
		icon.mapEvents({ \
		  icon.name + '/mousePressed' : self.on_click, \
		  icon.name + '/mouseDragged' : self.on_click \
		})

	def on_click(self, event):
		"""Scrolls screen to the point, where the cursor points to on the minimap"""
		# TODO: send ships via minimap
		icon_pos = Point(*self.overlay_icon.getAbsolutePos())
		mouse_position = Point(event.getX(), event.getY())
		abs_mouse_position = icon_pos + mouse_position
		if not self.location.contains(abs_mouse_position):
			# mouse click was on icon but not actually on minimap
			return
		abs_mouse_position = self._get_from_rotated_coords (abs_mouse_position.to_tuple())
		map_coord = self._minimap_coord_to_world_coord(abs_mouse_position)
		self.session.view.center(*map_coord)

	def _recalculate(self, where = None):
		"""Calculate which pixel of the minimap should display what and draw it
		@param where: Rect of minimap coords. Defaults to self.location"""
		if where is None:
			where = self.location
			self.minimap_image.rendertarget.removeAll("minimap")

		# calculate which area of the real map is mapped to which pixel on the minimap
		pixel_per_coord_x, pixel_per_coord_y = self._get_world_to_minimap_ratio()

		# calculate values here so we don't have to do it in the loop
		pixel_per_coord_x_half_as_int = int(pixel_per_coord_x/2)
		pixel_per_coord_y_half_as_int = int(pixel_per_coord_y/2)

		real_map_point = Point(0, 0)
		world_min_x = self.world.min_x
		world_min_y = self.world.min_y
		get_island = self.world.get_island
		island_col = self.colors[self.island_id]
		location_left = self.location.left
		location_top = self.location.top
		
		rt = self.minimap_image.rendertarget
		self.minimap_image.set_drawing_enabled()

		# loop through map coordinates, assuming (0, 0) is the origin of the minimap
		# this faciliates calculating the real world coords
		for x in xrange(where.left-self.location.left, where.left+where.width-self.location.left):
			# Optimisation: remember last island
			last_island = None
			island = None
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
				real_map_point_tuple = (real_map_point.x, real_map_point.y)

				# check what's at the covered_area
				if last_island is not None and real_map_point_tuple in last_island.ground_map:
					island = last_island
				else:
					island = get_island(real_map_point)
				if island is not None:
					last_island = island
					# this pixel is an island
					settlement = island.get_settlement(real_map_point)
					if settlement is None:
						# island without settlement
						color = island_col
					else:
						# pixel belongs to a player
						color = settlement.owner.color.to_tuple()
				else:
					continue

				# _get_rotated_coords has been inlined here
				rot_x, rot_y = self._rotate( (location_left + x, location_top + y), self._rotations)
				rt.addPoint("minimap", fife.Point(rot_x - location_left, rot_y - location_top) , *color)


	def _timed_update(self):
		"""Regular updates for domains we can't or don't want to keep track of."""
		# update ship dots
		self.renderer.removeAll("minimap_b_ship"+self._id)
		for ship in self.world.ship_map.itervalues():
			if not ship():
				continue
			coord = self._world_coord_to_minimap_coord( ship().position.to_tuple() )
			color = ship().owner.color.to_tuple()
			area_to_color = Rect.init_from_topleft_and_size(coord[0], coord[1], 3, 3)
			for tup in area_to_color.tuple_iter():
				try:
					node = fife.RendererNode(fife.Point(*self._get_rotated_coords(tup)))
					self.renderer.addPoint("minimap_b_ship"+self._id, node, *color)
				except KeyError:
					# this happens in rare cases, when the ship is at the border of the map,
					# and since we color an area, that's bigger than a point, it can exceed the
					# minimap's dimensions.
					pass

	def rotate_right (self):
		# keep track of rotation at any time, but only apply
		# if it's actually used
		self.rotation += 1
		self.rotation %= 4
		self.update_cam()
		if horizons.main.fife.get_uh_setting("MinimapRotation"):
			self.draw()

	def rotate_left (self):
		# see above
		self.rotation -= 1
		self.rotation %= 4
		self.update_cam()
		if horizons.main.fife.get_uh_setting("MinimapRotation"):
			self.draw()

	## CALC UTILITY

	_rotations = { 0 : 0,
	               1 : 3 * math.pi / 2,
	               2 : math.pi,
	               3 : math.pi / 2
	               }
	def _get_rotated_coords (self, tup):
		return self._rotate(tup, self._rotations)

	_from_rotations = { 0 : 0,
	                    1 : math.pi / 2,
	                    2 : math.pi,
	                    3 : 3 * math.pi / 2
	                    }
	def _get_from_rotated_coords (self, tup):
		return self._rotate (tup, self._from_rotations)

	def _rotate (self, tup, rotations):
		if not horizons.main.fife.get_uh_setting("MinimapRotation"):
			return tup
		else:
			rotation = rotations[ self.rotation ]

			x = tup[0]
			y = tup[1]
			x -= self.location_center.x
			y -= self.location_center.y

			new_x = x * cos(rotation) - y * sin(rotation)
			new_y = x * sin(rotation) + y * cos(rotation)

			new_x += self.location_center.x
			new_y += self.location_center.y
			#some points may get out of range
			new_x = max (self.location.left, new_x)
			new_x = min (self.location.right, new_x)
			new_y = max (self.location.top, new_y)
			new_y = min (self.location.bottom, new_y)
			tup = int(new_x), int(new_y)
			return tup

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

class _MinimapImage(object):
	"""Encapsulates handling of fife Image.
	Provides:
	- self.image: instance of fife.Image
	- self.rendertarget: instance of fife.RenderTarget
	"""
	def __init__(self, targetrenderer, imagemanager, image_file_path):
		self.imagemanager = imagemanager
		self.targetrenderer = targetrenderer
		self.image_file_path = image_file_path
		self.image = self.imagemanager.load( self.image_file_path )
		self.rendertarget = targetrenderer.createRenderTarget( self.image )

	def reset(self):
		"""Reset image to original image"""
		# reload
		self.imagemanager.reload( self.image_file_path )
		self.image = self.imagemanager.get( self.image_file_path )
		
	def set_drawing_enabled(self):
		self.targetrenderer.setRenderTarget( self.image_file_path, False, 0 )

bind_all(Minimap)
