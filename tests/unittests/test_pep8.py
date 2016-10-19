# -*- coding: utf-8 -*-

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

from unittest import TestCase

import pep8


class TestCodeFormat(TestCase):
	"""automatical test for code format use pep8"""

	def test_pep8_dir_tests(self):
		"""Test that code conform to PEP8 test all files"""
		tests = [
			# http://pep8.readthedocs.org/en/latest/intro.html#error-codes
			'W2',    # whitespace warnings
		]

		checker = pep8.StyleGuide(select=tests, paths=['horizons', 'tests', 'development'], reporter=pep8.StandardReport)
		report = checker.check_files()

		self.assertEqual(report.total_errors, 0,
			"Found code style errors (and warnings).")

