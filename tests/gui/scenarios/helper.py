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

from horizons.scenario import CONDITIONS

var_eq = CONDITIONS.get('var_eq')
settlement_res_stored_greater = CONDITIONS.get('settlement_res_stored_greater')
settler_level_greater = CONDITIONS.get('settler_level_greater')


def assert_win(gui):
	"""Returns once the scenario was won."""
	while True:
		if getattr(gui.session, '_scenariotest_won', False):
			break
		gui.run()


def assert_defeat(gui):
	"""Returns once the scenario was lost."""
	while True:
		if getattr(gui.session, '_scenariotest_lose', False):
			break
		gui.run()


def assert_goal_reached(gui, goal):
	"""Returns once a certain goal was reached."""
	while True:
		if (hasattr(gui.session, '_scenariotest_goals') and
			gui.session._scenariotest_goals and
			gui.session._scenariotest_goals[-1] == goal):
			break
		gui.run()


def wait_and_close_logbook(gui):
	"""Wait for the logbook to show and close it immediately."""
	while not gui.find('captains_log'):
		gui.run()

	gui.trigger('captains_log/okButton')
