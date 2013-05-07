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

import horizons.globals


class ColorMeta(type):
	"""Metaclass allows iteration and indexing of the Color class.

	Example:

		for c in Color:
			pass

		Color['red']
		Color[0]
	"""

	def __getitem__(cls, key):
		"""Gets a color by name or id in the db"""
		if key == 0:
			return None
		r, g, b = horizons.globals.db('SELECT red, green, blue FROM colors WHERE name = ? OR id = ?',
		                           key, key)[0]
		c = Color(r, g, b)
		return c

	def __iter__(cls):
		"""Iterate over all available colors in the db."""
		colors = horizons.globals.db('SELECT id FROM colors ORDER BY id')
		colors = (Color[id] for id, in colors)
		return iter(colors)


class Color(object):
	"""Class for saving a color.
	Colors are saved in 32 bit rgb-format with an alpha value (for transparency).
	32bit mean that each of the for values can only occupy 8 bit, i.e. the value is between
	0 and 255.

	Attributes:
	 r, g, b, a: Color values + Alpha
	 name: name of the Color or None
	"""
	__metaclass__ = ColorMeta

	def __init__(self, r=0, g=0, b=0, a=255):
		"""
		@params: int (0, 255)
		"""
		self.r, self.g, self.b, self.a = r, g, b, a
		query = horizons.globals.db('SELECT name, rowid FROM colors '
		                            'WHERE red = ? AND green = ? AND blue = ?',
		                            self.r, self.g, self.b)
		try:
			# load name for the color, if it's a standard color
			self.name, self.id = query[0]
		except IndexError:
			# id is not set to indicate this is a nondefault color
			self.name = None

	def to_tuple(self):
		"""Returns color as (r, g, b)-tuple, where each value is between 0 and 255"""
		return (self.r, self.g, self.b)

	@property
	def is_default_color(self):
		return hasattr(self, 'id')

	def __str__(self):
		return 'Color' + str(self.to_tuple())

	def __eq__(self, other):
		return self.to_tuple() == other.to_tuple()

	def __hash__(self):
		return hash("%s%s%s%s" % (self.r, self.g, self.b, self.a))
