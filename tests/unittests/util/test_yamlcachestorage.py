# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
import tempfile
import unittest

from horizons.util.yamlcachestorage import YamlCacheStorage


class YamlCacheStorageTest(unittest.TestCase):

	def setUp(self):
		super().setUp()
		self.tmp_file = tempfile.NamedTemporaryFile(delete=False)

	def tearDown(self):
		os.unlink(self.tmp_file.name)
		super().tearDown()

	def test_save_and_reopen(self):
		cache = YamlCacheStorage(self.tmp_file.name)
		cache['foo'] = 'bar'
		cache.sync()

		new_cache = YamlCacheStorage.open(self.tmp_file.name)
		self.assertEqual(new_cache['foo'], 'bar')
