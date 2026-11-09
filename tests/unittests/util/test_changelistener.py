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

import pytest

from horizons.util.changelistener import (
    ChangeListener,
    metaChangeListenerDecorator,
)


def test_change_listener_called():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener)

    obj._changed()

    assert called == [True]


def test_add_change_listener_call_now():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener, call_listener_now=True)

    assert called == [True]


def test_remove_change_listener():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener)
    obj.remove_change_listener(listener)

    obj._changed()

    assert called == []


def test_discard_existing_listener():
    obj = ChangeListener()

    def listener():
        pass

    obj.add_change_listener(listener)

    obj.discard_change_listener(listener)

    assert not obj.has_change_listener(listener)


def test_discard_missing_listener():
    obj = ChangeListener()

    def listener():
        pass

    obj.discard_change_listener(listener)


def test_clear_change_listeners():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener)

    obj.clear_change_listeners()

    obj._changed()

    assert called == []


def test_add_change_listener_no_duplicates():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener, no_duplicates=True)
    obj.add_change_listener(listener, no_duplicates=True)

    obj._changed()

    assert len(called) == 1


def test_add_change_listener_duplicates_allowed():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener)
    obj.add_change_listener(listener)

    obj._changed()

    assert len(called) == 2


def test_listener_can_remove_itself():
    obj = ChangeListener()

    calls = []

    def listener():
        calls.append(True)
        obj.remove_change_listener(listener)

    obj.add_change_listener(listener)

    obj._changed()
    obj._changed()

    assert calls == [True]


def test_removed_listener_is_not_called_in_same_dispatch_cycle():
    obj = ChangeListener()

    calls = []

    removed = False

    def second():
        calls.append("second")

    def first():
        nonlocal removed

        calls.append("first")

        if not removed:
            obj.remove_change_listener(second)
            removed = True

    obj.add_change_listener(first)
    obj.add_change_listener(second)

    obj._changed()
    obj._changed()

    assert calls == [
        "first",
        "first",
    ]


def test_remove_unknown_listener_raises():
    obj = ChangeListener()

    def listener():
        pass

    with pytest.raises(ValueError):
        obj.remove_change_listener(listener)


def test_remove_listener_called_on_remove():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_remove_listener(listener)

    obj.remove()

    assert called == [True]


def test_remove_remove_listener():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_remove_listener(listener)

    obj.remove_remove_listener(listener)

    obj.remove()

    assert called == []


def test_load_resets_listener_state():
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener)

    obj.load(None, 0)

    obj._changed()

    assert called == []


@metaChangeListenerDecorator("finished")
class FinishedObject:
    pass


def test_meta_listener_called():
    obj = FinishedObject()

    called = []

    def listener(instance):
        called.append(instance)

    obj.add_finished_listener(listener)

    obj.on_finished()

    assert called == [obj]


@metaChangeListenerDecorator("event")
class EventObject:
    pass


def test_meta_has_listener():
    obj = EventObject()

    def listener(instance):
        pass

    obj.add_event_listener(listener)

    assert obj.has_event_listener(listener)


@metaChangeListenerDecorator("event")
class EventObjectRemove:
    pass


def test_meta_remove_listener():
    obj = EventObjectRemove()

    called = []

    def listener(instance):
        called.append(True)

    obj.add_event_listener(listener)
    obj.remove_event_listener(listener)

    obj.on_event()

    assert called == []


@pytest.mark.parametrize(
    "duplicates,expected",
    [
        (False, 2),
        (True, 1),
    ],
)
def test_duplicate_listener_behavior(duplicates, expected):
    obj = ChangeListener()

    called = []

    def listener():
        called.append(True)

    obj.add_change_listener(listener, no_duplicates=duplicates)
    obj.add_change_listener(listener, no_duplicates=duplicates)

    obj._changed()

    assert len(called) == expected
