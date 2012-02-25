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

from tests.unittests import TestCase

from horizons.world.production.productionline import ProductionLine


class TestBase(TestCase):

	def add_line(self, ident, units=None):
		"""Add a new production line
		@param ident: numeric value
		@param time: production time
		@param changes_animation: bool
		@param resources: mapping of {resource: amount}
		@param units: mapping of {unit: amount}
		"""
		if units:
			self.db.execute_many(
				'INSERT INTO unit_production (production_line, unit, amount) \
				 VALUES (?, ?, ?)',
				[(ident, unit, amount) for (unit, amount) in units.items()]
			)


class TestProductionLineData(TestBase):

	def test_init(self):
		# NOTE: this has been broken by optimisations and will soon be moved to yaml, therefore not fixing it now
		#self.add_line(1, {10: 4, 12: 8})

		data = {'enabled_by_default': False,
		        'time': 90,
		        'level': [0, 1, 2],
		        'changes_animation': False,
		        'produces': [[14, 1]],
		        'consumes': [[19, -1]]
		}
		data = ProductionLine(1, data)
		self.assertEqual(data.time, 90)
		self.assertEqual(data.changes_animation, False)
		self.assertEqual(data.production, {14: 1, 19: -1})
		self.assertEqual(data.produced_res, {14: 1})
		self.assertEqual(data.consumed_res, {19: -1})
		#self.assertEqual(data.unit_production, {10: 4, 12: 8})

class TestProductionLine(TestBase):

	def setUp(self):
		"""Clear ProductionLine cache."""
		super(TestProductionLine, self).setUp()

	def test_alter_production_time(self):
		data = { 'time': 10 }
		line = ProductionLine(1, data)

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
		data = {
		        'time': 10,
		        'produces': [[2, 3]],
		        'consumes': [[4, -5]]
		}
		line = ProductionLine(1, data)

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
