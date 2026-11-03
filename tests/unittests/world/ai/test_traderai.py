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
from horizons.ai.trader import Trader
from horizons.constants import BUILDINGS, TRADER
from horizons.util.shapes import Point
from horizons.world.disaster.blackdeathdisaster import BlackDeathDisaster
from horizons.world.units.unitexeptions import MoveNotPossible


@pytest.fixture
def trader():
    trader = Trader.__new__(Trader)

    trader.worldid = 1
    trader.ships = {}
    trader.warehouse = {}
    trader.allured_by_signal_fire = set()

    trader.session = Mock()
    trader.session.random = Mock()

    trader.log = Mock()

    return trader


@pytest.fixture
def ship():
    ship = Mock()
    ship.worldid = 42
    ship.radius = 5
    return ship


def test_get_ship_count(trader):
    trader.ships = {Mock(): object(), Mock(): object()}

    assert trader.get_ship_count() == 2


def test_signal_fire_returns_none_for_allured_ship(trader, ship):
    trader.allured_by_signal_fire.add(ship)

    assert trader._check_for_signal_fire_in_ship_range(ship) is None


def test_signal_fire_returns_fire_in_range(trader, ship):
    signal_fire = Mock()
    signal_fire.id = BUILDINGS.SIGNAL_FIRE

    tile = Mock()
    tile.object = signal_fire

    trader.session.world.get_tiles_in_radius.return_value = [tile]

    assert trader._check_for_signal_fire_in_ship_range(ship) is signal_fire


def test_signal_fire_returns_none_when_absent(trader, ship):
    trader.session.world.get_tiles_in_radius.return_value = []

    assert trader._check_for_signal_fire_in_ship_range(ship) is None


def test_ship_found_signal_fire_handles_none(trader, ship):
    trader._check_for_signal_fire_in_ship_range = Mock(
        return_value=None
    )

    trader._ship_found_signal_fire(ship)


def test_is_warehouse_safe_returns_true_without_plague(
    trader,
):
    warehouse = Mock()
    warehouse.settlement = Mock()

    trader.session.world.disaster_manager.get_disaster.return_value = None

    assert trader.is_warehouse_safe(warehouse) is True


def test_is_warehouse_safe_returns_false_for_plague(
    trader,
):
    warehouse = Mock()
    warehouse.settlement = Mock()

    trader.session.world.disaster_manager.get_disaster.return_value = (
        BlackDeathDisaster.__new__(BlackDeathDisaster)
    )

    assert trader.is_warehouse_safe(warehouse) is False


def test_send_ship_random_warehouse_falls_back_when_empty(
    trader,
    ship,
):
    trader.session.world.get_warehouses.return_value = []

    trader.send_ship_random = Mock()

    trader.send_ship_random_warehouse(ship)

    trader.send_ship_random.assert_called_once_with(ship)


def test_send_ship_random_warehouse_handles_move_failure(
    trader,
    ship,
):
    warehouse = Mock()
    warehouse.position.center = Point(10, 10)

    trader.session.world.get_warehouses.return_value = [
        warehouse,
    ]

    trader.send_ship_random = Mock()
    trader.is_warehouse_safe = Mock(return_value=True)

    ship.move.side_effect = MoveNotPossible()

    trader.send_ship_random_warehouse(
        ship,
        warehouse=warehouse,
    )

    trader.send_ship_random.assert_called_once_with(ship)


def test_send_ship_random_warehouse_updates_state(
    trader,
    ship,
):
    warehouse = Mock()
    warehouse.position.center = Point(10, 10)

    trader.session.world.get_warehouses.return_value = [
        warehouse,
    ]

    trader.is_warehouse_safe = Mock(return_value=True)

    trader.shipStates = Mock()
    trader.shipStates.moving_to_warehouse = object()

    trader.send_ship_random_warehouse(
        ship,
        warehouse=warehouse,
    )

    assert trader.warehouse[ship.worldid] is warehouse

    assert (
        trader.ships[ship]
        is trader.shipStates.moving_to_warehouse
    )

    ship.move.assert_called_once()


def test_idle_selects_warehouse_route(trader, ship):
    trader.session.random.randint.return_value = 0

    trader.send_ship_random_warehouse = Mock()

    with patch(
        "horizons.ai.trader.Scheduler"
    ) as scheduler:
        trader.ship_idle(ship)

        assert scheduler.return_value.add_new_object.called


def test_idle_selects_random_route(trader, ship):
    trader.session.random.randint.return_value = 100

    trader.send_ship_random = Mock()

    with patch(
        "horizons.ai.trader.Scheduler"
    ) as scheduler:
        trader.ship_idle(ship)

        assert scheduler.return_value.add_new_object.called


def test_reached_warehouse_removes_target(
    trader,
    ship,
):
    warehouse = Mock()
    settlement = Mock()

    warehouse.settlement = settlement

    trader.warehouse[ship.worldid] = warehouse

    trade_comp = Mock()
    trade_comp.buy_list = {}
    trade_comp.sell_list = {}

    settlement.get_component.return_value = trade_comp

    trader.shipStates = Mock()
    trader.shipStates.reached_warehouse = object()

    with patch("horizons.ai.trader.Scheduler") as scheduler:
        scheduler.return_value.add_new_object = Mock()
        scheduler.return_value.get_ticks.return_value = 42

        trader.reached_warehouse(ship)

    assert ship.worldid not in trader.warehouse


def test_reached_warehouse_updates_state(
    trader,
    ship,
):
    warehouse = Mock()
    settlement = Mock()

    warehouse.settlement = settlement

    trader.warehouse[ship.worldid] = warehouse

    trade_comp = Mock()
    trade_comp.buy_list = {}
    trade_comp.sell_list = {}

    settlement.get_component.return_value = trade_comp

    trader.shipStates = Mock()
    trader.shipStates.reached_warehouse = object()

    with patch("horizons.ai.trader.Scheduler") as scheduler:
        scheduler.return_value.add_new_object = Mock()
        scheduler.return_value.get_ticks.return_value = 42

        trader.reached_warehouse(ship)

    assert (
        trader.ships[ship]
        is trader.shipStates.reached_warehouse
    )


def test_new_settlement_creates_ship_when_threshold_exceeded(trader):
    trader.create_ship = Mock()

    trader.session.world.settlements = [object()] * 10
    trader.get_ship_count = Mock(return_value=1)

    with patch.object(TRADER, "SETTLEMENTS_PER_SHIP", 5):
        trader._on_new_settlement(Mock())

    trader.create_ship.assert_called_once()


def test_ship_found_signal_fire_moves_to_warehouse(
    trader,
    ship,
):
    signal_fire = Mock()
    signal_fire.position = Mock()
    signal_fire.radius = 10
    signal_fire.owner = "player"

    house = Mock()
    house.owner = "player"

    house.position.distance.return_value = 5

    trader._check_for_signal_fire_in_ship_range = Mock(
        return_value=signal_fire
    )

    trader.session.world.get_warehouses.return_value = [house]

    trader.send_ship_random_warehouse = Mock()

    with patch("horizons.ai.trader.Scheduler") as scheduler:
        scheduler.return_value.add_new_object = Mock()
        scheduler.return_value.get_ticks.return_value = 60

        trader._ship_found_signal_fire(ship)

    trader.send_ship_random_warehouse.assert_called_once_with(
        ship,
        house,
    )

    assert ship in trader.allured_by_signal_fire


def test_ship_found_signal_fire_without_warehouse(
    trader,
    ship,
):
    signal_fire = Mock()
    signal_fire.position = Mock()
    signal_fire.radius = 10
    signal_fire.owner = "player"

    house = Mock()
    house.owner = "someone_else"

    house.position.distance.return_value = 5

    trader._check_for_signal_fire_in_ship_range = Mock(
        return_value=signal_fire
    )

    trader.session.world.get_warehouses.return_value = [house]

    trader.send_ship_random_warehouse = Mock()

    trader._ship_found_signal_fire(ship)

    trader.send_ship_random_warehouse.assert_not_called()


def test_reached_warehouse_buys_resources(
    trader,
    ship,
):
    warehouse = Mock()
    settlement = Mock()

    warehouse.settlement = settlement

    trader.warehouse[ship.worldid] = warehouse

    trade_comp = Mock()
    trade_comp.buy_list = {}
    trade_comp.sell_list = {5: object()}

    settlement.get_component.return_value = trade_comp

    trader.session.random.randint.return_value = 1
    trader.session.db.get_res_value.return_value = 10

    trader.shipStates = Mock()
    trader.shipStates.reached_warehouse = object()

    with patch("horizons.ai.trader.Scheduler") as scheduler:
        scheduler.return_value.add_new_object = Mock()
        scheduler.return_value.get_ticks.return_value = 42

        trader.reached_warehouse(ship)

    assert trade_comp.sell.called


def test_reached_warehouse_sells_resources(
    trader,
    ship,
):
    warehouse = Mock()
    settlement = Mock()

    warehouse.settlement = settlement

    trader.warehouse[ship.worldid] = warehouse

    trade_comp = Mock()
    trade_comp.buy_list = {5: object()}
    trade_comp.sell_list = {}

    settlement.get_component.return_value = trade_comp

    trader.session.random.randint.return_value = 1
    trader.session.db.get_res_value.return_value = 10

    trader.shipStates = Mock()
    trader.shipStates.reached_warehouse = object()

    with patch("horizons.ai.trader.Scheduler") as scheduler:
        scheduler.return_value.add_new_object = Mock()
        scheduler.return_value.get_ticks.return_value = 42

        trader.reached_warehouse(ship)

    assert trade_comp.buy.called


def test_reached_warehouse_processes_resources_sorted(
    trader,
    ship,
):
    warehouse = Mock()
    settlement = Mock()

    warehouse.settlement = settlement

    trader.warehouse[ship.worldid] = warehouse

    trade_comp = Mock()
    trade_comp.buy_list = {
        7: object(),
        2: object(),
        5: object(),
    }

    trade_comp.sell_list = {}

    settlement.get_component.return_value = trade_comp

    trader.session.random.randint.return_value = 1
    trader.session.db.get_res_value.return_value = 10

    processed = []

    def buy_side_effect(res, *args):
        processed.append(res)
        return True

    trade_comp.buy.side_effect = buy_side_effect

    trader.shipStates = Mock()
    trader.shipStates.reached_warehouse = object()

    with patch("horizons.ai.trader.Scheduler") as scheduler:
        scheduler.return_value.add_new_object = Mock()
        scheduler.return_value.get_ticks.return_value = 42

        trader.reached_warehouse(ship)

    assert processed == [2, 5, 7]


def test_save_persists_targeted_warehouse(trader):
    ship = Mock()
    ship.worldid = 5

    trader.shipStates = Mock()

    state = Mock()
    state.index = 1

    trader.ships = {ship: state}

    warehouse = Mock()
    warehouse.worldid = 99

    trader.warehouse[ship.worldid] = warehouse

    db = Mock()

    with patch.object(GenericAI, "save"):
        trader.save(db)

    assert any(
        call.args[4] == 99
        for call in db.call_args_list
        if isinstance(call.args[0], str)
        and "INSERT INTO trader_ships" in call.args[0]
    )


def test_end_unsubscribes_from_settlements(trader):
    with (
        patch.object(GenericAI, "end"),
        patch("horizons.ai.trader.NewSettlement.unsubscribe") as unsubscribe,
    ):
        trader.end()

    unsubscribe.assert_called_once_with(
        trader._on_new_settlement
    )


def test_load_ship_states_restores_moving_random():
    ship = Mock()
    ship.worldid = 1

    trader = Trader.__new__(Trader)

    trader.ships = {}

    trader.shipStates = Mock()
    trader.shipStates.moving_random = "moving_random"
    trader.shipStates.moving_to_warehouse = "moving_to_warehouse"
    trader.shipStates.reached_warehouse = "reached_warehouse"

    trader.shipStates.__getitem__ = Mock(
        return_value=trader.shipStates.moving_random
    )

    db = Mock(
        return_value=[
            (1, 0, None, None),
        ]
    )

    with patch(
        "horizons.ai.trader.WorldObject.get_object_by_id",
        return_value=ship,
    ):
        trader.load_ship_states(db)

    ship.add_move_callback.assert_called_once()

    assert trader.ships[ship] == trader.shipStates.moving_random


def test_load_ship_states_restores_targeted_warehouse():
    ship = Mock()
    ship.worldid = 5

    warehouse = Mock()

    trader = Trader.__new__(Trader)

    trader.ships = {}
    trader.warehouse = {}

    trader.shipStates = Mock()
    trader.shipStates.moving_random = "moving_random"
    trader.shipStates.moving_to_warehouse = "moving_to_warehouse"
    trader.shipStates.reached_warehouse = "reached_warehouse"

    trader.shipStates.__getitem__ = Mock(
        return_value=trader.shipStates.moving_to_warehouse
    )

    db = Mock(
        return_value=[
            (5, 1, None, 99),
        ]
    )

    def get_object(worldid):
        if worldid == 5:
            return ship
        if worldid == 99:
            return warehouse
        raise AssertionError

    with patch(
        "horizons.ai.trader.WorldObject.get_object_by_id",
        side_effect=get_object,
    ):
        trader.load_ship_states(db)

    ship.add_move_callback.assert_called_once()

    assert trader.warehouse[5] is warehouse


def test_load_ship_states_restores_reached_warehouse_scheduler():
    ship = Mock()
    ship.worldid = 10

    trader = Trader.__new__(Trader)

    trader.ships = {}

    trader.shipStates = Mock()
    trader.shipStates.moving_random = "moving_random"
    trader.shipStates.moving_to_warehouse = "moving_to_warehouse"
    trader.shipStates.reached_warehouse = "reached_warehouse"

    trader.shipStates.__getitem__ = Mock(
        return_value=trader.shipStates.reached_warehouse
    )

    db = Mock(
        return_value=[
            (10, 2, 123, None),
        ]
    )

    with (
        patch(
            "horizons.ai.trader.WorldObject.get_object_by_id",
            return_value=ship,
        ),
        patch("horizons.ai.trader.Scheduler") as scheduler,
    ):
        trader.load_ship_states(db)

    scheduler.return_value.add_new_object.assert_called_once()

    assert trader.ships[ship] == trader.shipStates.reached_warehouse


def test_load_ship_states_requires_targeted_warehouse():
    ship = Mock()
    ship.worldid = 5

    trader = Trader.__new__(Trader)

    trader.ships = {}
    trader.warehouse = {}

    trader.shipStates = Mock()
    trader.shipStates.moving_to_warehouse = "moving_to_warehouse"

    trader.shipStates.__getitem__ = Mock(
        return_value=trader.shipStates.moving_to_warehouse
    )

    db = Mock(
        return_value=[
            (5, 1, None, None),
        ]
    )

    with patch(
        "horizons.ai.trader.WorldObject.get_object_by_id",
        return_value=ship,
    ), pytest.raises(AssertionError):
        trader.load_ship_states(db)


def test_save_persists_ship_state_index(trader):
    ship = Mock()
    ship.worldid = 123

    state = Mock()
    state.index = 7

    trader.ships = {ship: state}

    db = Mock()

    with (
        patch.object(GenericAI, "save"),
        patch("horizons.ai.trader.Scheduler") as scheduler,
    ):
        scheduler.return_value.get_classinst_calls.return_value = {}

        trader.save(db)

    assert any(
        call.args[2] == 7
        for call in db.call_args_list
        if isinstance(call.args[0], str)
        and "INSERT INTO trader_ships" in call.args[0]
    )
