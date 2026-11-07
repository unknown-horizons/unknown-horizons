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

from unittest.mock import MagicMock, patch

import pytest

from horizons.constants import PRODUCTION
from horizons.world.production.production import Production


@pytest.fixture
def mock_inventories():
    """Fixture providing MagicMock storage and owner inventories with safe return defaults."""
    inventory = MagicMock()
    owner_inventory = MagicMock()

    # Configure defaults to match Production expectations
    inventory.alter.return_value = 0
    inventory.get_free_space_for.return_value = 100
    inventory.__getitem__.return_value = 100

    return inventory, owner_inventory


@pytest.fixture
def production_instance(mock_inventories):
    """Fixture providing an initialized Production instance with mocked dependencies."""
    inventory, owner_inventory = mock_inventories
    with patch("horizons.world.production.production.Scheduler") as mock_scheduler:
        mock_scheduler.return_value.cur_tick = 0
        production = Production(
            inventory=inventory,
            owner_inventory=owner_inventory,
            prod_id=1,
            prod_data={},
        )
        production._prod_line = MagicMock()
        production._prod_line.produced_res = {}
        production._prod_line.consumed_res = {}
        return production


def test_production_initial_state(mock_inventories):
    inventory, owner_inventory = mock_inventories
    with patch("horizons.world.production.production.Scheduler") as mock_scheduler:
        mock_scheduler.return_value.cur_tick = 0
        production = Production(
            inventory,
            owner_inventory,
            prod_id=1,
            prod_data={},
        )

    assert production.prod_id == 1
    assert production.inventory is inventory
    assert production.owner_inventory is owner_inventory


def test_get_production_line_id(production_instance):
    production_instance._prod_line.id = 42
    assert production_instance.get_production_line_id() == 42


def test_pause_changes_state(production_instance):
    production_instance._state = PRODUCTION.STATES.waiting_for_res

    with patch.object(production_instance, "_changed"):
        production_instance.pause()

    assert production_instance.is_paused()


def test_finish_production_now_when_not_producing(production_instance):
    production_instance._state = MagicMock()

    with patch("horizons.world.production.production.Scheduler") as scheduler:
        production_instance.finish_production_now()
        scheduler.return_value.rem_call.assert_not_called()


def test_give_produced_resources(production_instance, mock_inventories):
    inventory, _ = mock_inventories
    production_instance._prod_line.produced_res = {1: 5, 2: 3}

    production_instance._give_produced_res()

    inventory.alter.assert_any_call(1, 5)
    inventory.alter.assert_any_call(2, 3)
    assert inventory.alter.call_count == 2


def test_check_available_resources_true(production_instance, mock_inventories):
    inventory, _ = mock_inventories
    production_instance._prod_line.consumed_res = {1: -5}
    inventory.__getitem__.return_value = 10

    assert production_instance._check_available_res() is True


def test_check_available_resources_false(production_instance, mock_inventories):
    inventory, _ = mock_inventories
    production_instance._prod_line.consumed_res = {1: -5}
    inventory.__getitem__.return_value = 2

    assert production_instance._check_available_res() is False


def test_check_for_space_for_produced_res(production_instance, mock_inventories):
    inventory, _ = mock_inventories
    production_instance._prod_line.produced_res = {1: 5}

    inventory.get_free_space_for.return_value = 10
    assert production_instance._check_for_space_for_produced_res() is True

    inventory.get_free_space_for.return_value = 0
    assert production_instance._check_for_space_for_produced_res() is False


def test_remove_res_to_expend(production_instance, mock_inventories):
    inventory, _ = mock_inventories
    production_instance._prod_line.consumed_res = {1: -3}

    production_instance._remove_res_to_expend()

    inventory.alter.assert_called_once_with(1, -3)


def test_get_unstorable_produced_res(production_instance, mock_inventories):
    inventory, _ = mock_inventories
    production_instance._prod_line.produced_res = {1: 5, 2: 3}

    inventory.get_free_space_for.side_effect = lambda res: 0 if res == 1 else 10

    assert production_instance.get_unstorable_produced_res() == [1]


def test_production_finished_listener_called(production_instance):
    events = []

    def listener(*args, **kwargs):
        events.append(True)

    production_instance.add_production_finished_listener(listener)
    production_instance.on_production_finished()

    assert events == [True]
