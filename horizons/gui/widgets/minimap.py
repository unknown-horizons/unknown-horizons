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


import itertools
import math
from math import cos, sin
from typing import List

from fife import fife

import horizons.globals
from horizons.command.unit import Act
from horizons.component.namedcomponent import NamedComponent
from horizons.extscheduler import ExtScheduler
from horizons.messaging import SettingChanged
from horizons.util.shapes import Circle, Point, Rect


def iter_minimap_points(location, world, island_color, water_color, area=None):
	"""Return an iterator over the pixels of a minimap of the given world.

	For every pixel, a tuple ((x, y), (r, g, b)) is returned. These are the x and y
	coordinated and the color of the pixel in RGB.

	If `area` is set, it's supposed to be a part of `location`, that is to be
	returned.

	This function is not used anymore in the in-game minimap, but it is necessary
	for the minimap preview.
	"""

	if area is None:
		area = location

	# calculate which area of the real map is mapped to which pixel on the minimap
	world_dimensions = (world.map_dimensions.width, world.map_dimensions.height)
	minimap_dimensions = (location.width, location.height)
	pixel_per_coord_x = world.map_dimensions.width / location.width
	pixel_per_coord_y = world.map_dimensions.height / location.height

	# calculate values here so we don't have to do it in the loop
	pixel_per_coord_x_half_as_int = int(pixel_per_coord_x / 2)
	pixel_per_coord_y_half_as_int = int(pixel_per_coord_y / 2)

	world_min_x = world.min_x
	world_min_y = world.min_y
	full_map = world.full_map

	# loop through map coordinates, assuming (0, 0) is the origin of the minimap
	# this facilitates calculating the real world coords
	for x in range(area.left - location.left, area.left + area.width - location.left):
		for y in range(area.top - location.top, area.top + area.height - location.top):
			"""
			This code should be here, but since python can't do inlining, we have to inline
			ourselves for performance reasons
			covered_area = Rect.init_from_topleft_and_size(
			  int(x * pixel_per_coord_x)+world_min_x,
			  int(y * pixel_per_coord_y)+world_min_y),
			  int(pixel_per_coord_x), int(pixel_per_coord_y))
			real_map_point = covered_area.center
			"""
			# use center of the rect that the pixel covers
			real_map_x = int(x * pixel_per_coord_x) + world_min_x + pixel_per_coord_x_half_as_int
			real_map_y = int(y * pixel_per_coord_y) + world_min_y + pixel_per_coord_y_half_as_int
			real_map_coords = (real_map_x, real_map_y)

			# check what's at the covered_area
			if real_map_coords in full_map:
				# this pixel is an island
				tile = full_map[real_map_coords]
				settlement = tile.settlement
				if settlement is None:
					# island without settlement
					if tile.id <= 0:
						color = water_color
					else:
						color = island_color
				else:
					# pixel belongs to a player
					color = settlement.owner.color.to_tuple()
			else:
				color = water_color

			yield ((x, y), color)


class Minimap:
	"""A basic minimap.

	USAGE:
	Minimap can be drawn via GenericRenderer on an arbitrary position (determined by rect in ctor)
	or
	via Pychan Icon. In this case, the rect parameter only determines the size, the
	Minimap will scroll by default on clicks, overwrite on_click if you don't want that.

	TODO:
	* Remove renderer when used in icon node
	* Clear up distinction of coords where the minimap image or screen is the origin
	* Create a minimap tag for pychan
	** Handle clicks, remove overlay icon
	"""
	COLORS = {
		"island":    (137, 117,  87),
		"cam":       (  1,   1,   1),
		"water":     (198, 188, 165),
		"highlight": (255,   0,   0),  # for events
	}

	WAREHOUSE_IMAGE = "content/gui/icons/minimap/warehouse.png"
	SHIP_NEUTRAL = "content/gui/icons/minimap/ship_neutral.png"
	SHIP_PIRATE = "content/gui/icons/minimap/pirate.png"
	GROUND_UNIT_IMAGE = "content/gui/icons/minimap/groundunit.png"

	SHIP_DOT_UPDATE_INTERVAL = 0.5 # seconds

	# Alpha-ordering determines the order:
	RENDER_NAMES = {
	  "background" : "c",
	  "base" : "d",  # islands, etc.
	  "warehouse" : "e",
	  "ship" : "f",
	  "cam" : "g",
	  "ship_route" : "h",
	  "highlight" : "l",
	  }

	__minimap_id_counter = itertools.count()
	__ship_route_counter = itertools.count()
	# all active instances
	_instances = [] # type: List[Minimap]

	_dummy_fife_point = fife.Point(0, 0) # use when you quickly need a temporary point

	def __init__(self, position, session, view, targetrenderer, imagemanager, renderer=None, world=None,
	             cam_border=True, use_rotation=True, on_click=None, preview=False, tooltip=None):
		"""
		@param position: a Rect or a Pychan Icon, where we will draw to
		@param world: World object or fake thereof
		@param view: View object for cam control. Can be None to disable this
		@param renderer: renderer to be used if position isn't an icon
		@param targetrenderer: fife target renderer for drawing on icons
		@param imagemanager: fife imagemanager for drawing on icons
		@param cam_border: boolean, whether to draw the cam border
		@param use_rotation: boolean, whether to use rotation (it must also be enabled in the settings)
		@param on_click: function taking 1 argument or None for scrolling
		@param preview: flag, whether to only show the map as preview
		@param tooltip: always show this tooltip when cursor hovers over minimap

		NOTE: Preview generation in a different process overwrites this method.
		"""
		if isinstance(position, Rect):
			self.location = position
			self.renderer = renderer
		else: # assume icon
			self.location = Rect.init_from_topleft_and_size(0, 0, position.width, position.height)
			self.icon = position
			self.use_overlay_icon(self.icon)

		# FIXME PY3 width / height of icon is sometimes zero. Why?
		if self.location.height == 0 or self.location.width == 0:
			self.location = Rect.init_from_topleft_and_size(0, 0, 128, 128)

		self.session = session
		self.world = world
		self.view = view
		self.rotation = 0
		self.fixed_tooltip = tooltip

		self.click_handler = on_click if on_click is not None else self.default_on_click

		self.cam_border = cam_border
		self.use_rotation = use_rotation
		self.preview = preview

		self.location_center = self.location.center

		self._id = str(next(self.__class__.__minimap_id_counter)) # internal identifier, used for allocating resources

		self._image_size_cache = {} # internal detail

		self.imagemanager = imagemanager

		self.minimap_image = _MinimapImage(self, targetrenderer)

		self._rotation_setting = horizons.globals.fife.get_uh_setting("MinimapRotation")
		if self.use_rotation:
			SettingChanged.subscribe(self._on_setting_changed)

		if self.world:
			self._update_transform_values()


	def end(self):
		self.disable()
		self.world = None
		self.session = None
		self.renderer = None
		if self.use_rotation:
			SettingChanged.unsubscribe(self._on_setting_changed)

	def disable(self):
		"""Due to the way the minimap works, there isn't really a show/hide,
		but you can disable it with this and enable again with draw().
		Stops all updates."""
		ExtScheduler().rem_all_classinst_calls(self)
		if self.view is not None:
			self.view.discard_change_listener(self.update_cam)

		if self in self.__class__._instances:
			self.__class__._instances.remove(self)

	def draw(self):
		"""Recalculates and draws the whole minimap of self.session.world or world.
		The world you specified is reused for every operation until the next draw().
		"""
		if self.world is None and self.session.world is not None:
			self.world = self.session.world # in case minimap has been constructed before the world
			self._update_transform_values()
		if not self.world.inited:
			return # don't draw while loading

		self.__class__._instances.append(self)

		# update cam when view updates
		if self.view is not None and not self.view.has_change_listener(self.update_cam):
			self.view.add_change_listener(self.update_cam)

		if not hasattr(self, "icon"):
			# add to global generic renderer with id specific to this instance
			self.renderer.removeAll("minimap_image" + self._id)
			self.minimap_image.reset()
			# NOTE: this is for the generic renderer interface, the offrenderer has slightly different methods
			node = fife.RendererNode(fife.Point(self.location.center.x, self.location.center.y))
			self.renderer.addImage("minimap_image" + self._id, node, self.minimap_image.image, False)

		else:
			# attach image to pychan icon (recommended)
			self.minimap_image.reset()
			self.icon.image = fife.GuiImage(self.minimap_image.image)

		self.update_cam()
		self._recalculate()
		if not self.preview:
			self._timed_update(force=True)
			ExtScheduler().rem_all_classinst_calls(self)
			ExtScheduler().add_new_object(self._timed_update, self,
			                              self.SHIP_DOT_UPDATE_INTERVAL, -1)

	def draw_data(self, data):
		"""Display data from dump_data"""
		# only icon mode for now
		self.minimap_image.reset()
		self.icon.image = fife.GuiImage(self.minimap_image.image)

		self.minimap_image.set_drawing_enabled()
		rt = self.minimap_image.rendertarget
		render_name = self._get_render_name("base")
		draw_point = rt.addPoint
		point = fife.Point()

		for x, y, r, g, b in data:
			point.set(x, y)
			draw_point(render_name, point, r, g, b)

	def _get_render_name(self, key):
		return self.RENDER_NAMES[key] + self._id

	def update_cam(self):
		"""Redraw camera border."""
		if not self.cam_border or self.view is None: # needs view
			return
		if self.world is None or not self.world.inited:
			return # don't draw while loading
		use_rotation = self._get_rotation_setting()
		self.minimap_image.set_drawing_enabled()
		self.minimap_image.rendertarget.removeAll(self._get_render_name("cam"))
		# draw rect for current screen
		displayed_area = self.view.get_displayed_area()
		minimap_corners_as_point = []
		for (x, y) in displayed_area:
			coords = self._world_to_minimap((x, y))
			minimap_corners_as_point.append(fife.Point(coords[0], coords[1]))

		for i in range(0, 4):
			self.minimap_image.rendertarget.addLine(self._get_render_name("cam"),
			                                        minimap_corners_as_point[i],
			                                        minimap_corners_as_point[(i + 1) % 4],
			                                                         *self.COLORS["cam"])

	@classmethod
	def update(cls, tup):
		for minimap in cls._instances:
			minimap._update(tup)

	def _update(self, tup):
		"""Recalculate and redraw minimap for real world coord tup
		@param tup: (x, y)"""
		if self.world is None or not self.world.inited:
			return # don't draw while loading
		minimap_point = self._world_to_minimap(tup)
		world_to_minimap = self._world_to_minimap_ratio
		# TODO: remove this remnant of the old implementation, perhaps by refactoring recalculate()
		minimap_point = (
		  minimap_point[0] + self.location.left,
		  minimap_point[1] + self.location.top,
		)
		rect = Rect.init_from_topleft_and_size(minimap_point[0], minimap_point[1],
								                           int(round(1 / world_to_minimap[0])) + 1,
								                           int(round(1 / world_to_minimap[1])) + 1)
		self._recalculate(rect)

	def use_overlay_icon(self, icon):
		"""Configures icon so that clicks get mapped here.
		The current gui requires, that the minimap is drawn behind an icon."""
		self.overlay_icon = icon
		icon.mapEvents({
			icon.name + '/mousePressed' : self._on_click,
			icon.name + '/mouseDragged' : self._on_drag,
			icon.name + '/mouseEntered' : self._mouse_entered,
			icon.name + '/mouseMoved' : self._mouse_moved,
			icon.name + '/mouseExited' : self._mouse_exited,
		})

	def default_on_click(self, event, drag):
		"""Handler for clicks (pressed and dragged)
		Scrolls screen to the point, where the cursor points to on the minimap.
		Overwrite this method to your convenience.
		"""
		if self.preview:
			return # we don't do anything in this mode
		button = event.getButton()
		map_coords = event.map_coords
		if button == fife.MouseEvent.RIGHT:
			if drag:
				return
			for i in self.session.selected_instances:
				if i.movable:
					Act(i, *map_coords).execute(self.session)
		elif button == fife.MouseEvent.LEFT:
			if self.view is None:
				print("Warning: Can't handle minimap clicks since we have no view object")
			else:
				self.view.center(*map_coords)

	def _on_click(self, event):
		if self.world is not None: # supply world coords if there is a world
			event.map_coords = self._get_event_coords(event)
			if event.map_coords:
				self.click_handler(event, drag=False)
		else:
			self.click_handler(event, drag=True)

	def _on_drag(self, event):
		if self.world is not None: # supply world coords if there is a world
			event.map_coords = self._get_event_coords(event)
			if event.map_coords:
				self.click_handler(event, drag=True)
		else:
			self.click_handler(event, drag=True)

	def _get_event_coords(self, event):
		"""Returns position of event as uh map coordinate tuple or None"""
		mouse_position = Point(event.getX(), event.getY())
		if not hasattr(self, "icon"):
			icon_pos = Point(*self.overlay_icon.getAbsolutePos())
			abs_mouse_position = icon_pos + mouse_position
			if not self.location.contains(abs_mouse_position):
				# mouse click was on icon but not actually on minimap
				return None
		return self._minimap_to_world((event.getX(), event.getY()))

	def _mouse_entered(self, event):
		self._show_tooltip(event)

	def _mouse_moved(self, event):
		self._show_tooltip(event)

	def _mouse_exited(self, event):
		if hasattr(self, "icon"): # only supported for icon mode atm
			self.icon.hide_tooltip()

	def _show_tooltip(self, event):
		if not hasattr(self, "icon"):
			# only supported for icon mode atm
			return
		if self.fixed_tooltip is not None:
			self.icon.helptext = self.fixed_tooltip
			self.icon.position_tooltip(event)
			#self.icon.show_tooltip()
		else:
			coords = self._get_event_coords(event)
			if not coords: # no valid/relevant event location
				self.icon.hide_tooltip()
				return

			tile = self.world.get_tile(Point(*coords))
			if tile is not None and tile.settlement is not None:
				new_helptext = tile.settlement.get_component(NamedComponent).name
				if self.icon.helptext != new_helptext:
					self.icon.helptext = new_helptext
					self.icon.show_tooltip()
				else:
					self.icon.position_tooltip(event)
			else:
				# mouse not over relevant part of the minimap
				self.icon.hide_tooltip()

	def highlight(self, tup, factor=1.0, speed=1.0, finish_callback=None, color=(0, 0, 0)):
		"""Try to get the users attention on a certain point of the minimap.
		@param tup: world coords
		@param factor: float indicating importance of event
		@param speed: animation speed as factor
		@param finish_callback: executed when animation finishes
		@param color: color of anim, (r,g,b), r,g,b of [0,255]
		@return duration of full animation in seconds"""
		tup = self._world_to_minimap(tup)

		# grow the circle from MIN_RAD to MAX_RAD and back with STEPS steps, where the
		# interval between steps is INTERVAL seconds
		MIN_RAD = int( 3 * factor) # pixel
		MAX_RAD = int(12 * factor) # pixel
		STEPS = int(20 * factor)
		INTERVAL = (math.pi / 16) * factor

		def high(i=0):
			i += 1
			render_name = self._get_render_name("highlight") + str(tup)
			self.minimap_image.set_drawing_enabled()
			self.minimap_image.rendertarget.removeAll(render_name)
			if i > STEPS:
				if finish_callback:
					finish_callback()
				return
			part = i # grow bigger
			if i > STEPS // 2: # after the first half
				part = STEPS - i  # become smaller

			radius = MIN_RAD + int((float(part) / (STEPS // 2)) * (MAX_RAD - MIN_RAD))

			draw_point = self.minimap_image.rendertarget.addPoint
			for x, y in Circle(Point(*tup), radius=radius).get_border_coordinates():
				draw_point(render_name, fife.Point(x, y), *color)

			ExtScheduler().add_new_object(lambda : high(i), self, INTERVAL, loops=1)

		high()
		return STEPS * INTERVAL

	def show_unit_path(self, unit):
		"""Show the path a unit is moving along"""
		path = unit.path.path
		if path is None: # show at least the position
			path = [unit.position.to_tuple()]

		# the path always contains the full path, the unit might be somewhere in it
		position_of_unit_in_path = 0
		unit_pos = unit.position.to_tuple()
		for i, pos in enumerate(path):
			if pos == unit_pos:
				position_of_unit_in_path = i
				break

		# display units one ahead if possible, it looks nicer if the unit is moving
		if len(path) > 1 and position_of_unit_in_path + 1 < len(path):
			position_of_unit_in_path += 1
		path = path[position_of_unit_in_path:]

		# draw every step-th coord
		step = 1
		relevant_coords = [path[0]]
		for i in range(step, len(path), step):
			relevant_coords.append(path[i])
		relevant_coords.append(path[-1])

		# get coords, actual drawing
		use_rotation = self._get_rotation_setting()
		self.minimap_image.set_drawing_enabled()
		p = fife.Point(0, 0)
		render_name = self._get_render_name("ship_route") + str(next(self.__class__.__ship_route_counter))
		color = unit.owner.color.to_tuple()
		last_coord = None
		draw_point = self.minimap_image.rendertarget.addPoint
		for i in relevant_coords:
			coord = self._world_to_minimap(i)
			if last_coord is not None and \
			   sum(abs(last_coord[i] - coord[i]) for i in (0, 1)) < 2:  # 2 is min dist in pixels
				continue
			last_coord = coord
			p.x = coord[0]
			p.y = coord[1]
			draw_point(render_name, p, *color)

		def cleanup():
			self.minimap_image.set_drawing_enabled()
			self.minimap_image.rendertarget.removeAll(render_name)

		speed = 1.0 + math.sqrt(5) / 2
		self.highlight(path[-1], factor=0.4, speed=speed, finish_callback=cleanup, color=color)

		return True

	def _recalculate(self, where=None):
		"""Calculate which pixel of the minimap should display what and draw it
		@param where: Rect of minimap coords. Defaults to self.location
		"""
		self.minimap_image.set_drawing_enabled()

		rt = self.minimap_image.rendertarget
		render_name = self._get_render_name("base")

		if where is None:
			rt.removeAll(render_name)

		# Is this really worth it?
		draw_point = rt.addPoint

		fife_point = fife.Point(0, 0)
		island_color = self.COLORS["island"]
		water_color = self.COLORS["water"]
		full_map = self.world.full_map

		for (x, y) in self.iter_points(where):

			real_map_coords = self._minimap_to_world((x, y))

			# check what's at the covered_area
			if real_map_coords in full_map:
				# this pixel is an island
				tile = full_map[real_map_coords]
				settlement = tile.settlement
				if settlement is None:
					# island without settlement
					if tile.id <= 0:
						color = water_color
					else:
						color = island_color
				else:
					# pixel belongs to a player
					color = settlement.owner.color.to_tuple()
			else:
				color = water_color
			fife_point.set(x, y)
			draw_point(render_name, fife_point, *color)

	def _timed_update(self, force=False):
		"""Regular updates for domains we can't or don't want to keep track of."""
		# OPTIMIZATION NOTE: There can be pretty many ships.
		# Don't rely on the loop being rarely executed!
		# update ship icons
		self.minimap_image.set_drawing_enabled()
		render_name = self._get_render_name("ship")
		self.minimap_image.rendertarget.removeAll(render_name)
		use_rotation = self._get_rotation_setting()
		# Make use of these dummy points instead of creating fife.Point instances
		# (which are consuming a lot of resources).
		dummy_point0 = fife.Point(0, 0)
		dummy_point1 = fife.Point(0, 0)
		for ship in self.world.ships:
			if not ship.in_ship_map:
				continue # no fisher ships, etc
			coord = self._world_to_minimap(ship.position.to_tuple())
			color = ship.owner.color.to_tuple()
			# set correct icon
			if ship.owner is self.session.world.pirate:
				ship_icon_path = self.__class__.SHIP_PIRATE
			else:
				ship_icon_path = self.__class__.SHIP_NEUTRAL
			ship_icon = self.imagemanager.load(ship_icon_path)
			dummy_point1.set(coord[0], coord[1])
			self.minimap_image.rendertarget.addImage(render_name, dummy_point1, ship_icon)
			if ship.owner.regular_player:
				# add the 'flag' over the ship icon, with the color of the owner
				dummy_point0.set(coord[0] - 5, coord[1] - 5)
				dummy_point1.set(coord[0], coord[1] - 5)
				self.minimap_image.rendertarget.addLine(render_name, dummy_point0,
									dummy_point1, color[0], color[1], color[2])
				dummy_point0.set(coord[0] - 6, coord[1] - 6)
				dummy_point1.set(coord[0], coord[1] - 6)
				self.minimap_image.rendertarget.addLine(render_name, dummy_point0,
									dummy_point1, color[0], color[1], color[2])
				dummy_point0.set(coord[0] - 4, coord[1] - 4)
				dummy_point1.set(coord[0], coord[1] - 4)
				self.minimap_image.rendertarget.addLine(render_name, dummy_point0,
									dummy_point1, color[0], color[1], color[2])
				# add black border around the flag
				dummy_point0.set(coord[0] - 6, coord[1] - 7)
				dummy_point1.set(coord[0], coord[1] - 7)
				self.minimap_image.rendertarget.addLine(render_name, dummy_point0, dummy_point1, 0, 0, 0)
				dummy_point0.set(coord[0] - 4, coord[1] - 3)
				dummy_point1.set(coord[0], coord[1] - 4)
				self.minimap_image.rendertarget.addLine(render_name, dummy_point0, dummy_point1, 0, 0, 0)
				dummy_point0.set(coord[0] - 6, coord[1] - 7)
				dummy_point1.set(coord[0] - 4, coord[1] - 3)
				self.minimap_image.rendertarget.addLine(render_name, dummy_point0, dummy_point1, 0, 0, 0)

			# TODO: nicer selected view
			dummy_point0.set(coord[0], coord[1])
			draw_point = self.minimap_image.rendertarget.addPoint
			if ship in self.session.selected_instances:
				draw_point(render_name, dummy_point0, *Minimap.COLORS["water"])
				for x_off, y_off in ((-2,  0),
				                     (+2,  0),
				                     ( 0, -2),
				                     ( 0, +2)):
					dummy_point1.set(coord[0] + x_off, coord[1] + y_off)
					draw_point(render_name, dummy_point1, *color)

		# draw settlement warehouses if something has changed
		settlements = self.world.settlements
		# save only worldids as to not introduce actual coupling
		cur_settlements = set(i.worldid for i in settlements)
		if force or \
		   (not hasattr(self, "_last_settlements") or cur_settlements != self._last_settlements):
			# update necessary
			warehouse_render_name = self._get_render_name("warehouse")
			self.minimap_image.rendertarget.removeAll(warehouse_render_name)
			for settlement in settlements:
				coord = settlement.warehouse.position.center.to_tuple()
				coord = self._world_to_minimap(coord)
				self._update_image(self.__class__.WAREHOUSE_IMAGE,
				                   warehouse_render_name,
				                   coord)
			self._last_settlements = cur_settlements

	def _update_image(self, img_path, name, coord_tuple):
		"""Updates image as part of minimap (e.g. when it has moved)"""
		img = self.imagemanager.load(img_path)

		size_tuple = self._image_size_cache.get(img_path)
		if size_tuple is None:
			ratio = sum(self._world_to_minimap_ratio) / 2.0
			ratio = max(1.0, ratio)
			size_tuple = int(img.getWidth() / ratio), int(img.getHeight() / ratio)
			self._image_size_cache[img_path] = size_tuple
		new_width, new_height = size_tuple
		p = self.__class__._dummy_fife_point
		p.set(*coord_tuple)
		# resizeImage also means draw
		self.minimap_image.rendertarget.resizeImage(name, p, img, new_width, new_height)


	def rotate_right(self):
		# keep track of rotation at any time, but only apply
		# if it's actually used
		self.transform.update_rotation(-1)
		if self._get_rotation_setting():
			self.draw()

	def rotate_left(self):
		# see above
		self.transform.update_rotation(1)
		if self._get_rotation_setting():
			self.draw()


	def _get_rotation_setting(self):
		return self.use_rotation and self._rotation_setting


	def _on_setting_changed(self, message):
		if message.setting_name == "MinimapRotation":
			self._rotation_setting = message.new_value
			self.transform.set_use_rotation(self._get_rotation_setting())
			self.draw()


class _MinimapTransform:

	def __init__(self, world_dimensions, location, rotation=0, use_rotation=True):
		self.world_dimensions = worlds_dimensions
		self.location = location
		self.rotation = rotation
		self.use_rotation = use_rotation

	def update_rotation(self, direction):
		self.rotation += direction
		self.rotation %= 4
		self._update_transform_values()

	def set_use_rotation(self, use_rotation):
		self.use_rotation = use_rotation
		self._update_transform_values()

	def world_to_minimap(self, coords):
		"""Complete coord transformation, batteries included."""

		x, y = coords

		# center on 0,0
		x -= self.world.map_dimensions.center.x
		y -= self.world.map_dimensions.center.y

		# rotate
		x_ = x * self._cos_rotation - y * self._sin_rotation
		y_ = x * self._sin_rotation + y * self._cos_rotation

		# scale to minimap size and translate to correct position
		x = x_ * self._world_minimap_ratio_x + self.location.center.x
		y = y_ * self._world_minimap_ratio_y + self.location.center.y

		return (int(x), int(y))

	def minimap_to_world(self, coords):
		x, y = coords

		# center on 0,0 and scale to world size
		x = (x - self.location.center.x) / self._world_minimap_ratio_x
		y = (y - self.location.center.y) / self._world_minimap_ratio_y

		# rotate
		x_ =  x * self._cos_rotation + y * self._sin_rotation
		y_ = -x * self._sin_rotation + y * self._cos_rotation

		# undo centering and translate to correct position
		x = x_ + self.world.map_dimensions.center.x
		y = y_ + self.world.map_dimensions.center.y


		return (int(x), int(y))


	def _update_parameters(self):
		""" Update the transformation parameters.
		This is only executed at the begin and when the map rotation changes.
		This should improve performance """
		self._rotation_rad = self._get_rotation()
		self._sin_rotation = sin(self._rotation_rad)
		self._cos_rotation = cos(self._rotation_rad)

		self._scale_correction = max(abs(self._sin_rotation), abs(self._cos_rotation))

		self._world_minimap_ratio_x = self.location.width / self.world.map_dimensions.width * self._scale_correction
		self._world_minimap_ratio_y = self.location.height / self.world.map_dimensions.height * self._scale_correction




	def _get_rotation(self):
		if self.use_rotation:
			return (-self.rotation - 0.5) * math.pi / 2
		else:
			return 0


	def get_size(self):
		return (self.location.height, self.location.width)


	def iter_points(self, area=None):
		"""Return an iterator over the pixels of a minimap of the given world.

		For every pixel, a tuple ((x, y), (r, g, b)) is returned. These are the x and y
		coordinated and the color of the pixel in RGB.

		If `area` is set, it's supposed to be a part of `location`, that is to be
		returned.
		"""
		location = self.location

		if area is None:
			area = location

		# loop through map coordinates, assuming (0, 0) is the origin of the minimap
		# this facilitates calculating the real world coords
		for x_i in range(0, area.width):
			x = x_i + area.left
			asdf = int(abs(x / location.width - 0.5) * location.height)
			for y_i in range(max(area.top, asdf), min(location.height - asdf, area.height)):
				y = y_i + area.top

				yield (x, y)


class _MinimapImage:
	"""Encapsulates handling of fife Image.
	Provides:
	- self.rendertarget: instance of fife.RenderTarget
	"""
	def __init__(self, minimap, targetrenderer):
		self.minimap = minimap
		self.targetrenderer = targetrenderer
		size = self.minimap.get_size()
		self.image = self.minimap.imagemanager.loadBlank(size[0], size[1])
		self.rendertarget = targetrenderer.createRenderTarget(self.image)
		self.set_drawing_enabled()

	def reset(self):
		"""Reset image to original image"""
		# reload
		self.rendertarget.removeAll()
		size = self.minimap.get_size()
		self.rendertarget.addQuad(self.minimap._get_render_name("background"),
		                          fife.Point(0, 0),
		                          fife.Point(0, size[1]),
		                          fife.Point(size[0], size[1]),
		                          fife.Point(size[0], 0),
		                          *Minimap.COLORS["water"])

	def set_drawing_enabled(self):
		"""Always call this."""
		targetname = self.rendertarget.getTarget().getName()
		self.targetrenderer.setRenderTarget(targetname, False, 0)

