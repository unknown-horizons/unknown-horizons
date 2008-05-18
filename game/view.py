import fife
import math

class View:
	def __init__(self, engine, screen_size, layer, center = (0, 0)):
		self.cam = engine.getView().addCamera("main", layer, fife.Rect(0, 0, screen_size[0], screen_size[1]), fife.ExactModelCoordinate(center[0], center[1], 0.0))
		self.cam.setCellImageDimensions(32, 16)
		self.cam.setRotation(45.0)
		self.cam.setTilt(-60.0)
		self.cam.setZoom(1)
		self.center(center)

	def center(self, center):
		"""Sets the camera position
		@var center: tuple with x and y coordinate (float or int) of tile to center
		"""
		loc = self.cam.getLocationRef()
		pos = loc.getExactLayerCoordinatesRef()
		pos.x = center[0]
		pos.y = center[1]
		self.cam.setLocation(loc)

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
