# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from decorators import cached

class DbReader(object):
	"""Class that handles connections to sqlite databases
	@param file: str containing the database file."""
	def __init__(self, dbfile):
		self.connection = sqlite3.connect(dbfile)
		self.connection.isolation_level = None
		self.connection.text_factory = str
		def regexp(expr, item):
			"""
			@param expr:
			@param item:
			"""
			r = re.compile(expr)
			return r.match(item) is not None
		self.connection.create_function("regexp", 2, regexp)
		self.cur = self.connection.cursor()

	def __call__(self, command, *args):
		"""Executes a sql command.
		@param command: str containing the raw sql command, with ? as placeholders for values (eg. SELECT ? FROM ?). command must not end with ';', it's added automatically here.
		@param args: tuple containing the values to add into the command.
		"""
		assert not command.endswith(";")
		command = '%s;' % command
		self.cur.execute(command, args)
		return SqlResult(self.cur.fetchall(), None if self.cur.rowcount == -1 else self.cur.rowcount, self.cur.lastrowid)

	@cached
	def cached_query(self, command, *args):
		"""Executes a sql command and saves it's result in a dict.
		@params, return: same as in __call__"""
		return self(command, *args)

	def execute_script(self, script):
		"""Executes a multiline script.
		@param script: multiline str containing an sql script."""
		return self.cur.executescript(script)

class SqlError(object):
	"""Represents a SQL error
	@param error: str error description.
	"""
	def __init__(self, error):
		self.success, self.error, self.rows, self.affected, self.id = False, error, None, None, None

class SqlResult(object):
	"""Represents a SQL result
	@param rows: the rows that were returned by the sql query
	@param affected: int number of rows affected by the sql query
	@param id: int id of the sqlresult(lastrowid of the curser)
	"""
	def __init__(self, rows, affected, ident):
		self.success, self.error, self.rows, self.affected, self.id = True, None, rows, affected, ident

	def __getattr__(self, name):
		"""
		@param name: key in self.rows, whose corresponding value is then returned.
		"""
		return getattr(self.rows, name)
	def __add__(self, *args, **kwargs):
		return self.rows.__add__(*args, **kwargs)
	def __contains__(self, *args, **kwargs):
		return self.rows.__contains__(*args, **kwargs)
	def __delitem__(self, *args, **kwargs):
		return self.rows.__delitem__(*args, **kwargs)
	def __delslice__(self, *args, **kwargs):
		return self.rows.__delslice__(*args, **kwargs)
	def __eq__(self, *args, **kwargs):
		return self.rows.__eq__(*args, **kwargs)
	def __ge__(self, *args, **kwargs):
		return self.rows.__ge__(*args, **kwargs)
	def __getitem__(self, *args, **kwargs):
		return self.rows.__getitem__(*args, **kwargs)
	def __getslice__(self, *args, **kwargs):
		return self.rows.__getslice__(*args, **kwargs)
	def __gt__(self, *args, **kwargs):
		return self.rows.__gt__(*args, **kwargs)
	def __hash__(self, *args, **kwargs):
		return self.rows.__hash__(*args, **kwargs)
	def __iadd__(self, *args, **kwargs):
		return self.rows.__iadd__(*args, **kwargs)
	def __imul__(self, *args, **kwargs):
		return self.rows.__imul__(*args, **kwargs)
	def __iter__(self, *args, **kwargs):
		return self.rows.__iter__(*args, **kwargs)
	def __le__(self, *args, **kwargs):
		return self.rows.__le__(*args, **kwargs)
	def __len__(self, *args, **kwargs):
		return self.rows.__len__(*args, **kwargs)
	def __lt__(self, *args, **kwargs):
		return self.rows.__lt__(*args, **kwargs)
	def __mul__(self, *args, **kwargs):
		return self.rows.__mul__(*args, **kwargs)
	def __ne__(self, *args, **kwargs):
		return self.rows.__ne__(*args, **kwargs)
	def __repr__(self, *args, **kwargs):
		return self.rows.__repr__(*args, **kwargs)
	def __reversed__(self, *args, **kwargs):
		return self.rows.__reversed__(*args, **kwargs)
	def __rmul__(self, *args, **kwargs):
		return self.rows.__rmul__(*args, **kwargs)
	def __setitem__(self, *args, **kwargs):
		return self.rows.__setitem__(*args, **kwargs)
	def __setslice__(self, *args, **kwargs):
		return self.rows.__setslice__(*args, **kwargs)
