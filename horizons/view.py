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

import math
import time
import fife

import horizons.main

from horizons.util import Changelistener, Rect
from constants import LAYERS

class View(Changelistener):
	"""Class that takes care of all the camera and rendering stuff."""
	def __init__(self, center = (0, 0)):
		"""
		@param center: center position for the main camera
		"""
		super(View, self).__init__()
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
		for i in xrange(0, 3):
			self.layers.append(self.map.createLayer(str(i), cellgrid))
			self.layers[i].setPathingStrategy(fife.CELL_EDGES_ONLY)
		self.view = horizons.main.fife.engine.getView()

		self.cam = self.view.addCamera("main", self.layers[len(self.layers) - 1], fife.Rect(0, 0, horizons.main.fife.settings.getScreenWidth(), horizons.main.fife.settings.getScreenHeight()), fife.ExactModelCoordinate(center[0], center[1], 0.0))
		self.cam.setCellImageDimensions(64, 32)
		self.cam.setRotation(45.0)
		self.cam.setTilt(-60)
		self.cam.setZoom(1)
		self._autoscroll = [0, 0]

		self.view.resetRenderers()
		self.renderer = {}
		for r in ('CameraZoneRenderer', 'InstanceRenderer', 'GridRenderer', 'CellSelectionRenderer', 'BlockingInfoRenderer', 'FloatingTextRenderer', 'QuadTreeRenderer', 'CoordinateRenderer', 'GenericRenderer'):
			self.renderer[r] = getattr(fife, r).getInstance(self.cam) if hasattr(fife, r) else self.cam.getRenderer(r)
			self.renderer[r].clearActiveLayers()
			self.renderer[r].setEnabled(r in ('InstanceRenderer','GenericRenderer'))
		self.renderer['InstanceRenderer'].activateAllLayers(self.map)
		self.renderer['GenericRenderer'].addActiveLayer(self.layers[LAYERS.OBJECTS])
		self.renderer['GridRenderer'].addActiveLayer(self.layers[LAYERS.WATER])

		horizons.main.settings.addCategorys('view')
		horizons.main.settings.view.addCategorys('zoom')
		horizons.main.settings.view.zoom.max = 1
		horizons.main.settings.view.zoom.min = 0.25

	def end(self):
		self.model.deleteMaps()
		self.view.clearCameras()
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
		old = (self._autoscroll[0] != 0) or (self._autoscroll[1] != 0)
		self._autoscroll[0] += x
		self._autoscroll[1] += y
		new = (self._autoscroll[0] != 0) or (self._autoscroll[1] != 0)
		if old != new:
			if old:
				horizons.main.fife.pump.remove(self.do_autoscroll)
			if new:
				self.time_last_autoscroll = time.time()
				horizons.main.fife.pump.append(self.do_autoscroll)

	def do_autoscroll(self):
		t = time.time()
		self.scroll(self._autoscroll[0] * 16 * (t - self.time_last_autoscroll), self._autoscroll[1] * 16 * (t - self.time_last_autoscroll))
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

		if pos.x > horizons.main.session.world.max_x:
			pos.x = horizons.main.session.world.max_x
		elif pos.x < horizons.main.session.world.min_x:
			pos.x = horizons.main.session.world.min_x

		if pos.y > horizons.main.session.world.max_y:
			pos.y = horizons.main.session.world.max_y
		elif pos.y < horizons.main.session.world.min_y:
			pos.y = horizons.main.session.world.min_y

		self.cam.setLocation(loc)
		horizons.main.fife.soundmanager.setListenerPosition(pos.x, pos.y, 1)
		self.cam.refresh()
		self._changed()

	def set_location(self, location):
		loc = self.cam.getLocation()
		pos = loc.getExactLayerCoordinatesRef()
		pos.x, pos.y = location[0], location[1]
		self.cam.setLocation(loc)
		self.cam.refresh()
		self._changed()

	def zoom_out(self):
		zoom = self.cam.getZoom() * 0.875
		if(zoom < horizons.main.settings.view.zoom.min):
			zoom = horizons.main.settings.view.zoom.min
		self.cam.setZoom(zoom)

	def zoom_in(self):
		zoom = self.cam.getZoom() / 0.875
		if(zoom > horizons.main.settings.view.zoom.max):
			zoom = horizons.main.settings.view.zoom.max
		self.cam.setZoom(zoom)

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
		coords = self.cam.getLocation().getLayerCoordinates()
		# TODO: check if acctual screen dimensions are calculated correctly
		return Rect.init_from_topleft_and_size(coords.x, coords.y, \
		            horizons.main.fife.settings.getScreenHeight()/32, \
		            horizons.main.fife.settings.getScreenWidth()/32)

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
