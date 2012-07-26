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

import logging
import os.path

try:
	import cPickle as pickle
except:
	import pickle

class YamlCacheStorage(object):
	"""
	Store the YamlCache data in a cache.

	An instance of this class provides a implements a cache that always has all the data
	in memory. It tries to also load the data from disk and write it back on disk but
	if it fails then it just ignores the errors and keeps working.
	"""

	log = logging.getLogger("yamlcachestorage")

	# Increment this when the users of this class change the way they use it.
	version = 1

	def __init__(self, filename):
		super(YamlCacheStorage, self).__init__()
		self._filename = filename
		self._data = {}

	@classmethod
	def _validate(cls, data):
		"""Make sure data is a tuple (version no, _data dict) with the right version."""
		if not isinstance(data, tuple):
			return False
		if len(data) != 2:
			return False
		if not isinstance(data[1], dict):
			return False
		return data[0] == cls.version

	def _reload(self):
		"""Load the cache from disk if possible. Create an empty cache otherwise."""
		if os.path.exists(self._filename):
			self.log.debug('%s._reload(): loading cache from disk', self)
			file = open(self._filename)
			try:
				data = pickle.load(file)
				if not self._validate(data):
					raise RuntimeError('Bad YamlCacheStorage data format')
				self._data = data[1]
			finally:
				file.close()
			self.log.debug('%s._reload(): successfully loaded cache from disk', self)
		else:
			self._clear()

	def _clear(self):
		"""Clear the cache in memory."""
		self.log.debug('%s._clear(): creating a new cache', self)
		self._data = {}

	@classmethod
	def open(cls, filename):
		"""Open the cache specified by the file name or create an empty one otherwise."""
		cls.log.debug("YamlCacheStorage.open('%s')", filename)
		obj = YamlCacheStorage(filename)
		try:
			obj._reload()
		except Exception as e:
			# Ignore all exceptions because loading the cache from disk is not critical.
			e = unicode(str(e), errors='replace')
			cls.log.warning("Warning: Failed to open %s as cache: %s\nThis warning is expected when upgrading from old versions.\n" % (filename, e))
			obj._clear()
		return obj

	def sync(self):
		"""Write the file to disk if possible. Do nothing otherwise."""
		try:
			file = open(self._filename, 'wb')
			try:
				pickle.dump((self.version, self._data), file)
				self.log.debug('%s.sync(): success', self)
			finally:
				file.close()
		except Exception as e:
			# Ignore all exceptions because saving the cache on disk is not critical.
			self.log.warning("Warning: Unable to save cache into %s: %s" % (self._filename, unicode(e)))

	def close(self):
		"""Write the file to disk if possible and then invalidate the object in memory."""
		self.log.debug('%s.close()', self)
		self.sync()
		self._filename = None
		self._data = None

	def __getitem__(self, key):
		"""This function enables the following syntax: cache[key]"""
		self.log.debug("%s.__getitem__('%s')", self, key)
		return self._data[key]

	def __setitem__(self, key, value):
		"""This function enables the following syntax: cache[key] = value"""
		self.log.debug("%s.__setitem__('%s', data excluded)", self, key)
		self._data[key] = value

	def __contains__(self, item):
		"""This function enables the following syntax: item in cache"""
		self.log.debug("%s.__contains__('%s')", self, item)
		return item in self._data

	def __str__(self):
		return "YamlCacheStorage('%s', %d items)" % (self._filename, len(self._data))
