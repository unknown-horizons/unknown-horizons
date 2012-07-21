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
import sys
import yaml
import threading
import logging

from horizons.constants import TIER, RES, UNITS, BUILDINGS, PATHS
from horizons.util.yamlcachestorage import YamlCacheStorage

try:
	from yaml import CSafeLoader as SafeLoader
except ImportError:
	from yaml import SafeLoader

# make SafeLoader allow unicode
def construct_yaml_str(self, node):
	return self.construct_scalar(node)
SafeLoader.add_constructor(u'tag:yaml.org,2002:python/unicode', construct_yaml_str)
SafeLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_str)


def parse_token(token, token_klass):
	"""Helper function that tries to parse a constant name.
	Does not do error detection, but passes unparseable stuff through.
	Allowed values: integer or token_klass.LIKE_IN_CONSTANTS
	@param token_klass: "TIER", "RES", "UNITS" or "BUILDINGS"
	"""
	classes = {'TIER': TIER, 'RES': RES, 'UNITS': UNITS, 'BUILDINGS': BUILDINGS}

	if isinstance(token, unicode):
		if token.startswith(token_klass):
			try:
				return getattr( classes[token_klass], token.split(".", 2)[1])
			except AttributeError as e: # token not defined here
				err =  "This means that you either have to add an entry in horizons/constants.py in the class %s for %s,\nor %s is actually a typo." % (token_klass, token, token)
				raise Exception( str(e) + "\n\n" + err +"\n" )

		else:
			return token
	else:
		return token # probably numeric already

def convert_game_data(data):
	"""Translates convenience symbols into actual game data usable by machines"""
	if isinstance(data, dict):
		return dict( [ convert_game_data(i) for i in data.iteritems() ] )
	elif isinstance(data, (tuple, list)):
		return type(data)( ( convert_game_data(i) for i in data) )
	else: # leaf
		data = parse_token(data, "TIER")
		data = parse_token(data, "RES")
		data = parse_token(data, "UNITS")
		data = parse_token(data, "BUILDINGS")
		return data


class YamlCache(object):
	"""Loads and caches YAML files in a persistent cache.
	Threadsafe.

	Use get_file for files to cache (default case) or load_yaml_data for special use cases (behaves like yaml.load).
	"""

	cache = None
	cache_filename = os.path.join(PATHS.USER_DIR, 'yamldata.cache')

	sync_scheduled = False

	lock = threading.Lock()

	log = logging.getLogger("yamlcache")

	@classmethod
	def load_yaml_data(self, string_or_stream):
		"""Use this instead of yaml.load everywhere in uh in case get_file isn't useable"""
		return yaml.load( string_or_stream, Loader=SafeLoader )

	@classmethod
	def get_file(cls, filename, game_data=False):
		"""Get contents of a yaml file
		@param filename: path to the file
		@param game_data: Whether this file contains data like BUILDINGS.LUMBERJACk to resolve
		"""

		# calc the hash
		f = open(filename, 'r')
		h = hash(f.read())
		f.seek(0)

		# check for updates or new files
		if cls.cache is None:
			cls._open_cache()

		yaml_file_in_cache = (filename in cls.cache and cls.cache[filename][0] == h)
		if not yaml_file_in_cache:
			data = cls.load_yaml_data( f )
			if game_data: # need to convert some values
				try:
					data = convert_game_data(data)
				except Exception as e:
					# add info about file
					to_add = "\nThis error happened in %s ." % filename
					e.args = ( e.args[0] + to_add, ) + e.args[1:]
					e.message = ( e.message + to_add )
					raise

			cls.lock.acquire()
			cls.cache[filename] = (h, data)
			if not cls.sync_scheduled:
				cls.sync_scheduled = True
				from horizons.extscheduler import ExtScheduler
				ExtScheduler().add_new_object(cls._do_sync, cls, run_in=1)
			cls.lock.release()

		return cls.cache[filename][1] # returns an object from the YAML

	@classmethod
	def _open_cache(cls):
		cls.lock.acquire()
		cls.cache = YamlCacheStorage.open(cls.cache_filename)
		cls.lock.release()

	@classmethod
	def _do_sync(cls):
		"""Only write to disc once in a while, it's too slow when done every time"""
		cls.lock.acquire()
		cls.sync_scheduled = False
		cls.cache.sync()
		cls.lock.release()
