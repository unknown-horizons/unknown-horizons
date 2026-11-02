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

"""Headless regression tests for tutorial scenario mechanics.

No GUI, no FIFE, so they finish in milliseconds. They cover the two behaviours
that made the GUI tutorial test hang:

* a tent costs two boards and an unaffordable build is silently dropped -- the
  tutorial placed three tents with only four boards, then waited forever for the
  third one (goal 34)
* variable comparisons are checked in the same tick the variable is set (queued,
  never polled), so a goal such as 46 can be reached straight after goal 43
"""

import textwrap

from horizons.command.building import Build
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import BUILDINGS, RES
from horizons.scenario.actions import ACTIONS
from horizons.scenario.conditions import CONDITIONS
from horizons.scenario.scenarioeventhandler import ScenarioEventHandler
from tests.game import game_test, settle

# Positions for the tents, spaced out so they do not overlap.
TENT_POSITIONS = [(22, 22), (25, 22), (28, 22)]


def _boards(settlement):
	return settlement.get_component(StorageComponent).inventory[RES.BOARDS]


def _place_tents(session, island, settlement, count):
	"""Place *count* tents and return how many actually got built."""
	built = 0
	for x, y in TENT_POSITIONS[:count]:
		if Build(BUILDINGS.RESIDENTIAL, x, y, island, settlement=settlement)(session.world.player):
			built += 1
	return built


@game_test()
def test_tent_costs_two_boards(s, p):
	"""A tent costs exactly two boards; building is refused without them."""
	settlement, island = settle(s)

	# Replace the boards `settle` grants with a known amount.
	inv = settlement.get_component(StorageComponent).inventory
	inv.alter(RES.BOARDS, -_boards(settlement))
	inv.alter(RES.BOARDS, 4)

	# Four boards suffice for two tents but not three.
	assert _place_tents(s, island, settlement, 2) == 2
	assert _boards(settlement) == 0
	assert _place_tents(s, island, settlement, 3) == 0


@game_test()
def test_three_tents_need_six_boards(s, p):
	"""Six boards (the amount the test waits for) build all three tents."""
	settlement, island = settle(s)

	inv = settlement.get_component(StorageComponent).inventory
	inv.alter(RES.BOARDS, -_boards(settlement))
	inv.alter(RES.BOARDS, 6)

	assert _place_tents(s, island, settlement, 3) == 3
	assert _boards(settlement) == 0


@game_test()
def test_counted_tents_are_connected_neighbours(s, p):
	"""Three tents placed side by side count as three buildings."""
	settlement, island = settle(s)
	inv = settlement.get_component(StorageComponent).inventory
	inv.alter(RES.BOARDS, -_boards(settlement))
	inv.alter(RES.BOARDS, 6)

	assert _place_tents(s, island, settlement, 3) == 3
	assert len(settlement.buildings_by_id[BUILDINGS.RESIDENTIAL]) == 3


SCENARIO_YAML = textwrap.dedent("""
    events:
    - # sets tutorial_progress = 43
      actions:
       - type: set_var
         arguments: ["tutorial_progress", 43]
      conditions:
       - type: var_gt
         arguments: ["tutorial_progress", 42]

    - # cascade target: reachable once tutorial_progress > 42
      actions:
       - type: set_var
         arguments: ["cascade_fired", 1]
      conditions:
       - type: var_gt
         arguments: ["tutorial_progress", 42]

    metadata: {}
    """)


def _new_scenario_handler(session, yaml):
	handler = ScenarioEventHandler(session, None)
	handler._apply_data(handler._parse_yaml(yaml))
	# Replace the session's dummy handler.
	session.scenario_eventhandler = handler
	handler.start()
	return handler


@game_test()
def test_var_cascade_fires_in_one_tick(s, p):
	"""A var_gt goal is reached in the tick another goal set the var.

	``set_var`` queues the variable checks with ``run_in=0``; they run at the end
	of the current scheduler tick. So a comparison sees the new value within one
	tick, which is how the tutorial's farm goal (46) is reached straight after
	the tier goal (43).
	"""
	handler = _new_scenario_handler(s, SCENARIO_YAML)

	# Simulate goal 43's action, which sets tutorial_progress via set_var.
	handler._scenario_variables['tutorial_progress'] = 42
	ACTIONS.get('set_var')(s, 'tutorial_progress', 43)
	assert handler._scenario_variables['tutorial_progress'] == 43
	# Checks are only queued, so nothing has fired yet.
	assert handler._scenario_variables.get('cascade_fired') is None

	# One tick drains the queue and fires the cascade event.
	s.run(ticks=1)
	assert handler._scenario_variables.get('cascade_fired') == 1

	handler.end()


@game_test()
def test_var_conditions_are_only_notified_by_set_var(s, p):
	"""Control: variable checks rely on set_var and are not polled.

	The periodic check only covers conditions registered as periodic, and the
	variable comparisons are not among them. A plain assignment is never noticed;
	the value must be set through set_var, as the tutorial does.
	"""
	assert 'var_gt' not in CONDITIONS.check_periodically
	assert 'var_eq' not in CONDITIONS.check_periodically

	handler = _new_scenario_handler(s, SCENARIO_YAML)
	handler._scenario_variables['tutorial_progress'] = 43

	# Several periodic intervals pass without the event firing.
	s.run(seconds=3 * ScenarioEventHandler.CHECK_CONDITIONS_INTERVAL)
	assert handler._scenario_variables.get('cascade_fired') is None

	# Notifying the handler manually (as set_var does) fires it at once.
	handler.check_events('var_gt')
	assert handler._scenario_variables.get('cascade_fired') == 1

	handler.end()
