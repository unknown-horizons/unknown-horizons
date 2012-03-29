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

import sqlite3
import re

from horizons.util.python import decorators

class DbReader(object):
	"""Class that handles connections to sqlite databases
	@param file: str containing the database file."""
	def __init__(self, dbfile):
		self.connection = sqlite3.connect(dbfile)
		self.connection.isolation_level = None
		def regexp(expr, item):
			r = re.compile(expr)
			return r.match(item) is not None
		self.connection.create_function("regexp", 2, regexp)
		self.cur = self.connection.cursor()

	@decorators.make_constants()
	def __call__(self, command, *args):
		"""Executes a sql command.
		@param command: str containing the raw sql command, with ? as placeholders for values (eg. SELECT ? FROM ?). command must not end with ';', it's added automatically here.
		@param args: tuple containing the values to add into the command.
		"""
		assert not command.endswith(";")
		command = '%s;' % command
		self.cur.execute(command, args)
		# fetch rows only on select statements, PEP-249 specifies that an error should be
		# raised when fetching results on other statements that produced no results. This
		# does not happen on CPython, but on PyPy
		if command.startswith("SELECT"):
			return self.cur.fetchall()
		else:
			return []

	@decorators.cachedmethod
	def cached_query(self, command, *args):
		"""Executes a sql command and saves its result in a dict.
		@params, return: same as in __call__"""
		return self(command, *args)

	def execute_many(self, command, parameters):
		"""Executes a sql command for each sequence or mapping
		found in parameters.
		@param command: same as in __call__
		@param parameters: sequence or iterator"""
		return self.cur.executemany(command, parameters)

	def execute_script(self, script):
		"""Executes a multiline script.
		@param script: multiline str containing an sql script."""
		return self.cur.executescript(script)

	def close(self):
		"""Closes the db"""
		self.connection.close()
