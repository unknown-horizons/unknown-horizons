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

import horizons.main

class ColorIter(object):
	"""Makes iterating through standard colors possible"""
	def __iter__(self):
		return self

	def next(self):
		try:
			if hasattr(self, 'last'):
				id = horizons.main.db('SELECT id FROM colors WHERE id > ? ORDER BY id LIMIT 1', self.last)[0][0]
			else:
				id = horizons.main.db('SELECT id FROM colors ORDER BY id LIMIT 1')[0][0]
		except:
			raise StopIteration
		self.last = id
		return Color[id]

class ColorMeta(type):
	def __getitem__(cls, key):
		"""Gets a color by name or id in the db"""
		if key == 0:
			return None
		r, g, b = horizons.main.db('SELECT red, green, blue FROM colors WHERE name = ? OR id = ?',
		                           key, key)[0]
		c = Color(r, g, b)
		return c

	def __iter__(cls):
		return ColorIter()

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
		@params: float (0.0, 1.0) or int (0, 255)
		"""
		if isinstance(r, float) and r >= 0.0 and r <= 1.0:
			r = int(r * 255)
		if isinstance(g, float) and g >= 0.0 and g <= 1.0:
			g = int(g * 255)
		if isinstance(b, float) and b >= 0.0 and b <= 1.0:
			b = int(b * 255)
		if isinstance(a, float) and a >= 0.0 and a <= 1.0:
			a = int(a * 255)
		assert(isinstance(r, int) and isinstance(b, int) and isinstance(b, int) and isinstance(a, int))
		self.r, self.g, self.b, self.a = r, g, b, a
		self.name = None
		try:
			# load name for the color, if it's a standard color
			self.name, self.id = horizons.main.db('SELECT name, rowid FROM colors WHERE red = ? AND green = ? AND blue = ?', self.r, self.g, self.b)[0]
		except:
			pass

	def to_tuple(self):
		"""Returns color as (r, g, b)-tuple, where each value is between 0 and 255"""
		return (self.r, self.g, self.b)

	@property
	def is_default_color(self):
		return hasattr(self, 'id')

	def __str__(self):
		return 'Color'+str(self.to_tuple())

	def __eq__(self, other):
		return(self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a)

	def __hash__(self):
		return hash("%s%s%s%s" % (self.r, self.g, self.b, self.a))
