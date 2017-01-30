#!/usr/bin/env python3

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

from tests.dummy import Dummy

try:
	import pytest
except ImportError:
	print('The pytest package is needed to run the UH tests.')
	sys.exit(1)


def mock_fife():
	"""
	Using a custom import hook, we catch all imports of fife and provide a
	dummy module.
	"""
	from importlib.abc import MetaPathFinder, Loader
	from importlib.machinery import PathFinder, ModuleSpec

	class Finder(PathFinder):
		@classmethod
		def find_spec(cls, fullname, path, target=None):
			if fullname.startswith('fife'):
				return ModuleSpec(fullname, DummyLoader())
			return PathFinder.find_spec(fullname, path, target)

	class DummyLoader(Loader):
		def load_module(self, module):
			sys.modules.setdefault(module, Dummy())

	sys.meta_path = [Finder]



def setup_horizons():
	"""
	Get ready for testing.
	"""

	# This needs to run at first to avoid that other code gets a reference to
	# the real fife module
	mock_fife()

	# set global reference to fife
	import horizons.globals
	import fife
	horizons.globals.fife = fife.fife

	from run_uh import create_user_dirs
	create_user_dirs()

	import horizons.i18n
	horizons.i18n.change_language()


if __name__ == '__main__':
	gettext.install('') # no translations here

	setup_horizons()

	sys.exit(pytest.main())
