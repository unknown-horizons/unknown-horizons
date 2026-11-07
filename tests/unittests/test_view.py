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

from unittest.mock import MagicMock

import pytest

from horizons.view import View


@pytest.fixture
def view():
    """Fixture to provide a partially-constructed View with mocked dependencies."""
    view = object.__new__(View)

    view.cam = MagicMock()
    view.world = MagicMock()

    view.world.min_x = 0
    view.world.max_x = 100
    view.world.min_y = 0
    view.world.max_y = 100

    view._autoscroll = [0, 0]
    view._autoscroll_keys = [0, 0]

    return view


def test_zoom_getter(view):
    view.cam.getZoom.return_value = 1.5

    assert view.zoom == 1.5


def test_zoom_setter(mocker, view):
    broadcast = mocker.patch(
        "horizons.view.ZoomChanged.broadcast"
    )

    view.zoom = 2.0

    view.cam.setZoom.assert_called_once_with(2.0)
    broadcast.assert_called_once()


def test_rotate_left(view):
    view.cam.getRotation.return_value = 0

    view.rotate_left()

    view.cam.setRotation.assert_called_once_with(90)


def test_rotate_right(view):
    view.cam.getRotation.return_value = 90

    view.rotate_right()

    view.cam.setRotation.assert_called_once_with(0)


def test_autoscroll_keys(view):
    view.autoscroll_keys(1, -1)

    assert view._autoscroll_keys == [1, -1]


def test_set_rotation(view):
    view._changed = MagicMock()

    view.set_rotation(180)

    view.cam.setRotation.assert_called_once_with(180)
    view._changed.assert_called_once()


def test_save(view):
    db = MagicMock()

    loc = MagicMock()
    loc.x = 10
    loc.y = 20

    view.cam.getZoom.return_value = 1.5
    view.cam.getRotation.return_value = 90

    location = MagicMock()
    location.getExactLayerCoordinates.return_value = loc

    view.cam.getLocation.return_value = location

    view.save(db)

    db.assert_called_once()


def test_load(view):
    db = MagicMock()

    db.return_value = [
        (2.0, 90, 10, 20)
    ]

    view.center = MagicMock()
    view.set_rotation = MagicMock()

    view.load(db, "world")

    view.set_rotation.assert_called_once_with(90)
    view.center.assert_called_once_with(10, 20)


def test_resize_layers_empty_map(view):
    db = MagicMock()

    db.return_value = [(None, None, None, None)]
    db.map_padding = 2

    water_layer = MagicMock()
    water_layer.getCellCache.return_value = None

    layer = MagicMock()
    layer.getCellCache.return_value = MagicMock()

    view.layers = [
        water_layer,
        layer,
    ]

    view.resize_layers(db)

    layer.getCellCache.return_value.setSize.assert_called_once()
