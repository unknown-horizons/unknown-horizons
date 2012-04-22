#!/usr/bin/env python

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

from horizons.component import Component


class A(Component):
	NAME = 'A'

class B(Component):
	NAME = 'B'
	DEPENDENCIES = [A]

class C(Component):
	NAME = 'C'


class TestComponent(TestCase):

	def test_dependencysorting(self):
		a = A()
		b = B()
		components = [b, C(), a]
		components.sort()
		self.assertTrue(components.index(b) > components.index(a))
		# Trigger __lt__
		self.assertFalse(b < a)
		self.assertTrue(a < b)
		# Trigger __gt__
		self.assertTrue(b > a)
		self.assertFalse(a > b)
