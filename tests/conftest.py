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
	parser.addoption('--gui-tests', action='store_true', help='include gui tests')


def pytest_configure(config):
	config.addinivalue_line('markers', 'long: mark test as long-running')
	# The import hook is already installed at module import time (bottom of
	# this file); finish wiring the dummy fife into horizons now.
	_setup_fife_dummy()


def pytest_runtest_setup(item):
	"""
	Called for every test, here we skip expensive tests from the default test run.
	"""
	# Skip tests marked as long unless specified otherwise on the command line
	marker = item.get_closest_marker('long')
	if marker is not None and not item.config.getoption('--long-tests'):
		pytest.skip('test is long running')

	# Skip gui tests unless specified otherwise on the command line
	marker = item.get_closest_marker('gui_test')
	if marker is not None and not item.config.getoption('--gui-tests'):
		pytest.skip('test is gui test')


# Basic test setup, installs global mock for fife so we can run gui/game tests.
#
# This must run before any import of game or test code that references the real
# `fife` module. It is invoked from pytest_configure (above) and guarded by a
# flag in case it is triggered more than once.

FIFE_MOCK_INSTALLED = False


def _install_fife_import_hook():
	"""
	Install a global import hook so every `import fife*` yields a dummy module,
	keeping tests independent of (and unable to touch) the real engine.
	"""
	if any(isinstance(f, type) and f.__name__ == 'FifeDummyFinder' for f in sys.meta_path):
		return  # already installed

	from tests.dummy import Dummy

	class FifeDummyFinder(PathFinder):
		@staticmethod
		def find_spec(fullname, path, target=None):
			if fullname.startswith('fife'):
				return ModuleSpec(fullname, DummyLoader())

	class DummyLoader(Loader):
		# Modern loader protocol: the legacy load_module() hook was removed in
		# Python 3.12+, and its absence would make create_module()'s default
		# build a real (empty) module instead of a Dummy.
		@staticmethod
		def create_module(spec):
			return Dummy()

		@staticmethod
		def exec_module(module):
			pass

	sys.meta_path.insert(0, FifeDummyFinder())


def _setup_fife_dummy():
	"""
	Point horizons at the dummy fife and finish initialisation (user dirs, i18n).
	"""
	global FIFE_MOCK_INSTALLED
	if FIFE_MOCK_INSTALLED:
		return

	import horizons.globals
	import fife
	horizons.globals.fife = fife.fife

	from horizons.util import create_user_dirs
	create_user_dirs()

	import horizons.i18n
	horizons.i18n.change_language()

	FIFE_MOCK_INSTALLED = True


# Install the import hook at module import time (not in pytest_configure):
# pytest loads child conftests (tests/game, tests/unittests) that import
# `horizons.main` -> `fife` during conftest collection, which happens BEFORE
# pytest_configure. This parent conftest is imported first, so installing the
# hook here makes it active before any child conftest imports fife.
_install_fife_import_hook()
