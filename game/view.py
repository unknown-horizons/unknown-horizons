import fife
import math
import game.main

class View:
	def __init__(self, center = (0, 0)):
		self.model = game.main.fife.engine.getModel()
		self.map = self.model.createMap("map")

		cellgrid = fife.SquareGrid(False)
		cellgrid.thisown = 0
		cellgrid.setRotation(0)
		cellgrid.setXScale(1)
		cellgrid.setYScale(1)
		cellgrid.setXShift(0)
		cellgrid.setYShift(0)

		self.layers = []
		for i in xrange(0,3):
			self.layers.append(self.map.createLayer(str(i), cellgrid))
			self.layers[i].setPathingStrategy(fife.CELL_EDGES_ONLY)
		self.view = game.main.fife.engine.getView()

		self.cam = self.view.addCamera("main", self.layers[len(self.layers) - 1], fife.Rect(0, 0, game.main.fife.settings.getScreenWidth(), game.main.fife.settings.getScreenHeight()), fife.ExactModelCoordinate(center[0], center[1], 0.0))
		self.cam.setCellImageDimensions(32, 16)
		self.cam.setRotation(45.0)
		self.cam.setTilt(-60)
		self.cam.setZoom(1)
		self._autoscroll = [0, 0]

		self.outline_renderer = fife.InstanceRenderer.getInstance(self.cam)

		self.view.resetRenderers()
		self.renderer = {}
		for r in ('InstanceRenderer',):
			self.renderer[r] = getattr(fife, r).getInstance(self.cam)
		for r in ('CoordinateRenderer', 'GridRenderer'):
			self.renderer[r] = self.cam.getRenderer(r)
		print self.renderer
		self.renderer['CoordinateRenderer'].clearActiveLayers()
		self.renderer['CoordinateRenderer'].addActiveLayer(self.layers[1])

	def center(self, x, y):
		"""Sets the camera position
		@var center: tuple with x and y coordinate (float or int) of tile to center
		"""
		loc = self.cam.getLocationRef()
		pos = loc.getExactLayerCoordinatesRef()
		pos.x = x
		pos.y = y
		self.cam.setLocation(loc)

	def autoscroll(self, x, y):
		print "autoscroll x:", x, "y:", y
		old = (self._autoscroll[0] != 0) or (self._autoscroll[1] != 0)
		self._autoscroll[0] += x
		self._autoscroll[1] += y
		new = (self._autoscroll[0] != 0) or (self._autoscroll[1] != 0)
		if old != new:
			if old:
				game.main.game.timer.remove_test(self.tick)
			if new:
				game.main.game.timer.add_test(self.tick)

	def tick(self, tick):
		self.scroll(self._autoscroll[0], self._autoscroll[1])

	def scroll(self, x, y):
		"""Moves the camera across the screen
		@var x: int representing the amount of pixels to scroll in x direction
		@var y: int representing the amount of pixels to scroll in y direction
		"""
		loc = self.cam.getLocationRef()
		pos = loc.getExactLayerCoordinatesRef()
		if x != 0:
			pos.x += x * math.cos(math.pi * self.cam.getRotation() / 180.0) / self.cam.getZoom()
			pos.y += x * math.sin(math.pi * self.cam.getRotation() / 180.0) / self.cam.getZoom()
		if y != 0:
			pos.x += y * math.sin(math.pi * self.cam.getRotation() / -180.0) / self.cam.getZoom()
			pos.y += y * math.cos(math.pi * self.cam.getRotation() / -180.0) / self.cam.getZoom()
		self.cam.setLocation(loc)

	def zoom_out(self):
		zoom = self.cam.getZoom() * 0.875
		if(zoom < 0.25):
			zoom = 0.25
		self.cam.setZoom(zoom)

	def zoom_in(self):
		zoom = self.cam.getZoom() / 0.875
		if(zoom > 1):
			zoom = 1
		self.cam.setZoom(zoom)

	def rotate_right(self):
		self.cam.setRotation((self.cam.getRotation() + 90) % 360)

	def rotate_left(self):
		self.cam.setRotation((self.cam.getRotation() - 90) % 360)
