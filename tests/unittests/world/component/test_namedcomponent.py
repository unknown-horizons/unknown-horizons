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

from unittest import mock

import pytest

from horizons.component.namedcomponent import NamedComponent


@pytest.fixture(autouse=True)
def prepare_component(request, mocker):
	mocker.patch.object(NamedComponent, '_possible_names', return_value=['Test'])
	request.addfinalizer(NamedComponent.reset)


def make_component(name=None):
	instance = mock.Mock()
	instance.session.random.choice = lambda seq: seq[0]

	component = NamedComponent(name)
	component.instance = instance
	component.initialize()
	return component


def test_new_default_name():
	component = make_component()
	assert component.name == 'Test'
	component2 = make_component()
	assert component2.name == 'Test 2'
	component3 = make_component()
	assert component3.name == 'Test 3'


def test_duplicates():
	component = make_component()
	component2 = make_component()
	component2.set_name('Test')

	assert component.name == 'Test'
	assert component2.name == 'Test'

	component.set_name('Test name')
	component3 = make_component()
	assert component3.name == 'Test 2'

	component2.set_name('Test name')
	component4 = make_component()
	assert component4.name == 'Test'


def test_rename_none():
	component = make_component()
	assert component.name == 'Test'
	component.set_name('Test name')
	assert component.name == 'Test name'
	component.set_name(None)
	assert component.name == 'Test'


def test_new_named_object():
	component = make_component('Test name')
	assert component.name == 'Test name'
	component2 = make_component('Test name')
	assert component2.name == 'Test name'


def test_unchanged_rename():
	component = make_component()
	assert component.name == 'Test'
	component.set_name('Test')
	assert component.name == 'Test'
	component2 = make_component()
	assert component2.name == 'Test 2'


def test_reset():
	component = make_component()
	component2 = make_component()

	assert NamedComponent.names_used == ['Test', 'Test 2']
	NamedComponent.reset()

	assert NamedComponent.names_used == []
	assert make_component().name == 'Test'
