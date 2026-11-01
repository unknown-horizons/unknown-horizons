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


def test_damage(component):
    component, instance = component

    component.deal_damage(1, 19)

    assert component.health == 1
    assert component.max_health == 20
    assert not instance.remove.called


def test_damage_zero_health(component):
    component, instance = component

    component.deal_damage(1, 20)

    assert component.health == 0
    assert component.max_health == 20
    assert instance.remove.called


def test_huge_damage(component):
    component, instance = component

    component.deal_damage(1, 300)

    assert component.health == 0
    assert component.max_health == 20
    assert instance.remove.called
