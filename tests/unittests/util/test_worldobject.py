# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

import gc

import pytest

from horizons.util.worldobject import WorldObject, WorldObjectNotFound


@pytest.fixture(autouse=True)
def reset_world_objects():
    """Keep WorldObject's global registry and ID counter isolated per test."""
    WorldObject.reset()
    yield
    WorldObject.reset()


def test_auto_assigns_worldid():
    obj = WorldObject()

    assert obj.worldid == 1


def test_worldids_increment():
    a = WorldObject()
    b = WorldObject()
    c = WorldObject()

    assert a.worldid == 1
    assert b.worldid == 2
    assert c.worldid == 3


def test_explicit_worldid():
    obj = WorldObject(worldid=99)

    assert obj.worldid == 99


def test_explicit_worldid_updates_next_id():
    WorldObject(worldid=100)

    obj = WorldObject()

    assert obj.worldid == 101


def test_duplicate_worldid_raises():
    first = WorldObject(worldid=5)

    assert first.worldid == 5

    with pytest.raises(AssertionError):
        WorldObject(worldid=5)


def test_get_object_by_id():
    obj = WorldObject()

    assert WorldObject.get_object_by_id(obj.worldid) is obj


def test_get_missing_object_raises():
    with pytest.raises(WorldObjectNotFound):
        WorldObject.get_object_by_id(9999)


def test_object_registered():
    obj = WorldObject()

    assert obj.worldid in WorldObject.get_objs()


def test_reset_clears_registry():
    obj = WorldObject()

    assert obj.worldid in WorldObject.get_objs()

    WorldObject.reset()

    assert len(WorldObject.get_objs()) == 0


def test_reset_resets_id_counter():
    WorldObject()
    WorldObject()

    WorldObject.reset()

    obj = WorldObject()

    assert obj.worldid == 1


def test_load_assigns_worldid():
    obj = WorldObject()

    WorldObject.reset()
    obj.load(None, 42)

    assert obj.worldid == 42


def test_load_registers_object():
    obj = WorldObject()

    WorldObject.reset()
    obj.load(None, 33)

    assert WorldObject.get_object_by_id(33) is obj


def test_worldobjects_are_ordered_by_worldid():
    a = WorldObject(worldid=1)
    b = WorldObject(worldid=2)

    assert a < b
    assert not b < a


def test_sorting_uses_worldid():
    c = WorldObject(worldid=3)
    a = WorldObject(worldid=1)
    b = WorldObject(worldid=2)

    result = sorted([c, a, b])

    assert [obj.worldid for obj in result] == [1, 2, 3]


def test_remove_unregisters_object():
    obj = WorldObject()
    worldid = obj.worldid

    obj.remove()

    with pytest.raises(WorldObjectNotFound):
        WorldObject.get_object_by_id(worldid)


def test_remove_notifies_remove_listeners():
    obj = WorldObject()
    called = []

    def listener():
        called.append(True)

    obj.add_remove_listener(listener)
    obj.remove()

    assert called == [True]


def test_load_updates_next_id():
    obj = WorldObject()

    WorldObject.reset()
    obj.load(None, 50)

    next_obj = WorldObject()

    assert next_obj.worldid == 51


def test_remove_twice_is_not_supported():
    obj = WorldObject()

    obj.remove()

    # ChangeListener.end() clears the listener lists, so the second remove fails.
    with pytest.raises(TypeError):
        obj.remove()


def test_worldobject_registry_uses_weak_references():
    obj = WorldObject()
    worldid = obj.worldid

    assert WorldObject.get_object_by_id(worldid) is obj

    del obj
    gc.collect()

    with pytest.raises(WorldObjectNotFound):
        WorldObject.get_object_by_id(worldid)


def test_duplicate_worldid_allowed_after_gc():
    obj = WorldObject(worldid=5)

    del obj
    gc.collect()

    new_obj = WorldObject(worldid=5)

    assert new_obj.worldid == 5
