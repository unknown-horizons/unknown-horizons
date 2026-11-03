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

from unittest.mock import Mock

import pytest

from horizons.component.healthcomponent import HealthComponent
from tests.dummy import Dummy


@pytest.fixture
def component():
    instance = Mock()
    instance.session = Dummy()

    component = HealthComponent(20)
    component.instance = instance
    component.initialize()

    return component, instance


def test_trivial(component):
    component, _ = component

    assert component.health == 20
    assert component.max_health == 20


def test_maxhealth_required():
    with pytest.raises(AssertionError):
        HealthComponent(None)


@pytest.mark.parametrize(
    "damage, expected_health, removed",
    [
        (19, 1, False),
        (20, 0, True),
        (300, 0, True),
    ],
)
def test_damage_cases(component, damage, expected_health, removed):
    component, instance = component

    component.deal_damage(1, damage)

    assert component.health == expected_health
    assert instance.remove.called is removed


def test_health_is_float(component):
    component, _ = component

    assert isinstance(component.health, float)
    assert isinstance(component.max_health, float)


def test_zero_damage(component):
    component, instance = component

    component.deal_damage(1, 0)

    assert component.health == 20
    assert not instance.remove.called


def test_health_clamped_to_zero(component):
    component, _ = component

    component.deal_damage(1, 1000)

    assert component.health == 0


def test_multiple_hits(component):
    component, instance = component

    component.deal_damage(1, 5)
    component.deal_damage(1, 5)

    assert component.health == 10
    assert not instance.remove.called


def test_alive_after_partial_damage(component):
    component, instance = component

    component.deal_damage(1, 19.9)

    assert component.health == pytest.approx(0.1)
    assert not instance.remove.called


def test_negative_damage_rejected(component):
    component, _ = component

    with pytest.raises(ValueError):
        component.deal_damage(1, -10)


def test_save(component):
    component, instance = component

    instance.worldid = 42

    db = Mock()

    component.save(db)

    db.assert_called_once_with(
        "INSERT INTO unit_health(owner_id, health) VALUES(?, ?)",
        42,
        component.health,
    )


def test_load():
    db = Mock()
    db.get_health.return_value = 13

    component = HealthComponent(20)

    component._add_listeners = Mock()

    component.load(db, 7)

    assert component.health == 13
    db.get_health.assert_called_once_with(7)
    component._add_listeners.assert_called_once_with()


def test_check_if_alive_does_not_remove_living_instance(component):
    component, instance = component

    component.health = 1

    component.check_if_alive()

    assert not instance.remove.called


def test_check_if_alive_removes_dead_instance(component):
    component, instance = component

    component.health = 0

    component.check_if_alive()

    assert instance.remove.called


def test_redraw_health_without_instance():
    component = HealthComponent(20)
    component.instance = None

    # should not raise
    component.redraw_health()


def test_redraw_health_selected_instance(component):
    component, instance = component

    instance.draw_health = Mock()

    instance.session = Mock()
    instance.session.selected_instances = [instance]

    component.redraw_health()

    instance.draw_health.assert_called_once()


def test_redraw_health_unselected_instance(component):
    component, instance = component

    instance.draw_health = Mock()

    instance.session = Mock()
    instance.session.selected_instances = []

    component.redraw_health()

    instance.draw_health.assert_not_called()


def test_initialize_adds_listeners():
    component = HealthComponent(20)

    component.add_damage_dealt_listener = Mock()

    component.initialize()

    assert component.add_damage_dealt_listener.call_count == 2
