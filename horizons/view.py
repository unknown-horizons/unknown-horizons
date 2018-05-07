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

import math
import time

from fife import fife
from fife.fife import AudioSpaceCoordinate, Point3D

import horizons.globals
from horizons.constants import GAME_SPEED, LAYERS, VIEW
from horizons.messaging import ZoomChanged
from horizons.util.changelistener import ChangeListener
from horizons.util.shapes import Rect


class View(ChangeListener):
	"""Class that takes care of all the camera and rendering stuff."""

	def __init__(self):
		super().__init__()
		self.world = None
		self.model = horizons.globals.fife.engine.getModel()
		self.map = self.model.createMap("map")

		cellgrid = self.model.getCellGrid('square')
		cellgrid.thisown = 0
		cellgrid.setRotation(0)
		cellgrid.setXScale(1)
		cellgrid.setYScale(1)
		cellgrid.setXShift(0)
		cellgrid.setYShift(0)

		using_opengl = horizons.globals.fife.engine.getRenderBackend().getName() == "OpenGL"

		self.layers = []
		for layer_id in range(LAYERS.NUM):
			layer = self.map.createLayer(str(layer_id), cellgrid)
			if layer_id == LAYERS.OBJECTS:
				layer.setPathingStrategy(fife.CELL_EDGES_AND_DIAGONALS)
				layer.setWalkable(True)
			elif using_opengl and layer_id == LAYERS.WATER:
				layer.setStatic(True)
			self.layers.append(layer)

		self.map.initializeCellCaches()
		self.map.finalizeCellCaches()

		# Make sure layer can't change size on layer.createInstance
		# This is necessary because otherwise ship movement on the map edges would
		# keep changing the units' layer size.
		for layer in self.layers:
			if layer.getCellCache():
				layer.getCellCache().setStaticSize(True)

		rect = fife.Rect(0, 0, horizons.globals.fife.engine_settings.getScreenWidth(),
		                       horizons.globals.fife.engine_settings.getScreenHeight())
		self.cam = self.map.addCamera("main", rect)
		self.cam.setCellImageDimensions(*VIEW.CELL_IMAGE_DIMENSIONS)
		self.cam.setRotation(VIEW.ROTATION)
		self.cam.setTilt(VIEW.TILT)
		self.cam.setZoom(VIEW.ZOOM_DEFAULT)

		self.cam.resetRenderers()
		self.renderer = {}
		for r in ('InstanceRenderer', 'GridRenderer',
		          'CellSelectionRenderer', 'BlockingInfoRenderer', 'FloatingTextRenderer',
		          'QuadTreeRenderer', 'CoordinateRenderer', 'GenericRenderer'):
			self.renderer[r] = getattr(fife, r).getInstance(self.cam) if hasattr(fife, r) else self.cam.getRenderer(r)
			self.renderer[r].clearActiveLayers()
			self.renderer[r].setEnabled(r in ('InstanceRenderer', 'GenericRenderer'))
		self.renderer['InstanceRenderer'].activateAllLayers(self.map)
		self.renderer['GenericRenderer'].addActiveLayer(self.layers[LAYERS.OBJECTS])
		self.renderer['GridRenderer'].addActiveLayer(self.layers[LAYERS.GROUND])

		#Setup autoscroll
		horizons.globals.fife.pump.append(self.do_autoscroll)
		self.time_last_autoscroll = time.time()
		self._autoscroll = [0, 0]
		self._autoscroll_keys = [0, 0]

	def end(self):
		horizons.globals.fife.pump.remove(self.do_autoscroll)
		self.model.deleteMaps()
		super().end()

	def center(self, x, y):
		"""Sets the camera position
		@param center: tuple with x and y coordinate (float or int) of tile to center
		"""
		loc = self.cam.getLocation()
		pos = loc.getExactLayerCoordinatesRef()
		pos.x = x
		pos.y = y
		self.cam.setLocation(loc)
		self.cam.refresh()
		self._changed()

	def autoscroll(self, x, y):
		"""Scrolling via mouse (reaching edge of screen)"""
		if horizons.globals.fife.get_uh_setting('EdgeScrolling'):
			self._autoscroll = [x, y]

	def autoscroll_keys(self, x, y):
		"""Scrolling via keyboard keys"""
		self._autoscroll_keys = [x, y]

	def do_autoscroll(self):
		if self._autoscroll == [0, 0] and self._autoscroll_keys == [0, 0]:
			self.time_last_autoscroll = time.time()
			return
		t = time.time()
		speed_factor = GAME_SPEED.TICKS_PER_SECOND * (t - self.time_last_autoscroll)
		self.scroll(speed_factor * (self._autoscroll[0] + self._autoscroll_keys[0]),
		            speed_factor * (self._autoscroll[1] + self._autoscroll_keys[1]))
		self.time_last_autoscroll = t
		self._changed()

	def scroll(self, x, y):
		"""Moves the camera across the screen
		@param x: int representing the amount of pixels to scroll in x direction
		@param y: int representing the amount of pixels to scroll in y direction
		"""
		loc = self.cam.getLocation()
		pos = loc.getExactLayerCoordinatesRef()
		cell_dim = self.cam.getCellImageDimensions()

		if x != 0:
			new_angle = math.pi * self.cam.getRotation() / 180.0
			zoom_factor = self.cam.getZoom() * cell_dim.x * horizons.globals.fife.get_uh_setting('ScrollSpeed')
			pos.x += x * math.cos(new_angle) / zoom_factor
			pos.y += x * math.sin(new_angle) / zoom_factor
		if y != 0:
			new_angle = math.pi * self.cam.getRotation() / -180.0
			zoom_factor = self.cam.getZoom() * cell_dim.y * horizons.globals.fife.get_uh_setting('ScrollSpeed')
			pos.x += y * math.sin(new_angle) / zoom_factor
			pos.y += y * math.cos(new_angle) / zoom_factor

		if pos.x > self.world.max_x:
			pos.x = self.world.max_x
		elif pos.x < self.world.min_x:
			pos.x = self.world.min_x

		if pos.y > self.world.max_y:
			pos.y = self.world.max_y
		elif pos.y < self.world.min_y:
			pos.y = self.world.min_y

		self.cam.setLocation(loc)
		for i in ['speech', 'effects']:
			emitter = horizons.globals.fife.sound.emitter[i]
			if emitter is not None:
				emitter.setPosition(AudioSpaceCoordinate(pos.x, pos.y, 1))
		if horizons.globals.fife.get_fife_setting("PlaySounds"):
			horizons.globals.fife.sound.soundmanager.setListenerPosition(AudioSpaceCoordinate(pos.x, pos.y, 1))
		self._changed()

	def _prepare_zoom_to_cursor(self, zoom):
		"""Change the camera's position to accommodation zooming to the specified setting."""
		def middle(click_coord, scale, length):
			mid = length / 2.0
			return int(round(mid - (click_coord - mid) * (scale - 1)))

		scale = self.cam.getZoom() / zoom
		x, y = horizons.globals.fife.cursor.getPosition()
		new_x = middle(x, scale, horizons.globals.fife.engine_settings.getScreenWidth())
		new_y = middle(y, scale, horizons.globals.fife.engine_settings.getScreenHeight())
		screen_point = fife.ScreenPoint(new_x, new_y)
		map_point = self.cam.toMapCoordinates(screen_point, False)
		self.center(map_point.x, map_point.y)

	def zoom_out(self, track_cursor=False):
		zoom = self.cam.getZoom() * VIEW.ZOOM_LEVELS_FACTOR
		if zoom < VIEW.ZOOM_MIN:
			zoom = VIEW.ZOOM_MIN
		if track_cursor:
			self._prepare_zoom_to_cursor(zoom)
		self.zoom = zoom

	def zoom_in(self, track_cursor=False):
		zoom = self.cam.getZoom() / VIEW.ZOOM_LEVELS_FACTOR
		if zoom > VIEW.ZOOM_MAX:
			zoom = VIEW.ZOOM_MAX
		if track_cursor:
			self._prepare_zoom_to_cursor(zoom)
		self.zoom = zoom

	@property
	def zoom(self):
		return self.cam.getZoom()

	@zoom.setter
	def zoom(self, value):
		self.cam.setZoom(value)
		ZoomChanged.broadcast(self, value)

	def rotate_right(self):
		self.cam.setRotation((self.cam.getRotation() - 90) % 360)

	def rotate_left(self):
		self.cam.setRotation((self.cam.getRotation() + 90) % 360)

	def set_rotation(self, rotation):
		self.cam.setRotation(rotation)
		self._changed()

	def get_displayed_area(self):
		"""
		Returns the coords (clockwise, beginning in the top-left corner) of what is
		displayed on the screen.
		"""
		screen_width = horizons.globals.fife.engine_settings.getScreenWidth()
		screen_height = horizons.globals.fife.engine_settings.getScreenHeight()

		points = []
		for screen_x, screen_y in [
				(0, 0),
				(screen_width, 0),
				(screen_width, screen_height),
				(0, screen_height)]:
			map_point = self.cam.toMapCoordinates(Point3D(screen_x, screen_y), False)
			points.append((map_point.x, map_point.y))
		return points

	def save(self, db):
		loc = self.cam.getLocation().getExactLayerCoordinates()
		db("INSERT INTO view(zoom, rotation, location_x, location_y) VALUES(?, ?, ?, ?)",
			 self.cam.getZoom(), self.cam.getRotation(), loc.x, loc.y)

	def load(self, db, world):
		# NOTE: this is no class function, since view is initiated before loading
		self.world = world
		res = db("SELECT zoom, rotation, location_x, location_y FROM view")
		if not res:
			# no view info
			return
		zoom, rotation, loc_x, loc_y = res[0]
		self.zoom = zoom
		self.set_rotation(rotation)
		self.center(loc_x, loc_y)

	def resize_layers(self, db):
		"""Resize layers to the size required by the entire map."""
		min_x, min_y, max_x, max_y = db("SELECT min(x), min(y), max(x), max(y) FROM ground")[0]
		if min_x is None:
			# this happens on the empty maps that are created for the editor
			min_x, min_y, max_x, max_y = (0, 0, 0, 0)
		min_x -= db.map_padding
		min_y -= db.map_padding
		max_x += db.map_padding
		max_y += db.map_padding

		for layer_id, layer in enumerate(self.layers):
			if not layer.getCellCache():
				continue
			assert layer_id != LAYERS.WATER, 'Water layer would need special treatment (see previous version)'

			rect = fife.Rect(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
			layer.getCellCache().setSize(rect)
