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


def test_init_state_creates_ship_registry(
    generic_ai,
):
    generic_ai._init_state()

    assert generic_ai.ships is not None


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


def test_ship_idle_schedules_send_ship(
    generic_ai,
    ship,
):
    with patch(
        "horizons.ai.generic.Scheduler"
    ) as scheduler:
        generic_ai.ship_idle(ship)

    scheduler.return_value.add_new_object.assert_called_once()


def test_load_reinitializes_state(
    generic_ai,
):
    generic_ai._init_state = Mock()

    with patch.object(
        GenericAI.__bases__[0],
        "_load",
    ):
        generic_ai._load(
            Mock(),
            1,
        )

    generic_ai._init_state.assert_called_once_with()


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
