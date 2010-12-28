# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

import horizons.main

from horizons.util import ChangeListener, Rect
from horizons.constants import LAYERS, VIEW, GAME_SPEED

class View(ChangeListener):
	"""Class that takes care of all the camera and rendering stuff."""

	def __init__(self, session, center = (0, 0)):
		"""
		@param session: Session instance
		@param center: center position for the main camera
		"""
		super(View, self).__init__()
		self.session = session
		self.model = horizons.main.fife.engine.getModel()
		self.map = self.model.createMap("map")

		cellgrid = self.model.getCellGrid('square')
		cellgrid.thisown = 0
		cellgrid.setRotation(0)
		cellgrid.setXScale(1)
		cellgrid.setYScale(1)
		cellgrid.setXShift(0)
		cellgrid.setYShift(0)

		self.layers = []
		for i in xrange(0, LAYERS.NUM):
			self.layers.append(self.map.createLayer(str(i), cellgrid))
			self.layers[i].setPathingStrategy(fife.CELL_EDGES_ONLY)

		self.cam = self.map.addCamera("main", self.layers[len(self.layers) - 1], \
		                               fife.Rect(0, 0, \
		                                         horizons.main.fife.engine_settings.getScreenWidth(), \
		                                         horizons.main.fife.engine_settings.getScreenHeight()) \
		                               )
		self.cam.setCellImageDimensions(*VIEW.CELL_IMAGE_DIMENSIONS)
		self.cam.setRotation(VIEW.ROTATION)
		self.cam.setTilt(VIEW.TILT)
		self.cam.setZoom(VIEW.ZOOM)

		self.cam.resetRenderers()
		self.renderer = {}
		for r in ('InstanceRenderer', 'GridRenderer', \
		          'CellSelectionRenderer', 'BlockingInfoRenderer', 'FloatingTextRenderer', \
		          'QuadTreeRenderer', 'CoordinateRenderer', 'GenericRenderer'):
			self.renderer[r] = getattr(fife, r).getInstance(self.cam) if hasattr(fife, r) else self.cam.getRenderer(r)
			self.renderer[r].clearActiveLayers()
			self.renderer[r].setEnabled(r in ('InstanceRenderer','GenericRenderer'))
		self.renderer['InstanceRenderer'].activateAllLayers(self.map)
		self.renderer['GenericRenderer'].addActiveLayer(self.layers[LAYERS.OBJECTS])
		self.renderer['GridRenderer'].addActiveLayer(self.layers[LAYERS.GROUND])

		#Setup autoscroll
		horizons.main.fife.pump.append(self.do_autoscroll)
		self.time_last_autoscroll = time.time()
		self._autoscroll = [0, 0]
		self._autoscroll_keys = [0, 0]

	def end(self):
		horizons.main.fife.pump.remove(self.do_autoscroll)
		self.model.deleteMaps()
		super(View, self).end()

	def center(self, x, y):
		"""Sets the camera position
		@param center: tuple with x and y coordinate (float or int) of tile to center
		"""
		loc = self.cam.getLocationRef()
		pos = loc.getExactLayerCoordinatesRef()
		pos.x = x
		pos.y = y
		self.cam.setLocation(loc)
		self._changed()

	def autoscroll(self, x, y):
		"""
		@param x:
		@param y:
		"""
		self._autoscroll[0] = x
		self._autoscroll[1] = y

	def autoscroll_keys(self, x, y):
		"""
		@param x:
		@param y:
		"""
		self._autoscroll_keys[0] = x
		self._autoscroll_keys[1] = y

	def do_autoscroll(self):
		if self._autoscroll[0] == 0 and \
		   self._autoscroll[1] == 0 and \
		   self._autoscroll_keys[0] == 0 and \
		   self._autoscroll_keys[1] == 0:
			self.time_last_autoscroll = time.time()
			return
		t = time.time()
		self.scroll( \
		  (self._autoscroll[0]+self._autoscroll_keys[0]) * GAME_SPEED.TICKS_PER_SECOND * (t - self.time_last_autoscroll), \
		  (self._autoscroll[1]+self._autoscroll_keys[1]) * GAME_SPEED.TICKS_PER_SECOND * (t - self.time_last_autoscroll))
		self.time_last_autoscroll = t
		self._changed()

	def scroll(self, x, y):
		"""Moves the camera across the screen
		@param x: int representing the amount of pixels to scroll in x direction
		@param y: int representing the amount of pixels to scroll in y direction
		"""
		loc = self.cam.getLocation()
		pos = loc.getExactLayerCoordinatesRef()
		if x != 0:
			pos.x += x * math.cos(math.pi * self.cam.getRotation() / 180.0) / self.cam.getZoom() / 32.0
			pos.y += x * math.sin(math.pi * self.cam.getRotation() / 180.0) / self.cam.getZoom() / 32.0
		if y != 0:
			pos.x += y * math.sin(math.pi * self.cam.getRotation() / -180.0) / self.cam.getZoom() / 16.0
			pos.y += y * math.cos(math.pi * self.cam.getRotation() / -180.0) / self.cam.getZoom() / 16.0

		if pos.x > self.session.world.max_x:
			pos.x = self.session.world.max_x
		elif pos.x < self.session.world.min_x:
			pos.x = self.session.world.min_x

		if pos.y > self.session.world.max_y:
			pos.y = self.session.world.max_y
		elif pos.y < self.session.world.min_y:
			pos.y = self.session.world.min_y

		self.cam.setLocation(loc)
		horizons.main.fife.soundmanager.setListenerPosition(pos.x, pos.y, 1)
		self._changed()

	def set_location(self, location):
		loc = self.cam.getLocation()
		pos = loc.getExactLayerCoordinatesRef()
		pos.x, pos.y = location[0], location[1]
		self.cam.setLocation(loc)
		self.cam.refresh()
		self._changed()

	def zoom_out(self):
		zoom = self.cam.getZoom() * VIEW.ZOOM_LEVELS_FACTOR
		if(zoom < VIEW.ZOOM_MIN):
			zoom = VIEW.ZOOM_MIN
		self.set_zoom(zoom)

	def zoom_in(self):
		zoom = self.cam.getZoom() / VIEW.ZOOM_LEVELS_FACTOR
		if(zoom > VIEW.ZOOM_MAX):
			zoom = VIEW.ZOOM_MAX
		self.set_zoom(zoom)

	def get_zoom(self):
		return self.cam.getZoom()

	def set_zoom(self, zoom):
		self.cam.setZoom(zoom)
		self._changed()

	def rotate_right(self):
		self.cam.setRotation((self.cam.getRotation() + 90) % 360)

	def rotate_left(self):
		self.cam.setRotation((self.cam.getRotation() - 90) % 360)

	def set_rotation(self, rotation):
		self.cam.setRotation(rotation)
		self._changed()

	def get_displayed_area(self):
		"""Returns the coords of what is displayed on the screen as Rect"""
		coords = self.cam.getLocationRef().getLayerCoordinates()
		cell_dim = self.cam.getCellImageDimensions()
		screen_width_as_coords = (horizons.main.fife.engine_settings.getScreenWidth()/cell_dim.x, \
		                          horizons.main.fife.engine_settings.getScreenHeight()/cell_dim.y)
		return Rect.init_from_topleft_and_size(coords.x - (screen_width_as_coords[0]/2), \
		                                       coords.y - (screen_width_as_coords[1]/2),
		                                       *screen_width_as_coords)

	def save(self, db):
		loc = self.cam.getLocation().getExactLayerCoordinates()
		db("INSERT INTO view(zoom, rotation, location_x, location_y) VALUES(?, ?, ?, ?)",
			 self.cam.getZoom(), self.cam.getRotation(), loc.x, loc.y)

	def load(self, db):
		# NOTE: this is no class function, since view is initiated before loading
		res = db("SELECT zoom, rotation, location_x, location_y FROM view")
		if len(res) == 0 :
			# no view info
			return
		zoom, rotation, loc_x, loc_y = res[0]
		self.set_zoom(zoom)
		self.set_rotation(rotation)
		self.set_location((loc_x, loc_y))
