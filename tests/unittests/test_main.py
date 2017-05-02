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

from unittest import mock

import horizons.main
from horizons.util.cmdlineoptions import get_option_parser
from tests.unittests import TestCase


class TestHorizonsMain(TestCase):
	"""
	Test all things related to the horizons.main module.
	"""
	def setUp(self):
		self.mock_fife_patcher = mock.patch('horizons.engine.Fife')
		self.mock_fife = self.mock_fife_patcher.start()
		self.mock_set_debug_log_patcher = mock.patch('horizons.main.set_debug_log')
		self.mock_set_debug_log_patcher.start()
		self.mock_gui_patcher = mock.patch('horizons.main.Gui')
		self.mock_gui_patcher.start()

	def tearDown(self):
		self.mock_gui_patcher.stop()
		self.mock_set_debug_log_patcher.stop()
		self.mock_fife_patcher.stop()

	@staticmethod
	def start_game(*args):
		options = get_option_parser().parse_args(list(args) + ['--no-atlas-generation'])[0]
		horizons.main.start(options)

	@mock.patch('tests.gui.logger.setup_gui_logger')
	def test_sets_up_gui_logger(self, mock_setup_gui_logger):
		"""
		Make sure the gui logger is setup when starting UH with --gui-log.

		We need some tricks here because horizons.main has some inline imports that would
		trigger the normal Fife setup. By mocking setup_gui_logger with a special
		exception, we quit the startup process but can still assert that is was called.
		"""
		mock_setup_gui_logger.side_effect = Exception('i was called')

		with self.assertRaisesRegex(Exception, 'i was called'):
			self.start_game('--gui-log')

	@mock.patch('horizons.main.start_singleplayer')
	def test_start_scenario(self, mock_start_singleplayer):
		"""
		Test that a specific scenario can be started from the command line.
		"""
		instance = self.mock_fife.return_value
		instance.get_locale.return_value = 'de'

		self.start_game('--start-scenario', 'tutorial')

		options = mock_start_singleplayer.call_args[0][0]
		assert options.is_scenario
		assert not options.is_map
		assert options.game_identifier == 'content/scenarios/tutorial_de.yaml'
