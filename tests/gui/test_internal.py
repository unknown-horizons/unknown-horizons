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

import functools
import os

import pytest

from horizons.scheduler import Scheduler
from tests.gui import gui_test


@gui_test(use_dev_map=True)
def test_trivial(gui):
	"""Does nothing to see if test setup works."""
	pass


@gui_test(use_dev_map=True, _user_dir=os.path.join("test_settings", ".unknown-horizons"))
def test_update_settings(gui):
	"""Does nothing to see if the settings update works."""
	pass


@gui_test(use_dev_map=True)
def test_run_for_x_seconds(gui):
	"""Test that running the game X seconds works."""

	start_tick = Scheduler().cur_tick
	gui.run(seconds=20)
	difference = Scheduler().cur_tick - start_tick

	expected = Scheduler().get_ticks(20)

	deviation = (difference - expected) / difference
	assert deviation < 0.05, 'Expected max 0.05 deviation, got {}'.format(deviation)


@gui_test(use_fixture='boatbuilder')
def test_trigger(gui):
	"""Test the different ways to trigger an action in a gui."""

	assert not gui.find('captains_log')

	# Specify event name and group name
	gui.trigger('mainhud/logbook', 'action/default')
	assert gui.find('captains_log')
	gui.trigger('captains_log/okButton', 'action/default')
	assert not gui.find('captains_log')

	# Leave out group name
	gui.trigger('mainhud/logbook', 'action')
	assert gui.find('captains_log')
	gui.trigger('captains_log/okButton', 'action')
	assert not gui.find('captains_log')

	# Leave out event name
	gui.trigger('mainhud/logbook')
	assert gui.find('captains_log')
	gui.trigger('captains_log/okButton')
	assert not gui.find('captains_log')

	# Select mainsquare and show production overview to test
	# if mouseClicked and action are handled the same
	assert not gui.find('production_overview')

	gui.cursor_click(53, 12, 'left')
	gui.trigger('tab_account/show_production_overview', 'mouseClicked')
	assert gui.find('production_overview')
	gui.trigger('production_overview/okButton', 'action')
	assert not gui.find('production_overview')

	# Leave out event name, it will try action at first and fallback
	# to mouseClicked
	gui.trigger('tab_account/show_production_overview')
	assert gui.find('production_overview')
	gui.trigger('production_overview/okButton')
	assert not gui.find('production_overview')


@gui_test(timeout=60)
def test_dialog(gui):
	"""Test handling of a dialog."""

	assert not gui.find('popup_window')

	def func():
		assert gui.find('popup_window')
		gui.trigger('popup_window/okButton')

	with gui.handler(func):
		gui.trigger('menu/quit_button')


@pytest.mark.xfail(strict=True)
@gui_test(timeout=60)
def test_failing(gui):
	"""
	Test whether a failure of the test is correctly detected.

	NOTE: We're using XFAIL here, since the failure of the test is expected. If suddenly this
	test passes, the test suite will fail.
	"""
	1 / 0
