# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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


from fife.extensions.pychan.widgets import Container
from fife.extensions.pychan.widgets.common import BoolAttr, UnicodeAttr


class AutoResizeContainer(Container):
	"""A regular pychan container, that implements resizeToContent"""

	def resizeToContent(self):
		"""resizeToContent for unlayouted containers. Sets size to smallest box"""
		for child in self.children:
			child.adaptLayout() # recalculate values for children

		max_x = max_y = 0
		for child in self.children:
			x = child.position[0] + child.size[0]
			y = child.position[1] + child.size[1]
			if x > max_x:
				max_x = x
			if y > max_y:
				max_y = y
		self.size = (max_x, max_y)


class TabContainer(Container):
	"""A regular pychan container with fixed width and auto-resizing.

	Used as parent widget for all xml-defined tabs.
	Ideally, you do not need to specify its size at all."""
	ATTRIBUTES = AutoResizeContainer.ATTRIBUTES + [
		UnicodeAttr('headline'), BoolAttr('rename'),
		UnicodeAttr('left_icon'), UnicodeAttr('right_icon'),
	]

	def __init__(self, headline=None, rename=False, fixed_width=0,
	                   left_icon=None, right_icon=None, **kwargs):
		super(TabContainer, self).__init__(**kwargs)
		self.headline = headline
		# TODO make this work and do something at all:
		self.rename = rename
		# TODO make this work as attribute:
		self.fixed_width = 225
		self.left_icon = left_icon
		self.right_icon = right_icon
		self.adaptLayout()

	def resizeToContent(self):
		for child in self.children:
			child.adaptLayout()
		if not self.children:
			max_y = 0
		else:
			max_y = max(child.position[1] + child.size[1] for child in self.children)
		self.size = (self.fixed_width, max_y)
		self.max_size = (self.fixed_width, max_y)

	def _get_rename(self):
		return self.__rename

	def _set_rename(self, rename):
		self.__rename = rename

	rename = property(_get_rename, _set_rename)

	def _get_headline(self):
		return self.__headline

	def _set_headline(self, headline):
		self.__headline = headline

	headline = property(_get_headline, _set_headline)
