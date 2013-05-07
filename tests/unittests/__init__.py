# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

import unittest

import horizons.globals
import horizons.main


class TestCase(unittest.TestCase):
	"""
	For each test, set up a new database.
	"""
	def setUp(self):
		self.db = horizons.main._create_main_db()

		# Truncate all tables. We don't want to rely on existing data.
		for (table_name, ) in self.db("SELECT name FROM sqlite_master WHERE type = 'table'"):
			self.db('DELETE FROM %s' % table_name)

		horizons.globals.db = self.db

	def tearDown(self):
		self.db.close()


_multiprocess_can_split_ = True
