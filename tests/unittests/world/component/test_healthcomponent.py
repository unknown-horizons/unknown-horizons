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

from horizons.ext.dummy import Dummy
from horizons.component.healthcomponent import HealthComponent

from mock import Mock


class TestHealthComponent(TestCase):

	def setUp(self):
		self.instance = Mock()
		self.instance.session = Dummy()

		self.component = HealthComponent(20)
		self.component.instance = self.instance
		self.component.initialize()

	def test_trivial(self):
		self.assertEqual(self.component.health, 20)
		self.assertEqual(self.component.max_health, 20)

	def test_maxhealth_required(self):
		self.assertRaises(AssertionError, HealthComponent, None)

	def test_damage(self):
		self.component.deal_damage(1, 19)
		self.assertEqual(self.component.health, 1)
		self.assertEqual(self.component.max_health, 20)
		self.assertFalse(self.instance.remove.called)

	def test_damage_zero_health(self):
		self.component.deal_damage(1, 20)
		self.assertEqual(self.component.health, 0)
		self.assertEqual(self.component.max_health, 20)
		self.assertTrue(self.instance.remove.called)

	def test_huge_damage(self):
		self.component.deal_damage(1, 300)
		self.assertEqual(self.component.health, 0)
		self.assertEqual(self.component.max_health, 20)
		self.assertTrue(self.instance.remove.called)
