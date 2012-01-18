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

import os
import shelve
import yaml
import threading

try:
	from yaml import CSafeLoader as SafeLoader
except ImportError:
	from yaml import SafeLoader

# make SafeLoader allow unicode
def construct_yaml_str(self, node):
	return self.construct_scalar(node)
SafeLoader.add_constructor(u'tag:yaml.org,2002:python/unicode', construct_yaml_str)

from horizons.constants import PATHS

class YamlCache(object):
	"""Loads and caches YAML files in a shelve.
	Threadsafe.
	"""
	cache = {}
	virgin = True
	dirty = False
	yaml_cache = os.path.join(PATHS.USER_DIR, 'yamldata.cache')

	lock = threading.Lock()

	@classmethod
	def get_file(cls, filename):
		if cls.virgin:
			cls._read_bin_file()
			cls.virgin = False
		data = cls.get_yaml_file(filename)
		if cls.dirty:
			cls._write_bin_file()
			cls.dirty = False
		return data

	@classmethod
	def get_yaml_file(cls, filename):
		# calc the hash
		f = open(filename, 'r')
		h = hash(f.read())
		f.seek(0)
		# check for updates or new files
		if (filename in cls.cache and \
				cls.cache[filename][0] != h) or \
			 (not filename in cls.cache):
			cls.dirty = True
			cls.cache[filename] = (h, yaml.load( f, Loader = SafeLoader ) )

		return cls.cache[filename][1]

	@classmethod
	def _write_bin_file(cls):
		cls.lock.acquire()
		try:
			s = shelve.open(cls.yaml_cache)
		except UnicodeError as e:
			# this can happen with unicode characters in the name, because the bdb module on win
			# converts it internally to ascii and fails to open the file. Since this is just a cache,
			# we don't require it for the game to function, there is just a slight speed penality
			# on every startup
			print "Warning: failed to open "+cls.yaml_cache+": "+unicode(e)
			return
		for key, value in cls.cache.iteritems():
			# TODO : manage unicode problems (paths with accents ?)
			s[str(key)] = value # We have to decode it because _user_dir is encoded in constants
		s.close()
		cls.lock.release()

	@classmethod
	def _read_bin_file(cls):
		cls.lock.acquire()
		try:
			s = shelve.open(cls.yaml_cache)
		except ImportError:
			# Some python distributions used to use the bsddb module as underlying shelve.
			# The bsddb module is now deprecated since 2.6 and is not present in some 2.7 distributions.
			# Therefore, the line above will yield an ImportError if it has been executed with
			# a python supporting bsddb and now is executed again with python with no support for it.
			# Since this may also be caused by a different error, we just try again once.
			os.remove(cls.yaml_cache)
			s = shelve.open(cls.yaml_cache)
		except UnicodeError as e:
			print "Warning: failed to open "+cls.yaml_cache+": "+unicode(e)
			return # see _write_bin_file
		except Exception as e:
			# same as for the ImportError. If there is an old database file that was created with a
			# deprecated dbm library, opening it will fail with an obscure exception, so we delete it
			# and simply retry.
			print "Warning: you probably have an old cache file; deleting and retrying"
			os.remove(cls.yaml_cache)
			s = shelve.open(cls.yaml_cache)

		for key, value in s.iteritems():
			cls.cache[key] = value
		s.close()
		cls.lock.release()
