import itertools
import multiprocessing

from fife import fife

import horizons.globals
from horizons.extscheduler import ExtScheduler
from horizons.util.random_map import create_random_island
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

		# random map
		self._worker = None
		self._worker_shared = multiprocessing.RawArray('b', 250 * 250)  # 250 is maximum map size
		self._finish_callback = None

	def end(self):
		self._worker_shared = None
		ExtScheduler().rem_all_classinst_calls(self)
		if self._worker and self._worker.is_alive():
			self._worker.terminate()

	def _draw(self, map_width, map_height, grounds):
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

	# Existing maps

	def draw(self, map_file):
		(map_width, map_height), grounds = self._load_map(SavegameAccessor(map_file, is_map=True))
		self._draw(map_width, map_height, grounds)

	def _load_map(self, db):
		grounds = {}

		min_x, min_y, max_x, max_y = db("SELECT MIN(x), MIN(y), MAX(x), MAX(Y) FROM ground")[0]

		for (x, y) in db("SELECT x, y FROM ground"):
			grounds[(x, y)] = 1

		return ((max_x - min_x, max_y - min_y), grounds)

	# Random maps

	def draw_random_map(self, map_data, map_size, finish_callback=None):
		if self._worker and self._worker.is_alive():
			self._worker.terminate()

		self._map_size = map_size

		self._finish_callback = finish_callback
		self._worker = multiprocessing.Process(target=get_random_map_data, args=(map_data, map_size, self._worker_shared))
		self._worker.start()
		ExtScheduler().add_new_object(self._poll_worker, self, 0.5)

	def _poll_worker(self):
		if self._worker.is_alive():
			ExtScheduler().add_new_object(self._poll_worker, self, 0.1)
			return

		ExtScheduler().rem_all_classinst_calls(self)
		self._worker = None

		# transform array into a dict that `_draw` understands and clear shared memory
		grounds = {}
		for (x, y) in itertools.product(xrange(self._map_size), xrange(self._map_size)):
			idx = x + y * self._map_size
			if self._worker_shared[idx] == 1:
				grounds[(x, y)] = 1
			self._worker_shared[idx] = 0

		self._draw(self._map_size, self._map_size, grounds)
		if self._finish_callback:
			self._finish_callback()


def get_random_map_data(island_strings, map_size, grounds):
	"""Worker process. Creates random map and writes data into shared memory `grounds`."""

	# silence prints when the process is terminated
	import os
	import sys
	sys.stdout = open(os.devnull, 'w')

	for island in island_strings:
		for (x, y, __) in create_random_island(island):
			grounds[x + y * map_size] = 1
