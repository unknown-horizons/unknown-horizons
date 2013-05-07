#!/usr/bin/env python2

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

import gettext
import sys

try:
	import nose
except ImportError:
	print 'The nose package is needed to run the UH tests.'
	sys.exit(1)

try:
	import mock
except ImportError:
	print 'The mock package is needed to run the UH tests.'
	sys.exit(1)


from horizons.ext.dummy import Dummy


def mock_fife():
	"""
	Using a custom import hook, we catch all imports of fife and provide a
	dummy module.
	"""
	class Importer(object):

		def find_module(self, fullname, path=None):
			if fullname.startswith('fife'):
				return self

			return None

		def load_module(self, name):
			mod = sys.modules.setdefault(name, Dummy())
			return mod

	sys.meta_path = [Importer()]

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


if __name__ == '__main__':
	gettext.install('', unicode=True) # no translations here

	setup_horizons()

	from tests.gui import GuiTestPlugin
	from tests.utils import ReRunInfoPlugin
	nose.run(defaultTest='tests', addplugins=[GuiTestPlugin(), ReRunInfoPlugin()])
