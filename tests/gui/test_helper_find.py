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
from typing import Optional, Set
from unittest import mock

from tests.gui.helper import GuiHelper


class Widget:
	"""
	Fake widget with a name, children and possible a parent. All children of this widget will
	get their parent attribute set to this widget.
	"""
	def __init__(self, name, children=None):
		self.name = name
		self.parent = None # type: Optional[Widget]
		self.children = children or []
		for c in self.children:
			c.parent = self

	def __repr__(self):
		return self.name

	def __hash__(self):
		return id(self)


class FindWidgetTest(unittest.TestCase):
	"""
	Tests about finding widgets in pychan's internal lists.
	"""
	def setUp(self):
		self.widgets = set() # type: Set[Widget]

		def w(name, children=None):
			widget = Widget(name, children)
			self.widgets.add(widget)
			return widget

		self.w = w

		helper = GuiHelper(mock.Mock(), mock.Mock())
		self.find = lambda x: helper._find(self.widgets, x)

	def test_simple(self):
		"""
		Single widget in the global list.
		"""
		target = self.w('target')
		self.assertEqual(self.find('target'), target)

	def test_parent(self):
		"""
		Single widget with a child.
		"""
		target = self.w('target')
		self.w('foobar', [
			target
		])

		self.assertEqual(self.find('target'), target)

	def test_hierarchy(self):
		"""
		Target widget with multiple parents and another widget with the same name, but
		without parent.
		"""
		target = self.w('target')

		self.w('bla', [
			self.w('baz', [
				target
			])
		])
		self.w('foobar')
		self.w('target')

		self.assertEqual(self.find('bla/baz/target'), target)

	def test_hierarchy_incomplete_path(self):
		"""
		Target with multiple parents, select it while omitting one parent in the search
		path.
		"""
		target = self.w('target')

		self.w('bla', [
			self.w('baz', [
				target
			])
		])
		self.w('foobar')
		self.w('target')

		self.assertEqual(self.find('bla/target'), target)

	def test_hierarchy_returns_widget_with_best_matching_path(self):
		"""
		If we have multiple matches for a path, return the one that fits most closely,
		i.e. the one with the shortest path of names.
		"""
		target1 = self.w('target')
		target2 = self.w('target')

		self.w('bla', [
			self.w('baz', [
				target1
			])
		])
		self.w('bla', [
			target2
		])

		self.assertEqual(self.find('bla/target'), target2)

	def test_ambigious_error(self):
		"""
		If a single best match can't be found, an error is raised instead.
		"""
		target1 = self.w('target')
		target2 = self.w('target')

		self.w('bla', [
			target1
		])
		self.w('bla', [
			target2
		])

		try:
			self.find('bla/target')
		except Exception as e:
			self.assertEqual(str(e), 'Ambigious specification bla/target, found 2 matches')
		else:
			self.fail('No exception raised')

	def test_hierarchy_not_absolute_path(self):
		"""
		Target with multiple parents, select it without specifing the top-most widget.
		"""
		target = self.w('target')

		self.w('bla', [
			self.w('baz', [
				target
			])
		])
		self.w('foobar')
		self.w('target')

		self.assertEqual(self.find('baz/target'), target)

	def test_wrong_search_path(self):
		"""
		A previous implementation had a bug where the code would go in a dead end when one
		part of the path matches, but children below won't. Make sure this doesn't happen
		again.
		"""
		target = self.w('target')

		self.w('wrongpath', [
			self.w('foobar')
		])
		self.w('foobar', [
			target
		])

		self.assertEqual(self.find('foobar/target'), target)

	def test_multiple_siblings(self):
		"""
		Target widget with multiple parents and multiple siblings.
		"""
		target = self.w('target')

		self.w('bla', [
			self.w('baz', [
				self.w('sibling1'),
				target,
				self.w('sibling2'),
				self.w('sibling3'),
			])
		])

		self.assertEqual(self.find('bla/baz/target'), target)

	def test_target_with_childrens(self):
		"""
		Make sure that the target is still found even if it has children itself.
		"""
		target = self.w('target', [
			self.w('baz'),
			self.w('foo', [
				self.w('bar')
			]),
		])

		self.w('bla', [
			self.w('baz', [
				target
			])
		])

		self.assertEqual(self.find('bla/baz/target'), target)
