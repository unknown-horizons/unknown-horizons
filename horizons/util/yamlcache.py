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
import traceback
import logging

from horizons.constants import TIER, RES, UNITS, BUILDINGS, PATHS

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


class DummyShelve(dict):
	"""Implements the methods we use on a shelve but is really just a dict for
	when we are unable to open a shelve.
	"""
	def sync(self):
		"""No need to do that, because we are just a dummy shelve."""
		pass


class YamlCache(object):
	"""Loads and caches YAML files in a shelve.
	Threadsafe.
	"""
	cache = None
	cache_filename = os.path.join(PATHS.USER_DIR, 'yamldata.cache')

	sync_scheduled = False

	lock = threading.Lock()

	log = logging.getLogger("yamlcache")

	@classmethod
	def get_file(cls, filename, game_data=False):
		# calc the hash
		f = open(filename, 'r')
		h = hash(f.read())
		f.seek(0)
		# check for updates or new files
		if cls.cache is None:
			cls._open_cache()

		if isinstance(filename, unicode):
			filename = filename.encode('utf8') # shelve needs str keys

		def handle_get_file_error(e, release):
			# when something unexpected happens, shelve does not guarantee anything.
			# since crashing on any access is part of the specified behaviour, we need to handle it.
			# cf. http://bugs.python.org/issue14041
			cls.log.exception('Warning: Can\'t write to shelve: '+unicode(e))
			# delete cache and try again
			if os.path.exists(cls.cache_filename):
				os.remove(cls.cache_filename)
			cls.cache = None
			if release:
				cls.lock.release()
			return cls.get_file(filename, game_data=game_data)

		try:
			yaml_file_in_cache = (filename in cls.cache and cls.cache[filename][0] == h)
		except Exception as e:
			return handle_get_file_error(e, release=False)

		if not yaml_file_in_cache:
			data = yaml.load( f, Loader = SafeLoader )
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
			try:
				cls.cache[filename] = (h, data)
			except Exception as e:
				return handle_get_file_error(e, release=True)

			if not cls.sync_scheduled:
				cls.sync_scheduled = True
				from horizons.extscheduler import ExtScheduler
				ExtScheduler().add_new_object(cls._do_sync, cls, run_in=1)

			cls.lock.release()

		return cls.cache[filename][1]

	@classmethod
	def _open_cache(cls):
		cls.lock.acquire()
		try:
			cls.cache = shelve.open(cls.cache_filename)
		except UnicodeError as e:
			cls.log.exception("Warning: Failed to open "+cls.cache_filename+": "+unicode(e))
			# This can happen with unicode characters in the path because the bdb module
			# on win converts it internally to ascii, which fails
			# The shelve module therefore does not support writing to paths containing non-ascii characters in general,
			# which means we cannot store data persistently.
			cls.cache = DummyShelve()
		except Exception as e:
			# 2 causes for this:

			# Some python distributions used to use the bsddb module as underlying shelve.
			# The bsddb module is now deprecated since 2.6 and is not present in some 2.7 distributions.
			# Therefore, the line above will yield an ImportError if it has been executed with
			# a python supporting bsddb and now is executed again with python with no support for it.
			# Since this may also be caused by a different error, we just try again once.

			# If there is an old database file that was created with a
			# deprecated dbm library, opening it will fail with an obscure exception, so we delete it
			# and simply retry.
			cls.log.exception("Warning: You probably have an old cache file; deleting and retrying: "+unicode(e))
			if os.path.exists(cls.cache_filename):
				os.remove(cls.cache_filename)
			try:
				cls.cache = shelve.open(cls.cache_filename)
			except Exception as e:
				# If no persistant cache can be opened the game should still be
				# playable and not just crash.
				cls.log.exception("Warning: Failed to open %s as cache: %s" % (
									cls.cache_filename, unicode(e)))
				cls.cache = DummyShelve()
		cls.lock.release()


	@classmethod
	def _do_sync(cls):
		"""Only write to disc once in a while, it's too slow when done every time"""
		cls.lock.acquire()
		cls.sync_scheduled = False
		cls.cache.sync()
		cls.lock.release()