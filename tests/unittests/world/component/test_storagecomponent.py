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

from horizons.component.storagecomponent import StorageComponent


@pytest.fixture
def inventory():
    return Mock()


@pytest.fixture
def component(inventory):
    instance = Mock()

    component = StorageComponent(inventory)
    component.instance = instance

    return component, instance, inventory


def test_has_own_inventory(inventory):
    component = StorageComponent(inventory)

    assert component.inventory is inventory
    assert component.has_own_inventory


def test_initialize_adds_change_listener(component):
    component, _, inventory = component

    component.initialize()

    inventory.add_change_listener.assert_called_once_with(
        component.something_changed
    )


def test_remove_clears_inventory(component):
    component, _, inventory = component

    component.remove()

    inventory.clear_change_listeners.assert_called_once_with()
    inventory.reset_all.assert_called_once_with()


def test_remove_shared_inventory(component):
    component, _, inventory = component

    component.has_own_inventory = False

    component.remove()

    inventory.clear_change_listeners.assert_not_called()
    inventory.reset_all.assert_not_called()


def test_save_own_inventory(component):
    component, instance, inventory = component

    instance.worldid = 42

    db = Mock()

    component.save(db)

    inventory.save.assert_called_once_with(db, 42)


def test_save_shared_inventory(component):
    component, _, inventory = component

    component.has_own_inventory = False

    db = Mock()

    component.save(db)

    inventory.save.assert_not_called()


def test_load_inventory(monkeypatch, component):
    component, _, inventory = component

    db = Mock()
    scheduler = Mock()

    monkeypatch.setattr(
        "horizons.component.storagecomponent.Scheduler",
        Mock(return_value=scheduler),
    )

    component.initialize = Mock()

    component.load(db, 17)

    component.initialize.assert_called_once_with()
    inventory.load.assert_called_once_with(db, 17)
    scheduler.add_new_object.assert_called_once_with(
        component.something_changed,
        component,
        run_in=0,
    )


def test_load_shared_inventory(monkeypatch, component):
    component, _, inventory = component

    component.has_own_inventory = False

    db = Mock()
    scheduler = Mock()

    monkeypatch.setattr(
        "horizons.component.storagecomponent.Scheduler",
        Mock(return_value=scheduler),
    )

    component.initialize = Mock()

    component.load(db, 17)

    component.initialize.assert_called_once_with()
    inventory.load.assert_not_called()
    scheduler.add_new_object.assert_called_once_with(
        component.something_changed,
        component,
        run_in=0,
    )


def test_something_changed_broadcasts_message(monkeypatch, component):
    component, instance, inventory = component

    inventory._storage = {"resource": 5}

    broadcast = Mock()

    monkeypatch.setattr(
        "horizons.component.storagecomponent.InstanceInventoryUpdated.broadcast",
        broadcast,
    )

    component.something_changed()

    broadcast.assert_called_once_with(
        instance,
        inventory._storage,
    )


def test_get_instance():
    component = StorageComponent.get_instance(
        {"PositiveStorage": {}}
    )

    assert isinstance(component, StorageComponent)
    assert component.has_own_inventory


def test_initialize_shared_inventory():
    inventory = Mock()

    component = StorageComponent(inventory)
    component.has_own_inventory = False

    shared_inventory = Mock()

    storage_component = Mock()
    storage_component.inventory = shared_inventory

    settlement = Mock()
    settlement.get_component.return_value = storage_component

    instance = Mock()
    instance.settlement = settlement

    component.instance = instance

    component.initialize()

    assert component.inventory is shared_inventory

    settlement.get_component.assert_called_once_with(
        StorageComponent
    )

    shared_inventory.add_change_listener.assert_called_once_with(
        component.something_changed
    )
