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

from horizons.scenario import ACTIONS

# Patch scenario actions for easier detection


def do_win(session):
	session._scenariotest_won = True


def do_lose(session):
	session._scenariotest_lose = True


def goal_reached(session, goal):
	if hasattr(session, '_scenariotest_goals'):
		session._scenariotest_goals.append(goal)
	else:
		session._scenariotest_goals = [goal]


# We replace the code object on the original functions because replacing all
# references on these functions in the scenario manager is too cumbersome
ACTIONS.get('win').__code__ = do_win.__code__
ACTIONS.get('lose').__code__ = do_lose.__code__
ACTIONS.get('goal_reached').__code__ = goal_reached.__code__
