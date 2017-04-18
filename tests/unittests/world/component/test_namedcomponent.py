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

from unittest import TestCase

from horizons.component.namedcomponent import NamedComponent


class MockNameComponent(NamedComponent):
	def _possible_names(self):
		return ['Test']

class TestNamedComponent(TestCase):
	def tearDown(self):
		NamedComponent.reset()

	@classmethod
	def make_component(cls, name=None):
		class Instance(object):
			def __init__(self):
				super(Instance, self).__init__()
				self.instance = self
				self.session = self
				self.random = self

			def choice(self, seq):
				return seq[0]

		component = MockNameComponent(name)
		component.instance = Instance()
		component.initialize()
		return component

	def test_new_default_name(self):
		component = self.make_component()
		self.assertEqual(component.name, 'Test')
		component2 = self.make_component()
		self.assertEqual(component2.name, 'Test 2')
		component3 = self.make_component()
		self.assertEqual(component3.name, 'Test 3')

	def test_duplicates(self):
		component = self.make_component()
		self.assertEqual(component.name, 'Test')
		component2 = self.make_component()
		self.assertEqual(component2.name, 'Test 2')
		component2.set_name('Test')
		self.assertEqual(component.name, 'Test')
		self.assertEqual(component2.name, 'Test')

		component.set_name('Test name')
		component3 = self.make_component()
		self.assertEqual(component3.name, 'Test 2')

		component2.set_name('Test name')
		component4 = self.make_component()
		self.assertEqual(component4.name, 'Test')

	def test_rename_none(self):
		component = self.make_component()
		self.assertEqual(component.name, 'Test')
		component.set_name('Test name')
		self.assertEqual(component.name, 'Test name')
		component.set_name(None)
		self.assertEqual(component.name, 'Test')

	def test_new_named_object(self):
		component = self.make_component('Test name')
		self.assertEqual(component.name, 'Test name')
		component2 = self.make_component('Test name')
		self.assertEqual(component2.name, 'Test name')

	def test_unchanged_rename(self):
		component = self.make_component()
		self.assertEqual(component.name, 'Test')
		component.set_name('Test')
		self.assertEqual(component.name, 'Test')
		component2 = self.make_component()
		self.assertEqual(component2.name, 'Test 2')
