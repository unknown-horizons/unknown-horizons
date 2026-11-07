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

import weakref
from unittest.mock import Mock, patch

import pytest

from horizons.ai.generic import GenericAI
from horizons.constants import GAME_SPEED
from horizons.util.python.callback import Callback
from horizons.world.units.unitexeptions import MoveNotPossible


@pytest.fixture
def generic_ai():
    ai = GenericAI.__new__(GenericAI)

    ai.worldid = 1
    ai.log = Mock()

    ai.session = Mock()
    ai.session.world = Mock()

    ai.shipStates = Mock()
    ai.shipStates.moving_random = "moving_random"

    ai.ships = {}

    return ai


@pytest.fixture
def ship():
    ship = Mock()
    ship.worldid = 42
    return ship


def test_send_ship_delegates_to_send_ship_random(
    generic_ai,
    ship,
):
    generic_ai.send_ship_random = Mock()

    generic_ai.send_ship(ship)

    generic_ai.send_ship_random.assert_called_once_with(
        ship,
    )


def test_send_ship_random_moves_ship(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    generic_ai.send_ship_random(ship)

    ship.move.assert_called_once()


def test_send_ship_random_passes_destination(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    generic_ai.send_ship_random(ship)

    args, kwargs = ship.move.call_args

    assert args[0] is point
    assert isinstance(args[1], Callback)
    assert kwargs == {}


def test_send_ship_random_updates_ship_state(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    generic_ai.send_ship_random(ship)

    assert (
        generic_ai.ships[ship]
        == generic_ai.shipStates.moving_random
    )


def test_send_ship_random_gets_random_position_once(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    generic_ai.send_ship_random(ship)

    (
        generic_ai.session.world
        .get_random_possible_ship_position
        .assert_called_once_with()
    )


def test_send_ship_random_schedules_retry_on_move_failure(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    ship.move.side_effect = MoveNotPossible()

    with patch(
        "horizons.ai.generic.Scheduler"
    ) as scheduler:
        generic_ai.send_ship_random(ship)

    scheduler.return_value.add_new_object.assert_called_once()


def test_send_ship_random_uses_retry_delay(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    ship.move.side_effect = MoveNotPossible()

    with patch(
        "horizons.ai.generic.Scheduler"
    ) as scheduler:
        generic_ai.send_ship_random(ship)

    _, args, _ = (
        scheduler.return_value.add_new_object.mock_calls[0]
    )

    assert args[1] is generic_ai
    assert (
        args[2]
        == GAME_SPEED.TICKS_PER_SECOND * 2
    )


def test_send_ship_random_does_not_update_state_on_failure(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    ship.move.side_effect = MoveNotPossible()

    with patch(
        "horizons.ai.generic.Scheduler"
    ):
        generic_ai.send_ship_random(ship)

    assert ship not in generic_ai.ships


def test_send_ship_random_logs_when_blocked(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 10
    point.y = 20

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    ship.move.side_effect = MoveNotPossible()

    with patch(
        "horizons.ai.generic.Scheduler"
    ):
        generic_ai.send_ship_random(ship)

    generic_ai.log.info.assert_called_once()


def test_ship_idle_schedules_send_ship(
    generic_ai,
    ship,
):
    with patch(
        "horizons.ai.generic.Scheduler"
    ) as scheduler:
        generic_ai.ship_idle(ship)

    scheduler.return_value.add_new_object.assert_called_once()


def test_ship_idle_schedules_callback_for_ship(
    generic_ai,
    ship,
):
    with patch(
        "horizons.ai.generic.Scheduler"
    ) as scheduler:
        generic_ai.ship_idle(ship)

    _, args, _ = (
        scheduler.return_value.add_new_object.mock_calls[0]
    )

    assert isinstance(
        args[0],
        Callback,
    )

    assert args[1] is generic_ai


def test_load_reinitializes_ship_registry(
    generic_ai,
):
    with patch.object(
        GenericAI.__bases__[0],
        "_load",
    ):
        GenericAI._GenericAI__init(
            generic_ai
        )

    assert isinstance(
        generic_ai.ships,
        weakref.WeakValueDictionary,
    )


def test_end_clears_ship_registry(
    generic_ai,
):
    with patch.object(
        GenericAI.__bases__[0],
        "end",
    ):
        generic_ai.end()

    assert generic_ai.ships is None


def test_end_calls_superclass(
    generic_ai,
):
    with patch.object(
        GenericAI.__bases__[0],
        "end",
    ) as end:
        generic_ai.end()

    end.assert_called_once_with()


def test_send_ship_random_logs_target_coordinates(
    generic_ai,
    ship,
):
    point = Mock()
    point.x = 77
    point.y = 88

    generic_ai.session.world.get_random_possible_ship_position.return_value = (
        point
    )

    generic_ai.send_ship_random(ship)

    generic_ai.log.debug.assert_called()


def test_ship_idle_logs_debug_message(
    generic_ai,
    ship,
):
    with patch(
        "horizons.ai.generic.Scheduler"
    ):
        generic_ai.ship_idle(ship)

    generic_ai.log.debug.assert_called_once()


def test_load_creates_new_registry_instance(
    generic_ai,
):
    old_registry = generic_ai.ships

    with patch.object(
        GenericAI.__bases__[0],
        "_load",
    ):
        generic_ai._load(
            Mock(),
            1,
        )

    assert generic_ai.ships is not old_registry
