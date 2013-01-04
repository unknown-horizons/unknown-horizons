import itertools

from fife import fife

import horizons.globals
from horizons.util.savegameaccessor import SavegameAccessor


class MapPreview(object):
	color_island = (137, 117, 87)

	def __init__(self, icon_widget):
		self._icon_widget = icon_widget

		self._targetrenderer = horizons.globals.fife.targetrenderer

		self._width, self._height = self._icon_widget.width, self._icon_widget.height
		self._image = horizons.globals.fife.imagemanager.loadBlank(self._width, self._height)

		self._rendertarget = self._targetrenderer.createRenderTarget(self._image)
		self._icon_widget.image = fife.GuiImage(self._image)

	def draw(self, map_file):
		(map_width, map_height), grounds = self._load_map(SavegameAccessor(map_file, is_map=True))

		pixel_per_coord_x = float(map_width) / self._width
		pixel_per_coord_y = float(map_height) / self._height

		self._rendertarget.removeAll()
		# True means the previous data on the renderbackend will be discarded
		self._targetrenderer.setRenderTarget(self._rendertarget.getTarget().getName(), True, 0)

		point = fife.Point()
		draw_point = self._rendertarget.addPoint

		# for each pixel in the image we check the map to see if there is an island
		for (x, y) in itertools.product(xrange(self._width), xrange(self._height)):
			map_x = int(x * pixel_per_coord_x)
			map_y = int(y * pixel_per_coord_y)
			if (map_x, map_y) in grounds:
				point.set(x, y)
				draw_point("c", point, *self.color_island)

	def _load_map(self, db):
		grounds = {}

		min_x, min_y, max_x, max_y = db("SELECT MIN(x), MIN(y), MAX(x), MAX(Y) FROM ground")[0]

		for (x, y) in db("SELECT x, y FROM ground"):
			grounds[(x, y)] = 1

		return ((max_x - min_x, max_y - min_y), grounds)
