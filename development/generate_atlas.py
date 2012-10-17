#!/usr/bin/env python

# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import array
import glob
import json
import multiprocessing
import os
import os.path
import sys

try:
	import Image
except ImportError:
	print 'The Python Imaging Library (PIL) package is needed to run this script.'
	sys.exit(1)

# make this script work both when started inside development and in the uh root dir
if not os.path.exists('content'):
	os.chdir('..')
assert os.path.exists('content'), 'Content dir not found.'

sys.path.append('.')
from run_uh import init_environment
init_environment()

class DummyFife:
	use_atlases = False
import horizons.globals
horizons.globals.fife = DummyFife()

from horizons.constants import PATHS
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.loaders.tilesetloader import TileSetLoader

class AtlasEntry(object):
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height

class AtlasBook(object):
	def __init__(self, id, max_size):
		self.id = id
		self.path = os.path.join(PATHS.ATLAS_FILES_DIR, '%03d.png' % id)
		self.max_size = max_size
		self.location = {}
		self.cur_x = 0
		self.cur_y = 0
		self.cur_h = 0

	def add(self, w, h, path):
		"""Return true if and only if the image was added."""
		if self.cur_x + w <= self.max_size and self.cur_y + h <= self.max_size:
			# add to the end of the current row
			self.location[path] = AtlasEntry(self.cur_x, self.cur_y, w, h)
			self.cur_x += w
			self.cur_h = max(self.cur_h, h)
			return True

		if w <= self.max_size and self.cur_y + self.cur_h + h <= self.max_size:
			# add to the beginning of the next row
			self.cur_x = w
			self.cur_y += self.cur_h
			self.cur_h = h
			self.location[path] = AtlasEntry(0, self.cur_y, w, h)
			return True

		# unable to fit in the given space with the current algorithm
		return False

	def save(self):
		"""Write the entire image to a file with the given path."""
		im = Image.new('RGBA', (self.max_size, self.max_size), (255, 0, 255, 255))

		# place the sub-images in the right places
		gdata = []
		for path, entry in self.location.iteritems():
			with open(path, 'rb') as png_file:
				sub_image = Image.open(png_file)
				im.paste(sub_image, (entry.x, entry.y))

		# write the entire image to the file
		with open(self.path, 'wb') as out_file:
			im.save(out_file, 'png')

def save_atlas_book(book):
	book.save()

class ImageSetManager(object):
	def __init__(self, initial_data, path):
		self._data = {}
		self._path = path
		self._initial_data = initial_data

		self.files = []
		for set_id in initial_data:
			for action_id in initial_data[set_id]:
				for rotation in sorted(initial_data[set_id][action_id]):
					for path in sorted(initial_data[set_id][action_id][rotation]):
						self.files.append(path)

	def _add_entry(self, set_id, action_id, rotation, path, row):
		if set_id not in self._data:
			self._data[set_id] = {}
		if action_id not in self._data[set_id]:
			self._data[set_id][action_id] = {}
		if rotation not in self._data[set_id][action_id]:
			self._data[set_id][action_id][rotation] = {}
		self._data[set_id][action_id][rotation][path.replace(os.sep, '/')] = row

	def save(self, generator):
		for set_id in self._initial_data:
			for action_id in self._initial_data[set_id]:
				for rotation in sorted(self._initial_data[set_id][action_id]):
					for path in sorted(self._initial_data[set_id][action_id][rotation]):
						book = generator.atlas_book_lookup[path]
						book_entry = book.location[path]

						row = []
						row.append(self._initial_data[set_id][action_id][rotation][path])
						row.append(book.id)
						row.append(book_entry.x)
						row.append(book_entry.y)
						row.append(book_entry.width)
						row.append(book_entry.height)
						self._add_entry(set_id, action_id, rotation, path, row)

		with open(self._path, 'wb') as json_file:
			json.dump(self._data, json_file, indent=1)

class AtlasGenerator(object):
	def __init__(self, root_dir, max_size):
		self.root_dir = root_dir
		self.max_size = max_size
		self.files = []
		self.books = []
		self.num_books = 0
		self.atlas_book_lookup = {}

		self.sets = []
		self.sets.append(ImageSetManager(TileSetLoader.get_sets(), PATHS.TILE_SETS_JSON_FILE))
		self.sets.append(ImageSetManager(ActionSetLoader.get_sets(), PATHS.ACTION_SETS_JSON_FILE))

	def _find_files(self):
		paths = []
		for set in self.sets:
			for path in set.files:
				paths.append(path)

		for path in paths:
			with open(path, 'rb') as png_file:
				w, h = Image.open(png_file).size
				self.files.append((w * h, h, w, path))

	def _save_books(self):
		processes = max(1, min(len(self.books), multiprocessing.cpu_count() - 1))
		pool = multiprocessing.Pool(processes=processes)
		for book in self.books:
			pool.apply_async(save_atlas_book, [book])
		pool.close()
		pool.join()

	def save(self):
		with open(PATHS.ATLAS_DB_PATH, 'wb') as atlas_db_file:
			atlas_db_file.write("CREATE TABLE atlas('atlas_id' INTEGER NOT NULL PRIMARY KEY, 'atlas_path' TEXT NOT NULL);\n")
			for book in self.books:
				atlas_db_file.write("INSERT INTO atlas VALUES(%d, '%s');\n" % (book.id, book.path))

		for set in self.sets:
			set.save(self)

		self._save_books()

	def _add_atlas_book(self):
		self.books.append(AtlasBook(len(self.books), self.max_size))

	def _add_image(self, w, h, path):
		if not self.books:
			self._add_atlas_book()

		if not self.books[-1].add(w, h, path):
			self._add_atlas_book()
			assert self.books[-1].add(w, h, path)

		self.atlas_book_lookup[path] = self.books[-1]

	def generate(self):
		self._find_files()
		assert self.files, 'No files found.'
		assert (self.files[0][1] <= self.max_size and self.files[0][2] <= self.max_size), 'Image too large: ' + str(self.files[0][1:])

		for _, h, w, path in self.files:
			self._add_image(w, h, path)

if __name__ == '__main__':
	generator = AtlasGenerator('.', 2048)
	generator.generate()
	generator.save()
