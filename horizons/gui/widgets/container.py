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


class AutoResizeContainer(Container):
	"""A regular pychan container, that implements resizeToContent"""

	def resizeToContent(self):
		"""resizeToContent for unlayouted containers. Sets size to smallest box"""
		for child in self.children:
			child.adaptLayout() # recalc values for children

		max_x = max_y = 0
		for child in self.children:
			x = child.position[0] + child.size[0]
			y = child.position[1] + child.size[1]
			if x > max_x:
				max_x = x
			if y > max_y:
				max_y = y
		self.size = (max_x, max_y)
