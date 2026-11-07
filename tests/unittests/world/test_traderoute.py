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

from horizons.world.traderoute import TradeRoute


def test_current_transfer_initially_not_waiting():
    ship = Mock()

    route = TradeRoute(ship)

    assert route.current_transfer in ({}, None)


def test_traderoute_can_enable_requires_distinct_warehouses():
    route = TradeRoute(Mock())

    w1 = object()
    w2 = object()

    route.waypoints = [
        {"warehouse": w1, "resource_list": {}},
    ]

    assert route.can_enable() is False

    route.waypoints.append(
        {"warehouse": w1, "resource_list": {}}
    )

    assert route.can_enable() is False

    route.waypoints.append(
        {"warehouse": w2, "resource_list": {}}
    )

    assert route.can_enable() is True


def test_traderoute_initial_state():
    route = TradeRoute(Mock())

    assert route.enabled is False
    assert route.current_waypoint == -1
    assert route.waypoints == []
    assert route.wait_at_load is False
    assert route.wait_at_unload is False


def test_toggle_load_unload():
    route = TradeRoute(Mock())

    route.waypoints = [{
        "warehouse": object(),
        "resource_list": {1: 50},
    }]

    route.toggle_load_unload(0, 1)

    assert route.waypoints[0]["resource_list"][1] == -50

    route.toggle_load_unload(0, 1)

    assert route.waypoints[0]["resource_list"][1] == 50


def test_add_remove_resource():
    route = TradeRoute(Mock())

    route.waypoints = [{
        "warehouse": object(),
        "resource_list": {},
    }]

    route.add_to_resource_list(0, 1, 30)

    assert route.waypoints[0]["resource_list"][1] == 30

    route.remove_from_resource_list(0, 1)

    assert 1 not in route.waypoints[0]["resource_list"]


def test_enable_requires_two_distinct_waypoints():
    route = TradeRoute(Mock())

    route.waypoints = [
        {"warehouse": object(), "resource_list": {}},
    ]

    assert not route.enable()
    assert route.enabled is False


def test_append_adds_waypoint(mocker):
    route = TradeRoute(Mock())

    warehouse = object()

    mocker.patch(
        "horizons.world.traderoute.WorldObject.get_object_by_id",
        return_value=warehouse,
    )

    route.append(123)

    assert len(route.waypoints) == 1
    assert route.waypoints[0]["warehouse"] is warehouse
    assert route.waypoints[0]["resource_list"] == {}


def test_clear_resets_route():
    route = TradeRoute(Mock())

    route.waypoints = [{"warehouse": object(), "resource_list": {1: 2}}]
    route.current_waypoint = 5

    route.clear()

    assert route.waypoints == []
    assert route.current_waypoint == -1


def test_wait_flags_are_boolean():
    route = TradeRoute(Mock())

    route.set_wait_at_load(1)
    route.set_wait_at_unload("yes")

    assert route.wait_at_load is True
    assert route.wait_at_unload is True


def test_get_next_destination_cycles():
    route = TradeRoute(Mock())

    w1 = object()
    w2 = object()

    route.waypoints = [
        {"warehouse": w1, "resource_list": {}},
        {"warehouse": w2, "resource_list": {}},
    ]

    route.enabled = True

    assert route.get_next_destination(True)["warehouse"] is w1
    assert route.get_next_destination(True)["warehouse"] is w2
    assert route.get_next_destination(True)["warehouse"] is w1


def test_move_waypoint_rejects_invalid_direction():
    route = TradeRoute(Mock())

    route.waypoints = [
        {"warehouse": object(), "resource_list": {}},
        {"warehouse": object(), "resource_list": {}},
    ]

    with pytest.raises(ValueError):
        route.move_waypoint(0, "left")


def test_move_waypoint_up():
    route = TradeRoute(Mock())

    w1 = object()
    w2 = object()

    route.waypoints = [
        {"warehouse": w1, "resource_list": {}},
        {"warehouse": w2, "resource_list": {}},
    ]

    route.move_waypoint(1, "up")

    assert route.waypoints[0]["warehouse"] is w2
    assert route.waypoints[1]["warehouse"] is w1


def test_move_waypoint_down():
    route = TradeRoute(Mock())

    w1 = object()
    w2 = object()

    route.waypoints = [
        {"warehouse": w1, "resource_list": {}},
        {"warehouse": w2, "resource_list": {}},
    ]

    route.move_waypoint(0, "down")

    assert route.waypoints[0]["warehouse"] is w2
    assert route.waypoints[1]["warehouse"] is w1


def test_move_waypoint_up_at_start_has_no_effect():
    route = TradeRoute(Mock())

    w1 = object()
    w2 = object()

    route.waypoints = [
        {"warehouse": w1, "resource_list": {}},
        {"warehouse": w2, "resource_list": {}},
    ]

    route.move_waypoint(0, "up")

    assert route.waypoints[0]["warehouse"] is w1
    assert route.waypoints[1]["warehouse"] is w2


def test_get_next_destination_disabled_route_returns_none():
    route = TradeRoute(Mock())

    route.waypoints = [
        {"warehouse": object(), "resource_list": {}},
        {"warehouse": object(), "resource_list": {}},
    ]

    assert route.get_next_destination(True) is None


def test_get_next_destination_requires_two_waypoints():
    route = TradeRoute(Mock())

    route.enabled = True

    route.waypoints = [
        {"warehouse": object(), "resource_list": {}},
    ]

    assert route.get_next_destination(True) is None


def test_get_location_returns_current_waypoint():
    route = TradeRoute(Mock())

    waypoint = {
        "warehouse": object(),
        "resource_list": {1: 20},
    }

    route.waypoints = [waypoint]
    route.current_waypoint = 0

    assert route.get_location() == waypoint


def test_disable_stops_ship():
    ship = Mock()

    route = TradeRoute(ship)
    route.enabled = True

    route.disable()

    ship.stop.assert_called_once()
    assert route.enabled is False
