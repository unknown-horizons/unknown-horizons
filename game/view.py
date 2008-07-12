# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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
import math
import game.main
from game.util import livingObject

class View(livingObject):
	"""Class that takes care of all the camera and rendering stuff."""
	def begin(self, center = (0, 0)):
		"""
		@param center: center position for the main camera
		"""
		self.model = game.main.fife.engine.getModel()
		self.map = self.model.createMap("map")

		cellgrid = self.model.getCellGrid('square')
		cellgrid.thisown = 0
		cellgrid.setRotation(0)
		cellgrid.setXScale(1)
		cellgrid.setYScale(1)
		cellgrid.setXShift(0)
		cellgrid.setYShift(0)

		self.layers = []
		for i in xrange(0,2):
			self.layers.append(self.map.createLayer(str(i), cellgrid))
			self.layers[i].setPathingStrategy(fife.CELL_EDGES_ONLY)
		self.view = game.main.fife.engine.getView()

		self.cam = self.view.addCamera("main", self.layers[len(self.layers) - 1], fife.Rect(0, 0, game.main.fife.settings.getScreenWidth(), game.main.fife.settings.getScreenHeight()), fife.ExactModelCoordinate(center[0], center[1], 0.0))
		self.cam.setCellImageDimensions(32, 16)
		self.cam.setRotation(45.0)
		self.cam.setTilt(-60)
		self.cam.setZoom(1)
		self._autoscroll = [0, 0]

		self.view.resetRenderers()
		self.renderer = {}
		for r in ('CameraZoneRenderer','InstanceRenderer','GridRenderer','CellSelectionRenderer','BlockingInfoRenderer','FloatingTextRenderer','QuadTreeRenderer','CoordinateRenderer','GenericRenderer'):
			self.renderer[r] = getattr(fife, r).getInstance(self.cam) if hasattr(fife, r) else self.cam.getRenderer(r)
			self.renderer[r].clearActiveLayers()
			self.renderer[r].setEnabled(r in ('InstanceRenderer','GenericRenderer'))
		self.renderer['InstanceRenderer'].activateAllLayers(self.map)
		self.renderer['GenericRenderer'].addActiveLayer(self.layers[1])
		self.renderer['GridRenderer'].addActiveLayer(self.layers[0])

		game.main.settings.addCategorys('view')
		game.main.settings.view.addCategorys('zoom')
		game.main.settings.view.zoom.max = 1
		game.main.settings.view.zoom.min = 0.25

	def end(self):
		"""
		"""
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
				game.main.session.timer.remove_test(self.tick)
			if new:
				game.main.session.timer.add_test(self.tick)

	def tick(self, tick):
		"""
		@param tick:
		"""
		self.scroll(self._autoscroll[0], self._autoscroll[1])

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

		if pos.x > game.main.session.world.max_x:
			pos.x = game.main.session.world.max_x
		elif pos.x < game.main.session.world.min_x:
			pos.x = game.main.session.world.min_x

		if pos.y > game.main.session.world.max_y:
			pos.y = game.main.session.world.max_y
		elif pos.y < game.main.session.world.min_y:
			pos.y = game.main.session.world.min_y

		self.cam.setLocation(loc)
		self.cam.refresh()

	def zoom_out(self):
		zoom = self.cam.getZoom() * 0.875
		if(zoom < game.main.settings.view.zoom.min):
			zoom = game.main.settings.view.zoom.min
		self.cam.setZoom(zoom)

	def zoom_in(self):
		zoom = self.cam.getZoom() / 0.875
		if(zoom > game.main.settings.view.zoom.max):
			zoom = game.main.settings.view.zoom.max
		self.cam.setZoom(zoom)

	def rotate_right(self):
		self.cam.setRotation((self.cam.getRotation() + 90) % 360)

	def rotate_left(self):
		self.cam.setRotation((self.cam.getRotation() - 90) % 360)
