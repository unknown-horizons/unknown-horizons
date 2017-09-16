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


class PychanChildFinder(dict):
	"""Caches child references of a gui object, since pychan's findChild function is expensive.
	Init it with your gui and use like a dictionary or call object directly (__call__)"""
	def __init__(self, gui):
		super().__init__()
		self.gui = gui

	def __getitem__(self, key):
		try:
			return dict.__getitem__(self, key)
		except KeyError:
			self[key] = self.gui.findChild(name=key)
			return self[key]

	def __call__(self, name):
		return self[name]
