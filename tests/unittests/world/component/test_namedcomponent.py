# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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
		return [u'Test']

class TestNamedComponent(TestCase):
	def tearDown(self):
		NamedComponent.reset()

	@classmethod
	def make_component(cls, name = None):
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
		self.assertEquals(component.name, u'Test')
		component2 = self.make_component()
		self.assertEquals(component2.name, u'Test 2')
		component3 = self.make_component()
		self.assertEquals(component3.name, u'Test 3')

	def test_duplicates(self):
		component = self.make_component()
		self.assertEquals(component.name, u'Test')
		component2 = self.make_component()
		self.assertEquals(component2.name, u'Test 2')
		component2.set_name('Test')
		self.assertEquals(component.name, u'Test')
		self.assertEquals(component2.name, u'Test')

		component.set_name(u'Test name')
		component3 = self.make_component()
		self.assertEquals(component3.name, u'Test 2')

		component2.set_name(u'Test name')
		component4 = self.make_component()
		self.assertEqual(component4.name, u'Test')

	def test_rename_none(self):
		component = self.make_component()
		self.assertEquals(component.name, u'Test')
		component.set_name(u'Test name')
		self.assertEquals(component.name, u'Test name')
		component.set_name(None)
		self.assertEquals(component.name, u'Test')

	def test_new_named_object(self):
		component = self.make_component(u'Test name')
		self.assertEquals(component.name, u'Test name')
		component2 = self.make_component(u'Test name')
		self.assertEqual(component2.name, u'Test name')

	def test_unchanged_rename(self):
		component = self.make_component()
		self.assertEquals(component.name, u'Test')
		component.set_name(u'Test')
		self.assertEquals(component.name, u'Test')
		component2 = self.make_component()
		self.assertEquals(component2.name, u'Test 2')
