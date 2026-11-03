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

from unittest import mock

import pytest

from horizons.component.namedcomponent import NamedComponent
from horizons.util.changelistener import ChangeListener


class DummyChangeListener(ChangeListener):
    pass


@pytest.fixture(autouse=True)
def prepare_component(mocker):
    mocker.patch.object(
        NamedComponent,
        "_possible_names",
        return_value=["Test"],
    )

    yield

    NamedComponent.reset()


def make_component(name=None):
    instance = mock.Mock()
    instance.session.random.choice = lambda seq: seq[0]

    component = NamedComponent(name)
    component.instance = instance
    component.initialize()

    return component


def test_duplicates():
    component = make_component()

    component2 = make_component()
    component2.set_name("Test")

    assert component.name == "Test"
    assert component2.name == "Test"

    component.set_name("Test name")

    component3 = make_component()
    assert component3.name == "Test 2"

    component2.set_name("Test name")

    component4 = make_component()
    assert component4.name == "Test"


def test_rename_none():
    component = make_component()

    assert component.name == "Test"

    component.set_name("Test name")
    assert component.name == "Test name"

    component.set_name(None)
    assert component.name == "Test"


def test_new_named_object():
    component = make_component("Test name")
    assert component.name == "Test name"

    component2 = make_component("Test name")
    assert component2.name == "Test name"


def test_unchanged_rename():
    component = make_component()
    assert component.name == "Test"

    component.set_name("Test")
    assert component.name == "Test"

    component2 = make_component()
    assert component2.name == "Test 2"


def test_reset():
    make_component()
    make_component()

    assert NamedComponent.names_used == ["Test", "Test 2"]

    NamedComponent.reset()

    assert NamedComponent.names_used == []
    assert make_component().name == "Test"


def test_save():
    component = make_component()

    component.instance.worldid = 42

    db = mock.Mock()

    component.save(db)

    db.assert_called_once_with(
        "INSERT INTO name (rowid, name) VALUES(?, ?)",
        42,
        component.name,
    )


def test_load():
    db = mock.Mock()
    db.return_value = [("Loaded name",)]

    component = NamedComponent()
    component.instance = mock.Mock()

    component.load(db, 7)

    assert component.name == "Loaded name"
    db.assert_called_once_with(
        "SELECT name FROM name WHERE rowid = ?",
        7,
    )


def test_many_default_names():
    components = [make_component() for _ in range(5)]

    assert [c.name for c in components] == [
        "Test",
        "Test 2",
        "Test 3",
        "Test 4",
        "Test 5",
    ]


def test_old_name_becomes_available_again():
    component = make_component()

    assert component.name == "Test"

    component.set_name("Custom")

    component2 = make_component()

    assert component2.name == "Test"


def test_set_name_notifies_listener():
    instance = DummyChangeListener()
    instance._changed = mock.Mock()

    instance.session = mock.Mock()
    instance.session.random.choice = lambda seq: seq[0]

    component = NamedComponent()
    component.instance = instance

    component.initialize()
    instance._changed.assert_called_once()

    component.set_name("Renamed")
    assert instance._changed.call_count == 2
