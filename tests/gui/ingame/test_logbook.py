# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from tests.gui import TestFinished, gui_test


@gui_test(use_dev_map=True, timeout=60)
def test_logbook(gui):
	"""
	Open the (empty) logbook.
	"""
	yield # test needs to be a generator for now

	gui.trigger('mainhud', 'logbook/action/default')

	logbook = gui.find(name='captains_log')
	assert logbook

	# Close it and confirm it's gone
	gui.trigger(logbook, 'okButton/action/default')
	assert gui.find(name='captains_log') is None

	yield TestFinished


@gui_test(use_fixture='boatbuilder', timeout=60)
def test_logbook_statistics(gui):
	"""Open the 3 three different statistic tabs in the logbook."""
	yield

	# Open statistics page in logbook
	gui.trigger('mainhud', 'logbook/action/default')
	gui.trigger('captains_log', 'statistics_rt/mouseClicked/default')

	# Open players/ships/settlements tabs
	gui.trigger('captains_log', 'stats_players/action/default')
	gui.trigger('captains_log', 'stats_ships/action/default')
	gui.trigger('captains_log', 'stats_settlements/action/default')

	yield TestFinished
