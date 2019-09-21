#!/usr/bin/env python3

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

import glob
import json
import logging
import math
import multiprocessing
import os
import os.path
import pickle
import sys
import traceback

# add paths for Mac Os X app container (Unknown Horizons.app)
app_python_lib_path = os.path.join(os.getcwd(), 'lib', 'python3.4')
if os.path.exists(app_python_lib_path):
	# horizons path: Unknown Horizons.app/Contents/Resources/lib/python3.3/horizons
	sys.path.append(app_python_lib_path)
	# PIL path: Unknown Horizons.app/Contents/Resources/lib/python3.3/lib-dynload/PIL
	sys.path.append(os.path.join(app_python_lib_path, 'lib-dynload'))

try:
	from PIL import Image
except ImportError:
	# Logging is not set up at this point.
	print('The Python Imaging Library (PIL / Pillow) package'
	      ' is needed to run the atlas generator.')
	sys.exit(1)


# make this script work both when started inside development and in the uh root dir
if not os.path.exists('content'):
	os.chdir('..')
assert os.path.exists('content'), 'Content dir not found.'

sys.path.append('.')


class DummyFife:
	use_atlases = False

# TODO We can probably remove the type ignore in the next release of typeshed/mypy
#      See https://github.com/python/typeshed/commit/08ac3b7742f1fd55f801ac66d7517cf60aa471d6


import horizons.globals # isort:skip
horizons.globals.fife = DummyFife() # type: ignore

from horizons.constants import PATHS # isort:skip
from horizons.util.dbreader import DbReader # isort:skip
from horizons.util.loaders.actionsetloader import ActionSetLoader # isort:skip
from horizons.util.loaders.tilesetloader import TileSetLoader # isort:skip


class AtlasEntry:
	def __init__(self, x, y, width, height, last_modified):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.last_modified = last_modified


class AtlasBook:
	log = logging.getLogger("generate_atlases")

	def __init__(self, id, max_size):
		self.id = id
		self.path = os.path.join(PATHS.ATLAS_FILES_DIR, '{0:03d}.png'.format(id))
		self.max_size = max_size
		self._clear()

	def _clear(self):
		self.location = {}
		self.cur_x = 0
		self.cur_y = 0
		self.cur_h = 0

	def add(self, w, h, path):
		"""Return true if and only if the image was added."""
		if self.cur_x + w <= self.max_size and self.cur_y + h <= self.max_size:
			# add to the end of the current row
			self.location[path] = AtlasEntry(self.cur_x, self.cur_y, w, h, int(os.path.getmtime(path)))
			self.cur_x += w
			self.cur_h = max(self.cur_h, h)
			return True

		if w <= self.max_size and self.cur_y + self.cur_h + h <= self.max_size:
			# add to the beginning of the next row
			self.cur_x = w
			self.cur_y += self.cur_h
			self.cur_h = h
			self.location[path] = AtlasEntry(0, self.cur_y, w, h, int(os.path.getmtime(path)))
			return True

		# unable to fit in the given space with the current algorithm
		return False

	def save(self):
		"""Write the entire image to a file with the given path."""
		if not os.path.exists(PATHS.ATLAS_FILES_DIR):
			# Make sure atlas directory is available
			os.mkdir(PATHS.ATLAS_FILES_DIR)

		im = Image.new('RGBA', (self.max_size, self.max_size), (255, 0, 255, 255))

		# place the sub-images in the right places
		for path, entry in self.location.items():
			with open(path, 'rb') as png_file:
				sub_image = Image.open(png_file)
				im.paste(sub_image, (entry.x, entry.y))

		# write the entire image to the file
		with open(self.path, 'wb') as out_file:
			im.save(out_file, 'png')


def save_atlas_book(book):
	book.save()


class ImageSetManager:
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

		with open(self._path, 'w') as json_file:
			json.dump(self._data, json_file, indent=1)


class AtlasGenerator:
	log = logging.getLogger("generate_atlases")
	# increment this when the structure of the atlases changes
	current_version = 1

	def __init__(self, max_size):
		self.version = self.current_version
		self.max_size = max_size
		self.books = []
		self.num_books = 0
		self.atlas_book_lookup = {}

	def _init_sets(self):
		self.sets = []
		self.sets.append(ImageSetManager(TileSetLoader.get_sets(), PATHS.TILE_SETS_JSON_FILE))
		self.sets.append(ImageSetManager(ActionSetLoader.get_sets(), PATHS.ACTION_SETS_JSON_FILE))

	def _save_sets(self):
		for set in self.sets:
			set.save(self)

	@classmethod
	def _save_books(cls, books):
		processes = max(1, min(len(books), multiprocessing.cpu_count() - 1))
		pool = multiprocessing.Pool(processes=processes)
		for book in books:
			pool.apply_async(save_atlas_book, [book])
		pool.close()
		pool.join()

	def save(self):
		with open(PATHS.ATLAS_DB_PATH, 'w') as atlas_db_file:
			atlas_db_file.write("CREATE TABLE atlas('atlas_id' INTEGER NOT NULL PRIMARY KEY, 'atlas_path' TEXT NOT NULL);\n")
			for book in self.books:
				atlas_db_file.write("INSERT INTO atlas VALUES({0:d}, "
					"'{1!s}');\n".format(book.id, book.path))

		self._save_sets()
		self._save_books(self.books)
		self._save_metadata()

	def _add_atlas_book(self):
		self.books.append(AtlasBook(len(self.books), self.max_size))

	def _add_image(self, w, h, path):
		if not self.books:
			self._add_atlas_book()

		if not self.books[-1].add(w, h, path):
			self._add_atlas_book()
			assert self.books[-1].add(w, h, path)

		self.atlas_book_lookup[path] = self.books[-1]

	@classmethod
	def _get_dimensions(cls, path):
		with open(path, 'rb') as png_file:
			return Image.open(png_file).size

	def _get_paths(self):
		paths = []
		for set in self.sets:
			for path in set.files:
				paths.append(path)
		return paths

	def recreate(self):
		print('Recreating all atlases')

		self._init_sets()
		paths = self._get_paths()
		data = []
		for path in paths:
			w, h = self._get_dimensions(path)
			data.append((w * h, h, w, path))

		assert data, 'No files found.'
		assert (data[0][1] <= self.max_size and data[0][2] <= self.max_size), 'Image too large: ' + str(data[0][1:])

		for _, h, w, path in data:
			self._add_image(w, h, path)
		self.save()

	def _update_selected_books(self, update_books):
		print('Updating some of the atlases:')
		for book in sorted(update_books, key=lambda book: int(book.id)):
			print(book.path)
		print()

		self._save_sets()
		self._save_books(update_books)

	def update(self):
		self._init_sets()
		paths = self._get_paths()

		# if the sizes don't match then something has been deleted or added
		recreate_all = False
		if len(set(paths)) != len(self.atlas_book_lookup):
			recreate_all = True
			self.log.info("The old number of images (%d) doesn't match the new (%d)",
			              len(self.atlas_book_lookup), len(set(paths)))

		recreate_books = set()
		if not recreate_all:
			for path in paths:
				if path not in self.atlas_book_lookup:
					self.log.info('A new image has been added: %s', path)
					recreate_all = True
					break

				last_modified = int(os.path.getmtime(path))
				book = self.atlas_book_lookup[path]
				entry = book.location[path]
				if last_modified == entry.last_modified:
					continue

				self.log.info('An image has been modified: %s', path)
				w, h = self._get_dimensions(path)
				if w > entry.width or h > entry.height:
					self.log.info('An image is larger than before: %s', path)
					recreate_all = True
					break

				if book not in recreate_books:
					self.log.info('Need to recreate %s', book.path)
					recreate_books.add(book)

				# update the entry
				entry.width = w
				entry.height = h
				entry.last_modified = last_modified

		if recreate_all:
			self.log.info('Forced to recreate the entire atlas.')
			return False

		if recreate_books:
			self.log.info('Updated selected books')
			self._update_selected_books(recreate_books)
			self._save_metadata()
		else:
			# the sets have to always be saved because the tm_N files are not otherwise taken into account
			self._save_sets()
		return True

	def __getstate__(self):
		# avoid saving self.sets
		return {'version': self.version, 'max_size': self.max_size, 'books': self.books,
		        'num_books': self.num_books, 'atlas_book_lookup': self.atlas_book_lookup}

	def _save_metadata(self):
		self.log.info('Saving metadata')
		path = PATHS.ATLAS_METADATA_PATH
		if not os.path.exists(os.path.dirname(path)):
			os.makedirs(os.path.dirname(path))
		with open(path, 'wb') as file:
			pickle.dump(self, file)
		self.log.info('Finished saving metadata')

	@classmethod
	def check_files(cls):
		"""Check that the required atlas files exist."""
		paths = [
			PATHS.ACTION_SETS_JSON_FILE,
			PATHS.ATLAS_DB_PATH,
			PATHS.TILE_SETS_JSON_FILE,
		]
		for path in paths:
			if not os.path.exists(path):
				return False

		# verify that the combined images exist
		db = DbReader(':memory:')
		with open(PATHS.ATLAS_DB_PATH) as f:
			db.execute_script(f.read())
		for db_row in db("SELECT atlas_path FROM atlas"):
			if not os.path.exists(db_row[0]):
				return False
		return True

	@classmethod
	def load(cls, max_size):
		if not cls.check_files():
			cls.log.info('Some required atlas file missing.')
			return None

		if not os.path.exists(PATHS.ATLAS_METADATA_PATH):
			cls.log.info('Old atlas metadata cache not found.')
			return None

		cls.log.info('Loading the metadata cache')
		with open(PATHS.ATLAS_METADATA_PATH, 'rb') as file:
			data = pickle.load(file)

			if data.version != cls.current_version:
				cls.log.info('Old metadata version %d (current %d)', data.version, cls.current_version)
				return None

			if data.max_size != max_size:
				cls.log.info('The desired max_size has changed from %d to %d', data.max_size, max_size)
				return None

			cls.log.info('Successfully loaded the metadata cache')
			return data

	@classmethod
	def clear_everything(cls):
		"""Delete all known atlas-related files."""
		paths = []
		paths.append(PATHS.ATLAS_METADATA_PATH)
		paths.append(PATHS.ATLAS_DB_PATH)
		paths.append(PATHS.ACTION_SETS_JSON_FILE)
		paths.append(PATHS.TILE_SETS_JSON_FILE)
		paths.extend(glob.glob(os.path.join(PATHS.ATLAS_FILES_DIR, '*.png')))

		# delete everything
		for path in paths:
			if not os.path.exists(path):
				continue
			cls.log.info('Deleting %s', path)
			os.unlink(path)


if __name__ == '__main__':
	args = sys.argv[1:]
	if len(args) != 1:
		print('Usage: python3 generate_atlases.py max_size')
		exit(1)

	max_size = int(math.pow(2, int(math.log(int(args[0]), 2))))

	updated = False
	try:
		generator = AtlasGenerator.load(max_size)
		if generator is not None:
			updated = generator.update()
	except Exception:
		traceback.print_exc()

	if not updated:
		AtlasGenerator.clear_everything()
		generator = AtlasGenerator(max_size)
		generator.recreate()
