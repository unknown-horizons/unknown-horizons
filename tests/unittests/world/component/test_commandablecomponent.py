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

from unittest.mock import Mock

import pytest

from horizons.component.commandablecomponent import CommandableComponent
from horizons.util.shapes import Point
from horizons.world.units.unitexeptions import MoveNotPossible


@pytest.fixture
def component():
    component = CommandableComponent()
    session = Mock()
    session.ingame_gui = Mock()
    session.ingame_gui.minimap = Mock()
    session.ingame_gui.message_widget = Mock()
    session.world = Mock()
    owner = Mock()
    owner.is_local_player = True
    instance = Mock()
    instance.owner = owner
    instance.session = session
    component.instance = instance
    return component, instance, session


# --- Happy Path & Coordinate Rounding ---

def test_go_moves_to_rounded_coordinates(component):
    component, instance, _ = component
    instance.move.return_value = None  # Explicitly ensure the happy path succeeds
    component.go(10.4, 20.6)
    instance.move.assert_called_once()
    move_target = instance.move.call_args.args[0]
    assert isinstance(move_target, Point)
    assert move_target.x == 10
    assert move_target.y == 21


@pytest.mark.parametrize(
    ("x", "y", "expected_x", "expected_y"),
    [
        (1.2, 2.2, 1, 2),
        (1.5, 2.5, 2, 2),       # Documenting Python's banker's rounding
        (3.5, 4.5, 4, 4),       # Additional banker's rounding verification
        (10.49, 20.51, 10, 21),
        (-0.6, -1.6, -1, -2),
    ],
)
def test_go_rounds_coordinates(
    component,
    x,
    y,
    expected_x,
    expected_y,
):
    component, instance, _ = component
    instance.move.return_value = None
    component.go(x, y)
    point = instance.move.call_args.args[0]
    assert point.x == expected_x
    assert point.y == expected_y


# --- Minimap Integration ---

def test_go_updates_minimap_for_local_player(component):
    component, instance, session = component
    component.go(1, 2)
    session.ingame_gui.minimap.show_unit_path.assert_called_once_with(
        instance
    )


def test_go_does_not_update_minimap_for_remote_player(component):
    component, _, session = component
    component.instance.owner.is_local_player = False
    component.go(1, 2)
    session.ingame_gui.minimap.show_unit_path.assert_not_called()


# --- Fallback & Retry Logic ---

def test_go_falls_back_to_circle(component):
    component, instance, _ = component
    instance.move.side_effect = [
        MoveNotPossible(),
        None,
    ]
    instance.get_move_target.return_value = Mock()
    component.go(5, 5)
    assert instance.move.call_count == 2
    instance.get_move_target.assert_called_once()


@pytest.mark.parametrize(
    "successful_radius",
    [1, 2, 3, 4],
)
def test_go_tries_larger_circles_until_success(
    component,
    successful_radius,
):
    component, instance, _ = component
    effects = [
        MoveNotPossible(),
    ]
    for _ in range(1, successful_radius):
        effects.append(MoveNotPossible())
    effects.append(None)
    instance.move.side_effect = effects
    instance.get_move_target.return_value = Mock()
    component.go(20, 30)
    circles = [
        c.args[0]
        for c in instance.move.call_args_list[1:]
    ]
    assert circles[-1].radius == successful_radius


def test_go_fails_after_max_radius(component):
    component, instance, session = component
    instance.move.side_effect = MoveNotPossible()
    session.world.get_tile.return_value = Mock()
    component.go(10, 10)
    # Initial move attempt + 4 fallback circles (radii 1, 2, 3, 4) = 5 total calls
    assert instance.move.call_count == 5


# --- Failure Modes & Error Messaging ---

def test_go_reports_outside_world(component):
    component, instance, session = component
    instance.move.side_effect = MoveNotPossible()
    session.world.get_tile.return_value = None
    component.go(50, 60)
    session.ingame_gui.message_widget.add.assert_called_once()
    kwargs = (
        session.ingame_gui.message_widget.add.call_args.kwargs
    )
    assert kwargs["string_id"] == "MOVE_OUTSIDE_OF_WORLD"
    assert kwargs["point"] == Point(50, 60)


def test_go_reports_invalid_location(component):
    component, instance, session = component
    instance.move.side_effect = MoveNotPossible()
    session.world.get_tile.return_value = Mock()
    component.go(50, 60)
    kwargs = (
        session.ingame_gui.message_widget.add.call_args.kwargs
    )
    assert kwargs["string_id"] == "MOVE_INVALID_LOCATION"
    assert kwargs["point"] == Point(50, 60)


def test_go_no_error_message_for_non_local_player(component):
    component, instance, session = component
    instance.owner.is_local_player = False
    instance.move.side_effect = MoveNotPossible()
    component.go(30, 40)
    session.ingame_gui.message_widget.add.assert_not_called()


def test_go_uses_fallback_move_target(component):
    component, instance, _ = component
    target = Mock()
    instance.move.side_effect = [MoveNotPossible(), None]
    instance.get_move_target.return_value = target
    component.go(5, 5)
    assert instance.get_move_target.return_value is target
