# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from tests.unittests import TestCase

from horizons.world.production.productionline import _ProductionLineData, ProductionLine


class TestBase(TestCase):

	def add_line(self, ident, time, changes_animation, resources=None, units=None):
		"""Add a new production line
		@param ident: numeric value
		@param time: production time
		@param changes_animation: bool
		@param resources: mapping of {resource: amount}
		@param units: mapping of {unit: amount}
		"""
		self.db('INSERT INTO data.production_line (id, time, changes_animation) \
				 VALUES (?, ?, ?)', ident, time, int(changes_animation))

		if resources:
			self.db.execute_many(
				'INSERT INTO balance.production (production_line, resource, amount) \
				 VALUES (?, ?, ?)',
				[(ident, res, amount) for (res, amount) in resources.items()]
			)

		if units:
			self.db.execute_many(
				'INSERT INTO balance.unit_production (production_line, unit, amount) \
				 VALUES (?, ?, ?)',
				[(ident, unit, amount) for (unit, amount) in units.items()]
			)


class TestProductionLineData(TestBase):

	def test_init_unknown_identifier(self):
		self.assertRaises(IndexError, _ProductionLineData, 1)

	def test_init(self):
		self.add_line(1, 5, 0, {2: 3, 4: -5}, {10: 4, 12: 8})
		self.add_line(2, 4, 1, {2: 5}, {10: 7})

		data = _ProductionLineData(1)
		self.assertEqual(data.time, 5)
		self.assertEqual(data.changes_animation, False)
		self.assertEqual(data.production, {2: 3, 4: -5})
		self.assertEqual(data.produced_res, {2: 3})
		self.assertEqual(data.consumed_res, {4: -5})
		self.assertEqual(data.unit_production, {10: 4, 12: 8})

	def test_no_zero_production_amount(self):
		self.add_line(1, 5, 0, {3: 0})
		self.assertRaises(AssertionError, _ProductionLineData, 1)

	def test_readonly(self):
		self.add_line(1, 5, 0)
		data = _ProductionLineData(1)

		def tmp():
			data.produced_res = 5
		self.assertRaises(TypeError, tmp)


class TestProductionLine(TestBase):

	def setUp(self):
		"""Clear ProductionLine cache."""
		ProductionLine.reset()
		super(TestProductionLine, self).setUp()

	def test_init_unknown_identifier(self):
		self.assertRaises(IndexError, ProductionLine, 1)
		self.assertRaises(IndexError, ProductionLine.load_data, 1)

	def test_alter_production_time(self):
		self.add_line(1, 10, 0)
		line = ProductionLine(1)

		self.assertEqual(line.time, 10)

		line.alter_production_time(2)
		self.assertEqual(line.time, 20)

		# Test that it modifies the original value (10)
		line.alter_production_time(2)
		self.assertEqual(line.time, 20)

		line.alter_production_time(1.5)
		self.assertEqual(line.time, 15.0)

		# should this throw an error?
		# line.alter_production_time(0)

	def test_change_amount(self):
		self.add_line(1, 10, 0, {2: 3, 4: -5})
		line = ProductionLine(1)

		line.change_amount(2, 10)
		self.assertEqual(line.production, {2: 10, 4: -5})
		self.assertEqual(line.produced_res, {2: 10})
		self.assertEqual(line.consumed_res, {4: -5})

		line.change_amount(4, -1)
		self.assertEqual(line.production, {2: 10, 4: -1})
		self.assertEqual(line.produced_res, {2: 10})
		self.assertEqual(line.consumed_res, {4: -1})

		# should these throw an error?
		# line.change_amount(X, 0)
		# line.change_amount(2, -3) - produced becomes consumed
		# line.change_amount(4, 3)  - consumed becomes produced

	def test_reset(self):
		self.add_line(1, 10, 0)
		self.assertFalse(ProductionLine.data)

		ProductionLine.load_data(1)
		self.assertTrue(ProductionLine.data)

		ProductionLine.reset()
		self.assertFalse(ProductionLine.data)
