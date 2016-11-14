# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from horizons.gui.windows import Window, WindowManager


class DummyWindow(Window):

	def __init__(self, windows):
		Window.__init__(self, windows)
		self.visible = False

	def show(self):
		self.visible = True

	def hide(self):
		self.visible = False


class TestWindowManager(unittest.TestCase):

	def setUp(self):
		self.windows = WindowManager()

	def test_trivial(self):
		assert not self.windows.visible

	def test_open_hide(self):
		window1 = DummyWindow(self.windows)
		self.windows.open(window1)
		assert self.windows.visible
		assert window1.visible

		window2 = DummyWindow(self.windows)
		self.windows.open(window2)
		assert self.windows.visible
		assert not window1.visible
		assert window2.visible

	def test_close(self):
		window1 = DummyWindow(self.windows)
		window2 = DummyWindow(self.windows)
		self.windows.open(window1)
		self.windows.open(window2)
		assert not window1.visible
		assert window2.visible

		self.windows.close()
		assert window1.visible
		assert not window2.visible

		self.windows.close()
		assert not window1.visible
		assert not window2.visible
		assert not self.windows.visible

	def test_toggle_single_window(self):
		window1 = DummyWindow(self.windows)
		assert not window1.visible

		self.windows.toggle(window1)
		assert window1.visible
		self.windows.toggle(window1)
		assert not window1.visible

	def test_toggle_multiple(self):
		"""
		Alternately toggle two windows and make sure we have only
		once instance of each window in the stack.
		"""
		window1 = DummyWindow(self.windows)
		window2 = DummyWindow(self.windows)
		assert not window1.visible
		assert not window2.visible

		self.windows.toggle(window1)
		assert window1.visible
		assert not window2.visible

		self.windows.toggle(window2)
		assert not window1.visible
		assert window2.visible

		self.windows.toggle(window1)
		assert window1.visible
		assert not window2.visible

		self.windows.close()
		self.windows.close()
		assert not self.windows.visible
