# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import game.main

class ColorIter(object):
	def __iter__(self):
		return self

	def next(self):
		try:
			if hasattr(self, 'last'):
				id = game.main.db('SELECT rowid from data.colors where rowid > ? order by rowid limit 1', self.last)[0][0]
			else:
				id = game.main.db('SELECT rowid from data.colors order by rowid limit 1')[0][0]
		except:
			raise StopIteration
		self.last = id
		return Color[id]

class ColorMeta(type):
	def __getitem__(cls, key):
		r,g,b = game.main.db('SELECT red,green,blue from data.colors where %s = ?' % ('name' if isinstance(key, (str, unicode)) else 'rowid',), key)[0]
		c = Color(r, g, b)
		return c

	def __iter__(cls):
		return ColorIter()

class Color(object):
	__metaclass__ = ColorMeta
	def __init__(self, r = 0, g = 0, b = 0, a = 255):
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
		try:
			self.name, self.id = game.main.db('SELECT name,rowid from data.colors where red = ? and green = ? and blue = ?', self.r, self.g, self.b)[0]
		except:
			pass
