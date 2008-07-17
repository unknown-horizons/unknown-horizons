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

class Point(object):
	def __init__(self, *args):
		""" 
		Can be initialised with Point(1,2) or tu = (1,2); Point(tu)
		"""
		if len(args) == 1 and isinstance(args[0], tuple):
			self.x = args[0][0]
			self.y = args[0][1]
		elif len(args) == 2: # no need to check for int, who would be stupid enough to pass something else than a number for coords.. 
			self.x = args[0]
			self.y = args[1]

	def distance(self, other):
		if isinstance(other, Point):
			return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
		elif isinstance(other, tuple):
			return ((self.x - other[0]) ** 2 + (self.y - other[1]) ** 2) ** 0.5
		else:
			return other.distance(self)

	def __str__(self):
		""" nice representation for debugging purposes """
		return 'Point(%s, %s)' % (self.x, self.y)
	
	def get_coordinates(self):
		""" Returns point as coordinate
		This is useful, because Rect supports this too.
		"""
		return [(self.x, self.y)]