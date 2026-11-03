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

from horizons.ai.generic import GenericAI
from horizons.ai.pirate import Pirate
from horizons.util.shapes import Point


@pytest.fixture
def pirate():
    pirate = Pirate.__new__(Pirate)

    pirate.worldid = 1
    pirate.ships = {}

    pirate.log = Mock()

    pirate.session = Mock()
    pirate.session.world = Mock()

    pirate.unit_manager = Mock()
    pirate.combat_manager = Mock()
    pirate.strategy_manager = Mock()
    pirate.behavior_manager = Mock()

    return pirate


@pytest.fixture
def ship():
    ship = Mock()
    ship.worldid = 42
    return ship


def test_tick_calls_combat_manager_and_maintains_ship_count(
    pirate,
):
    pirate.maintain_ship_count = Mock()

    pirate.tick()

    pirate.combat_manager.tick.assert_called_once_with()
    pirate.maintain_ship_count.assert_called_once_with()


def test_tick_long_calls_strategy_manager(
    pirate,
):
    pirate.tick_long()

    pirate.strategy_manager.tick.assert_called_once_with()


def test_maintain_ship_count_creates_missing_ship(
    pirate,
):
    pirate.ship_count = 1
    pirate.ships = {}

    pirate.create_ship_at_random_position = Mock()

    pirate.maintain_ship_count()

    pirate.create_ship_at_random_position.assert_called_once_with()


def test_maintain_ship_count_does_not_create_extra_ship(
    pirate,
    ship,
):
    pirate.ship_count = 1

    pirate.ships = {
        ship: object(),
    }

    pirate.create_ship_at_random_position = Mock()

    pirate.maintain_ship_count()

    pirate.create_ship_at_random_position.assert_not_called()


def test_get_nearest_player_ship_returns_none_without_targets():
    base_ship = Mock()

    base_ship.find_nearby_ships.return_value = []

    assert (
        Pirate.get_nearest_player_ship(base_ship)
        is None
    )


def test_get_nearest_player_ship_ignores_non_selectable():
    base_ship = Mock()

    target = Mock()
    target.has_component.return_value = False

    base_ship.find_nearby_ships.return_value = [
        target,
    ]

    assert (
        Pirate.get_nearest_player_ship(base_ship)
        is None
    )


def test_get_nearest_player_ship_returns_closest():
    base_ship = Mock()

    ship1 = Mock()
    ship2 = Mock()

    ship1.has_component.return_value = True
    ship2.has_component.return_value = True

    base_ship.find_nearby_ships.return_value = [
        ship1,
        ship2,
    ]

    base_ship.position.distance.side_effect = [
        20,
        5,
    ]

    result = Pirate.get_nearest_player_ship(
        base_ship,
    )

    assert result is ship2


def test_create_ship_at_random_position(
    pirate,
):
    point = Mock()
    point.x = 10
    point.y = 20

    pirate.session.world.get_random_possible_ship_position.return_value = point

    pirate.session.world.player = Mock()

    pirate.shipStates = Mock()
    pirate.shipStates.idle = "idle"

    created_ship = Mock()

    with patch(
        "horizons.ai.pirate.CreateUnit"
    ) as create_unit:
        create_unit.return_value.return_value = (
            created_ship
        )

        pirate.create_ship_at_random_position()

    assert pirate.ships[created_ship] == "idle"

    pirate.combat_manager.add_new_unit.assert_called_once_with(
        created_ship
    )


def test_get_random_profile_delegates_to_manager(
    pirate,
):
    token = object()

    profile = Mock()

    with patch(
        "horizons.ai.pirate.BehaviorProfileManager.get_random_pirate_profile",
        return_value=profile,
    ) as getter:
        result = pirate.get_random_profile(token)

    getter.assert_called_once_with(
        pirate,
        token,
    )

    assert result is profile


def test_remove_unit_removes_ship_from_registry(
    pirate,
    ship,
):
    pirate.ships = {
        ship: object(),
    }

    pirate.remove_unit(ship)

    assert ship not in pirate.ships


def test_remove_unit_updates_managers(
    pirate,
    ship,
):
    pirate.ships = {
        ship: object(),
    }

    pirate.remove_unit(ship)

    pirate.combat_manager.remove_unit.assert_called_once_with(
        ship,
    )

    pirate.unit_manager.remove_unit.assert_called_once_with(
        ship,
    )


def test_end_stops_strategy_manager(
    pirate,
):
    with patch.object(GenericAI, "end"):
        pirate.end()

    pirate.strategy_manager.end.assert_called_once_with()


def test_save_marks_player_as_pirate(
    pirate,
):
    pirate.home_point = Point(10, 20)

    db = Mock()

    with (
        patch.object(GenericAI, "save"),
        patch("horizons.ai.pirate.Scheduler") as scheduler,
    ):
        scheduler.return_value.get_classinst_calls.side_effect = [
            {"tick": 8},
            {"tick_long": 16},
        ]

        pirate.save(db)

    assert any(
        "is_pirate" in call.args[0]
        for call in db.call_args_list
    )


def test_save_persists_home_point(
    pirate,
):
    pirate.home_point = Point(7, 9)

    db = Mock()

    with (
        patch.object(GenericAI, "save"),
        patch("horizons.ai.pirate.Scheduler") as scheduler,
    ):
        scheduler.return_value.get_classinst_calls.side_effect = [
            {"tick": 8},
            {"tick_long": 16},
        ]

        pirate.save(db)

    assert any(
        call.args[1] == 7
        and call.args[2] == 9
        for call in db.call_args_list
        if "pirate_home_point" in call.args[0]
    )


def test_save_persists_ship_states(
    pirate,
):
    ship = Mock()
    ship.worldid = 55

    state = Mock()
    state.index = 3

    pirate.home_point = Point(1, 1)

    pirate.ships = {
        ship: state,
    }

    db = Mock()

    with (
        patch.object(GenericAI, "save"),
        patch("horizons.ai.pirate.Scheduler") as scheduler,
    ):
        scheduler.return_value.get_classinst_calls.side_effect = [
            {"tick": 1},
            {"tick_long": 1},
        ]

        pirate.save(db)

    assert any(
        call.args[1] == 55
        and call.args[2] == 3
        for call in db.call_args_list
        if "pirate_ships" in call.args[0]
    )


def test_finish_loading_restores_ship_state(
    pirate,
):
    restored_ship = Mock()

    pirate.shipStates = Mock()
    pirate.shipStates.__getitem__ = Mock(
        return_value="idle"
    )

    db = Mock(
        return_value=[
            (42, 0),
        ]
    )

    with (
        patch(
            "horizons.ai.pirate.WorldObject.get_object_by_id",
            return_value=restored_ship,
        ),
        patch(
            "horizons.ai.pirate.UnitManager.load",
            return_value=Mock(),
        ),
        patch(
            "horizons.ai.pirate.PirateCombatManager.load",
            return_value=Mock(),
        ),
        patch(
            "horizons.ai.pirate.PirateStrategyManager.load",
            return_value=Mock(),
        ),
        patch(
            "horizons.ai.pirate.BehaviorManager.load",
            return_value=Mock(),
        ),
    ):
        pirate.finish_loading(db)

    assert (
        pirate.ships[restored_ship]
        == "idle"
    )


def test_finish_loading_restores_managers(
    pirate,
):
    db = Mock(return_value=[])

    unit_manager = Mock()
    combat_manager = Mock()
    strategy_manager = Mock()
    behavior_manager = Mock()

    with (
        patch(
            "horizons.ai.pirate.UnitManager.load",
            return_value=unit_manager,
        ),
        patch(
            "horizons.ai.pirate.PirateCombatManager.load",
            return_value=combat_manager,
        ),
        patch(
            "horizons.ai.pirate.PirateStrategyManager.load",
            return_value=strategy_manager,
        ),
        patch(
            "horizons.ai.pirate.BehaviorManager.load",
            return_value=behavior_manager,
        ),
    ):
        pirate.finish_loading(db)

    assert pirate.unit_manager is unit_manager
    assert pirate.combat_manager is combat_manager
    assert pirate.strategy_manager is strategy_manager
    assert pirate.behavior_manager is behavior_manager
