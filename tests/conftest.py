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

import pytest


def pytest_addoption(parser):
	parser.addoption('--long-tests', action='store_true', help='include long-running tests')


def pytest_configure(config):
	config.addinivalue_line('markers', 'long: mark test as long-running')


def pytest_runtest_setup(item):
	# Skip tests marked as long unless specified otherwise on the command line
	envmarker = item.get_marker('long')
	if envmarker is not None:
		if not item.config.getoption('--long-tests'):
			pytest.skip('test is long running')
