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
def test_private_init_creates_core_managers(
    international_trade_manager,
    special_domestic_trade_manager,
    behavior_manager,
    strategy_manager,
    combat_manager,
    unit_manager,
    unit_builder,
    settlement_founder,
    ai_player,
):
    AIPlayer._AIPlayer__init(ai_player)

    settlement_founder.assert_called_once_with(ai_player)
    unit_builder.assert_called_once_with(ai_player)
    unit_manager.assert_called_once_with(ai_player)
    combat_manager.assert_called_once_with(ai_player)
    strategy_manager.assert_called_once_with(ai_player)
    behavior_manager.assert_called_once_with(ai_player)
    special_domestic_trade_manager.assert_called_once_with(ai_player)
    international_trade_manager.assert_called_once_with(ai_player)


def test_load_calls_superclass(ai_player):
    with (
        patch.object(GenericAI, "_load") as parent_load,
        patch.object(AIPlayer, "_AIPlayer__init"),
        patch(
            "horizons.ai.aiplayer.PersonalityManager.load",
            return_value=Mock(),
        ),
        patch("horizons.ai.aiplayer.Scheduler"),
    ):
        db = Mock(
            return_value=[
                (False, False, False, 1, 1),
            ],
        )

        ai_player._load(db, 1)

    parent_load.assert_called_once_with(db, 1)


def test_load_schedules_ticks(ai_player):
    with (
        patch.object(GenericAI, "_load"),
        patch.object(AIPlayer, "_AIPlayer__init"),
        patch(
            "horizons.ai.aiplayer.PersonalityManager.load",
            return_value=Mock(),
        ),
        patch("horizons.ai.aiplayer.Scheduler") as scheduler,
    ):
        db = Mock(
            return_value=[
                (False, False, False, 5, 10),
            ],
        )

        ai_player._load(db, 1)

    assert scheduler.return_value.add_new_object.call_count == 2


def test_load_schedules_saved_tick_values(ai_player):
    with (
        patch.object(GenericAI, "_load"),
        patch.object(AIPlayer, "_AIPlayer__init"),
        patch(
            "horizons.ai.aiplayer.PersonalityManager.load",
            return_value=Mock(),
        ),
        patch("horizons.ai.aiplayer.Scheduler") as scheduler,
    ):
        db = Mock(
            return_value=[
                (False, False, False, 5, 10),
            ],
        )

        ai_player._load(db, 1)

    calls = scheduler.return_value.add_new_object.call_args_list

    assert calls[0].kwargs["run_in"] == 5
    assert calls[1].kwargs["run_in"] == 10


def test_start_mission_marks_ship_as_busy(ai_player):
    ship = Mock()
    mission = Mock()
    mission.ship = ship

    ai_player.ships = {}
    ai_player.missions = set()

    ai_player.start_mission(mission)

    assert ai_player.ships[ship] == ai_player.shipStates.on_a_mission


def test_start_mission_starts_mission(ai_player):
    ship = Mock()
    mission = Mock()
    mission.ship = ship

    ai_player.ships = {}
    ai_player.missions = set()

    ai_player.start_mission(mission)

    mission.start.assert_called_once_with()


def test_start_mission_adds_mission_to_registry(ai_player):
    ship = Mock()
    mission = Mock()
    mission.ship = ship

    ai_player.ships = {}
    ai_player.missions = set()

    ai_player.start_mission(mission)

    assert mission in ai_player.missions


def test_remove_unit_removes_ship_from_registry(ai_player):
    ship = Mock()

    ai_player._enabled = True
    ai_player.ships = {ship: object()}
    ai_player.combat_manager = Mock()
    ai_player.unit_manager = Mock()

    ai_player.remove_unit(ship)

    assert ship not in ai_player.ships


def test_remove_unit_updates_managers(ai_player):
    ship = Mock()

    ai_player._enabled = True
    ai_player.ships = {ship: object()}
    ai_player.combat_manager = Mock()
    ai_player.unit_manager = Mock()

    ai_player.remove_unit(ship)

    ai_player.combat_manager.remove_unit.assert_called_once_with(ship)
    ai_player.unit_manager.remove_unit.assert_called_once_with(ship)


def test_remove_unit_does_nothing_when_disabled(ai_player):
    ship = Mock()

    ai_player._enabled = False
    ai_player.ships = {ship: object()}
    ai_player.combat_manager = Mock()
    ai_player.unit_manager = Mock()

    ai_player.remove_unit(ship)

    assert ship in ai_player.ships
    ai_player.combat_manager.remove_unit.assert_not_called()
    ai_player.unit_manager.remove_unit.assert_not_called()


def test_request_ship_sets_flag(ai_player):
    ai_player.need_more_ships = False

    ai_player.request_ship()

    assert ai_player.need_more_ships is True


def test_request_ship_logs(ai_player):
    ai_player.request_ship()

    ai_player.log.info.assert_called_once()


def test_request_combat_ship_sets_flag(ai_player):
    ai_player.need_more_combat_ships = False

    ai_player.request_combat_ship()

    assert ai_player.need_more_combat_ships is True


def test_request_combat_ship_logs(ai_player):
    ai_player.request_combat_ship()

    ai_player.log.info.assert_called_once()


def test_refresh_ships_adds_new_ship(ai_player):
    ship = Mock()
    ship.owner = ai_player
    ship.has_component.return_value = True

    ai_player.world = Mock()
    ai_player.world.ships = [ship]
    ai_player.ships = {}
    ai_player.combat_manager = Mock()

    ai_player.refresh_ships()

    assert ai_player.ships[ship] == ai_player.shipStates.idle


def test_refresh_ships_does_not_duplicate_ships(ai_player):
    ship = Mock()
    ship.owner = ai_player
    ship.has_component.return_value = True

    ai_player.world = Mock()
    ai_player.world.ships = [ship]
    ai_player.ships = {ship: ai_player.shipStates.idle}

    ai_player.refresh_ships()

    assert len(ai_player.ships) == 1
