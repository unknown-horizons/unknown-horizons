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

from horizons.component.stancecomponent import (
    AggressiveStance,
    FleeStance,
    StanceComponent,
)
from horizons.util.shapes import Circle, Point
from horizons.world.units.unitexeptions import MoveNotPossible


@pytest.fixture(autouse=True)
def scheduler(mocker):
    mocker.patch("horizons.component.stancecomponent.Scheduler")


# ==========================================
# Base StanceComponent Fixtures & Tests
# ==========================================

@pytest.fixture
def stance():
    component = StanceComponent()
    instance = Mock()
    component.instance = instance
    return component, instance


def test_initial_state():
    component = StanceComponent()
    assert component.get_state() == "idle"


def test_initialize_registers_listeners(stance):
    component, instance = stance
    component.initialize()
    instance.add_user_attack_issued_listener.assert_called_once()
    instance.add_user_move_issued_listener.assert_called_once()


def test_remove_unregisters_listeners(stance):
    component, instance = stance

    component.remove()

    instance.remove_user_attack_issued_listener.assert_called_once()
    instance.remove_user_move_issued_listener.assert_called_once()


def test_set_state(stance):
    component, _ = stance
    component.set_state("user_attack")
    assert component.get_state() == "user_attack"


def test_act_dispatches_to_current_state(stance):
    component, _ = stance
    component.act_idle = Mock()
    component.action["idle"] = component.act_idle
    component.act()
    component.act_idle.assert_called_once()


def test_act_dispatches_user_attack(stance):
    component, _ = stance
    component.act_user_attack = Mock()
    component.action["user_attack"] = component.act_user_attack
    component.state = "user_attack"
    component.act()
    component.act_user_attack.assert_called_once()


def test_user_attack_returns_to_idle(stance):
    component, instance = stance
    component.state = "user_attack"
    instance.is_attacking.return_value = False
    component.act_user_attack()
    assert component.state == "idle"


def test_user_move_returns_to_idle(stance):
    component, instance = stance
    component.state = "user_move"
    instance.is_moving.return_value = False
    component.act_user_move()
    assert component.state == "idle"


def test_move_back_stops_and_becomes_idle(stance):
    component, instance = stance
    component.act_move_back()
    instance.stop.assert_called_once()
    assert component.state == "idle"


def test_auto_attack_stops_attack_and_becomes_idle(stance):
    component, instance = stance
    component.act_auto_attack()
    instance.stop_attack.assert_called_once()
    assert component.state == "idle"


def test_flee_stops_and_becomes_idle(stance):
    component, instance = stance
    component.act_flee()
    instance.stop.assert_called_once()
    assert component.state == "idle"


# ==========================================
# LimitedMoveStance & AggressiveStance Tests
# ==========================================

@pytest.fixture
def limited_stance():
    component = AggressiveStance()
    instance = Mock()
    instance.position.center = Point(0, 0)
    component.instance = instance
    return component, instance


def test_get_instance_data(limited_stance):
    component, instance = limited_stance
    component.get_instance_data()
    assert component.return_position == instance.position.center


def test_get_target_returns_none_without_enemies(limited_stance):
    component, instance = limited_stance
    instance.session = Mock()
    instance.session.world.get_health_instances.return_value = []
    assert component.get_target(10) is None


def test_get_target_ignores_non_enemies(limited_stance):
    component, instance = limited_stance

    enemy = Mock()

    instance.session = Mock()
    instance.session.world.get_health_instances.return_value = [enemy]
    instance.session.world.diplomacy.are_enemies.return_value = False

    assert component.get_target(10) is None


def test_get_target_returns_closest_enemy(limited_stance):
    component, instance = limited_stance
    enemy1 = Mock()
    enemy2 = Mock()
    instance.position = Mock()
    instance.position.distance.side_effect = [20, 5]
    instance.session = Mock()
    instance.session.world.get_health_instances.return_value = [
        enemy1,
        enemy2,
    ]
    instance.session.world.diplomacy.are_enemies.return_value = True
    target = component.get_target(10)
    assert target is enemy2


def test_auto_attack_moves_back_when_attack_finishes(limited_stance):
    component, instance = limited_stance
    component.return_position = Point(0, 0)
    component.state = "auto_attack"
    instance.is_attacking.return_value = False

    component.act_auto_attack()

    instance.move.assert_called_once_with(component.return_position)
    assert component.state == "move_back"


def test_aggressive_user_move_fires_at_target():
    stance = AggressiveStance()
    instance = Mock()
    stance.instance = instance
    target = Mock()
    stance.get_target = Mock(return_value=target)
    stance.act_user_move()
    instance.fire_all_weapons.assert_called_once_with(
        target.position.center
    )


def test_auto_attack_falls_back_to_circle_when_return_move_is_impossible(limited_stance):
    component, instance = limited_stance
    component.return_position = Point(0, 0)
    instance.position.center = Point(100, 0)
    instance.is_attacking.return_value = False
    instance.move.side_effect = [MoveNotPossible(), None]

    component.act_auto_attack()

    assert instance.move.call_count == 2
    assert instance.move.call_args_list[0].args == (component.return_position,)
    assert isinstance(instance.move.call_args_list[1].args[0], Circle)
    assert component.state == "move_back"


def test_move_back_attacks_target_when_one_is_found(limited_stance):
    component, instance = limited_stance
    instance._max_range = 5
    target = Mock()
    component.get_target = Mock(return_value=target)
    component.state = "move_back"

    component.act_move_back()

    instance.attack.assert_called_once_with(target)
    assert component.state == "auto_attack"


def test_move_back_becomes_idle_at_return_position_without_target(limited_stance):
    component, instance = limited_stance
    instance._max_range = 5
    component.return_position = Point(0, 0)
    instance.position.center = Point(0, 0)
    component.get_target = Mock(return_value=None)
    component.state = "move_back"

    component.act_move_back()

    assert component.state == "idle"
    instance.attack.assert_not_called()


# ==========================================
# FleeStance Tests
# ==========================================

@pytest.fixture
def flee_stance():
    component = FleeStance()
    instance = Mock()
    component.instance = instance
    return component, instance


def test_get_approaching_unit_none(flee_stance):
    component, instance = flee_stance
    instance.session = Mock()
    instance.session.world.get_health_instances.return_value = []
    assert component.get_approaching_unit() is None


def test_get_approaching_unit_returns_closest_enemy(flee_stance):
    component, instance = flee_stance

    enemy1 = Mock()
    enemy1._max_range = 10

    enemy2 = Mock()
    enemy2._max_range = 1

    instance.position = Mock()
    instance.position.distance.side_effect = [15, 3]

    instance.session = Mock()
    instance.session.world.get_health_instances.return_value = [
        enemy1,
        enemy2,
    ]
    instance.session.world.diplomacy.are_enemies.return_value = True

    approaching = component.get_approaching_unit()

    assert approaching is enemy2


def test_flee_idle_without_enemy(flee_stance):
    component, instance = flee_stance
    component.get_approaching_unit = Mock(return_value=None)
    component.act_idle()
    instance.move.assert_not_called()
    assert component.state == "idle"


def test_flee_idle_moves_away(flee_stance):
    component, instance = flee_stance
    enemy = Mock()
    enemy._max_range = 5
    enemy.position.center = Point(10, 10)
    component.get_approaching_unit = Mock(return_value=enemy)
    component.act_idle()
    instance.move.assert_called_once()
    assert component.state == "flee"


def test_flee_idle_handles_move_not_possible(flee_stance):
    component, instance = flee_stance
    enemy = Mock()
    enemy._max_range = 5
    enemy.position.center = Point(10, 10)
    component.get_approaching_unit = Mock(return_value=enemy)
    instance.move.side_effect = MoveNotPossible()
    component.act_idle()
    assert component.state == "idle"


def test_flee_returns_to_idle_when_not_moving(flee_stance):
    component, instance = flee_stance
    component.state = "flee"
    instance.is_moving.return_value = False
    component.get_approaching_unit = Mock(return_value=None)
    component.act_flee()
    assert component.state == "idle"
