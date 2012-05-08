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
from horizons.world.units.collectors.collector import Job, JobList
from horizons.util.shapes.point import Point


class TestJobList(TestCase):

	def distance(self, test_list, ident):
		return test_list.collector.position.distance(test_list[ident].object.loading_area)

	def create_list(self, order):
		test_list = JobList(TestCollector(0, 0), order)
		test_list.append(Job(TestObject(1, 3, 3), [Job.ResListEntry(3, 4, False)]))
		test_list.append(Job(TestObject(2, 1, 1), [Job.ResListEntry(1, 2, False)]))
		test_list.append(Job(TestObject(3, 2, 2), [Job.ResListEntry(2, 3, False)]))
		return test_list

	def test_sort_distance(self):
		test_list = self.create_list(JobList.order_by.distance)
		test_list.sort_jobs()

		self.assertTrue(self.distance(test_list, 0) <= self.distance(test_list, 1))
		self.assertTrue(self.distance(test_list, 1) <= self.distance(test_list, 2))

		# Make sure everything was sorted in order
		self.assertEqual(test_list[0].object.id, 2)
		self.assertEqual(test_list[1].object.id, 3)
		self.assertEqual(test_list[2].object.id, 1)

	def test_sort_fewest_available(self):
		test_list = self.create_list(JobList.order_by.fewest_available)
		test_list._sort_jobs_fewest_available(False)

		# Make sure everything was sorted in order
		self.assertEqual(test_list[0].object.id, 3)
		self.assertEqual(test_list[1].object.id, 1)
		self.assertEqual(test_list[2].object.id, 2)

	def test_sort_fewest_available_and_distance(self):
		test_list = JobList(TestCollector(0, 0), JobList.order_by.fewest_available_and_distance)

		test_list.append(Job(TestObject(1, 3, 3), [Job.ResListEntry(2, 4, False)]))
		test_list.append(Job(TestObject(2, 1, 1), [Job.ResListEntry(1, 2, False)]))
		test_list.append(Job(TestObject(3, 2, 2), [Job.ResListEntry(2, 3, False)]))
		test_list._sort_jobs_fewest_available_and_distance()

		# Make sure everything was sorted in order of fewest available with secondary
		# sorting by distance
		self.assertEqual(test_list[0].object.id, 3)
		self.assertEqual(test_list[1].object.id, 1)
		self.assertEqual(test_list[2].object.id, 2)

	def test_sort_for_storage(self):
		test_list = JobList(TestCollector(0, 0), JobList.order_by.for_storage_collector)

		test_list.append(Job(TestObject(1, 3, 3), [Job.ResListEntry(2, 4, False)]))
		test_list.append(Job(TestObject(2, 1, 1), [Job.ResListEntry(1, 2, False)]))
		test_list.append(Job(TestObject(3, 2, 2), [Job.ResListEntry(2, 3, False)]))
		test_list.append(Job(TestObject(4, 9, 0), [Job.ResListEntry(4, 9, target_inventory_full=True)]))
		test_list.sort_jobs()

		# Make sure everything was sorted in order of fewest available with secondary
		# sorting by distance
		self.assertEqual(test_list[0].object.id, 4)
		self.assertEqual(test_list[1].object.id, 3)
		self.assertEqual(test_list[2].object.id, 1)
		self.assertEqual(test_list[3].object.id, 2)

		# Both give res 2, but TestObject with id 3 is closer
		self.assertTrue(self.distance(test_list, 1) <= self.distance(test_list, 2))


class TestCollector(object):
	"""Dummy collector that only provides what we need to run the tests."""

	def __init__(self, x, y):
		self.position = Point(x, y)


	def get_home_inventory(self):
		"""Return a dummy inventory"""
		return {1: 3,
		        2: 1,
		        3: 2,
		        4: 8,
		        5: 4}

class TestObject(object):
	"""Dummy object that acts as building as far as we need it to"""

	def __init__(self, id, x, y):
		self.id = id
		self.loading_area = Point(x, y)


