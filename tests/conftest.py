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

import gettext
import sys
from importlib.abc import Loader, MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder

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


# Basic test setup, installs global mock for fife so we can run gui/game tests.
#
# We need to run this code as soon as possible, before any import of game or test code happened,
# and `pytest_namespace` is one of the first things that runs. Because it is called for every
# plugin, we remember whether we installed the mock already.

FIFE_MOCK_INSTALLED = False

def pytest_namespace():
	"""
	This needs to run at first to avoid that other code gets a reference to the real fife
	module.
	"""
	global FIFE_MOCK_INSTALLED
	if FIFE_MOCK_INSTALLED:
		return

	def mock_fife():
		"""
		Using a custom import hook, we catch all imports of fife and provide a
		dummy module.
		"""
		from tests.dummy import Dummy

		class Finder(PathFinder):
			@classmethod
			def find_spec(cls, fullname, path, target=None):
				if fullname.startswith('fife'):
					return ModuleSpec(fullname, DummyLoader())
				return PathFinder.find_spec(fullname, path, target)

		class DummyLoader(Loader):
			def load_module(self, module):
				sys.modules.setdefault(module, Dummy())

		sys.meta_path.insert(0, Finder)


	mock_fife()

	import horizons.globals
	import fife
	horizons.globals.fife = fife.fife

	from run_uh import create_user_dirs
	create_user_dirs()

	import horizons.i18n
	horizons.i18n.change_language()

	FIFE_MOCK_INSTALLED = True
