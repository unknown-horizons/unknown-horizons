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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
# ###################################################

from unittest.mock import Mock, patch

import pytest

from horizons.ai.aiplayer import AIPlayer
from horizons.ai.generic import GenericAI


@pytest.fixture
def ai_player():
    ai = AIPlayer.__new__(AIPlayer)

    ai.worldid = 1
    ai.log = Mock()

    ai.session = Mock()
    ai.session.world = Mock()

    ai.shipStates = Mock()
    ai.shipStates.idle = "idle"
    ai.shipStates.on_a_mission = "on_a_mission"

    ai.personality_manager = Mock()
    ai.personality_manager.get.return_value = Mock()

    return ai


@patch("horizons.ai.aiplayer.SettlementFounder")
@patch("horizons.ai.aiplayer.UnitBuilder")
@patch("horizons.ai.aiplayer.UnitManager")
@patch("horizons.ai.aiplayer.CombatManager")
@patch("horizons.ai.aiplayer.StrategyManager")
@patch("horizons.ai.aiplayer.BehaviorManager")
@patch("horizons.ai.aiplayer.SpecialDomesticTradeManager")
@patch("horizons.ai.aiplayer.InternationalTradeManager")
def test_init_state_calls_genericai_init_state(
    _international_trade_manager,
    _special_domestic_trade_manager,
    _behavior_manager,
    _strategy_manager,
    _combat_manager,
    _unit_manager,
    _unit_builder,
    _settlement_founder,
    ai_player,
):
    with patch.object(
        GenericAI,
        "_init_state",
    ) as generic_init_state:
        AIPlayer._init_state(ai_player)

    generic_init_state.assert_called_once_with()


def test_load_calls_superclass(
    ai_player,
):
    with (
        patch.object(
            GenericAI,
            "_load",
        ) as parent_load,
        patch(
            "horizons.ai.aiplayer.PersonalityManager.load",
            return_value=Mock(),
        ),
        patch(
            "horizons.ai.aiplayer.Scheduler",
        ),
    ):
        db = Mock(
            return_value=[
                (False, False, False, 1, 1),
            ],
        )

        ai_player._load(
            db,
            1,
        )

    parent_load.assert_called_once_with(
        db,
        1,
    )


def test_load_schedules_ticks(
    ai_player,
):
    with (
        patch.object(
            GenericAI,
            "_load",
        ),
        patch(
            "horizons.ai.aiplayer.PersonalityManager.load",
            return_value=Mock(),
        ),
        patch(
            "horizons.ai.aiplayer.Scheduler",
        ) as scheduler,
    ):
        db = Mock(
            return_value=[
                (False, False, False, 5, 10),
            ],
        )

        ai_player._load(
            db,
            1,
        )

    assert scheduler.return_value.add_new_object.call_count == 2


def test_start_mission_marks_ship_as_busy(
    ai_player,
):
    ship = Mock()

    mission = Mock()
    mission.ship = ship

    ai_player.ships = {}
    ai_player.missions = set()

    ai_player.start_mission(
        mission,
    )

    assert (
        ai_player.ships[ship]
        == ai_player.shipStates.on_a_mission
    )


def test_start_mission_starts_mission(
    ai_player,
):
    ship = Mock()

    mission = Mock()
    mission.ship = ship

    ai_player.ships = {}
    ai_player.missions = set()

    ai_player.start_mission(
        mission,
    )

    mission.start.assert_called_once_with()


def test_remove_unit_removes_ship_from_registry(
    ai_player,
):
    ship = Mock()

    ai_player._enabled = True

    ai_player.ships = {
        ship: object(),
    }

    ai_player.combat_manager = Mock()
    ai_player.unit_manager = Mock()

    ai_player.remove_unit(
        ship,
    )

    assert ship not in ai_player.ships


def test_remove_unit_updates_managers(
    ai_player,
):
    ship = Mock()

    ai_player._enabled = True

    ai_player.ships = {
        ship: object(),
    }

    ai_player.combat_manager = Mock()
    ai_player.unit_manager = Mock()

    ai_player.remove_unit(
        ship,
    )

    ai_player.combat_manager.remove_unit.assert_called_once_with(
        ship,
    )

    ai_player.unit_manager.remove_unit.assert_called_once_with(
        ship,
    )


def test_request_ship_sets_flag(
    ai_player,
):
    ai_player.need_more_ships = False

    ai_player.request_ship()

    assert ai_player.need_more_ships is True


def test_request_combat_ship_sets_flag(
    ai_player,
):
    ai_player.need_more_combat_ships = False

    ai_player.request_combat_ship()

    assert ai_player.need_more_combat_ships is True
