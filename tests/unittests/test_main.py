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

import mock

import horizons.main
from horizons.util.cmdlineoptions import get_option_parser
from tests.unittests import TestCase


class TestHorizonsMain(TestCase):
	"""
	Test all things related to the horizons.main module.
	"""
	@mock.patch('horizons.engine.Fife')
	@mock.patch('horizons.main.set_debug_log')
	@mock.patch('tests.gui.logger.setup_gui_logger')
	def test_sets_up_gui_logger(self, mock_setup_gui_logger, mock_set_debug_log, mock_fife):
		"""
		Make sure the gui logger is setup when starting UH with --gui-log.

		We need some tricks here because horizons.main has some inline imports that would
		trigger the normal Fife setup. By mocking setup_gui_logger with a special
		exception, we quit the startup process but can still assert that is was called.
		"""
		mock_setup_gui_logger.side_effect = Exception('i was called')

		options = get_option_parser().parse_args(['--gui-log', '--no-atlas-generation'])[0]
		with self.assertRaisesRegex(Exception, 'i was called'):
			horizons.main.start(options)
