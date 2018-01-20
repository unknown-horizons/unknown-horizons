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

import unittest

from horizons.world.building import BuildingClass
from horizons.world.ingametype import IngameType
from horizons.world.units import UnitClass


class IngameTypeClassesTest(unittest.TestCase):

	def test_ingametype(self):
		t = IngameType(1, {
			'baseclass': 'building.DefaultBuilding',
			'name': 'BuildingName',
			'radius': 0,
			'components': [],
			'actionsets': []
		})

		self.assertEqual(t.__name__, 'Type[1]')
		self.assertEqual(t.class_name, 'DefaultBuilding')
		self.assertEqual(t.name, 'BuildingName')
		self.assertEqual(t.id, 1)

	def test_buildingclass(self):
		yaml_data = {
			'baseclass': 'building.DefaultBuilding',
			'name': 'BuildingName',
			'radius': 0,
			'components': [],
			'actionsets': [],
			'tier': 1,
			'tooltip_text': 'Tooltip',
			'size_x': 1,
			'size_y': 1,
			'inhabitants': 0,
			'buildingcosts': 0,
			'cost': 0,
			'cost_inactive': 0,
		}

		t = BuildingClass(None, 1, yaml_data)
		self.assertEqual(t.__name__, 'Building[1]')
		self.assertEqual(t.class_name, 'DefaultBuilding')
		self.assertEqual(t.name, 'BuildingName')
		self.assertEqual(t.id, 1)
		self.assertEqual(str(t), 'Building[1](BuildingName)')

	def test_unitclass(self):
		t = UnitClass(1, {
			'baseclass': 'unit.Unit',
			'name': 'UnitName',
			'radius': 0,
			'components': [],
			'actionsets': []
		})

		self.assertEqual(t.__name__, 'Unit[1]')
		self.assertEqual(t.class_name, 'Unit')
		self.assertEqual(t.name, 'UnitName')
		self.assertEqual(t.id, 1)
