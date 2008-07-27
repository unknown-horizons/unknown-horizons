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
from game.world.storage import Storage
from game.util import WorldObject

class Settlement(WorldObject):
	"""The Settlement class describes a settlement and stores all the necessary information
	like name, current inhabitants, lists of tiles and houses, etc belonging to the village."""
	def __init__(self, owner):
		"""
		@param owner: player that owns the settlement
		"""
		self.name = game.main.db("SELECT name FROM data.citynames WHERE for_player = 1 ORDER BY random() LIMIT 1")[0][0]
		self.owner = owner
		self._inhabitants = 0
		self.buildings = [] # List of all the buildings belonging to the settlement
		self.inventory = Storage()
		self.inventory.addChangeListener(self._changed)
		resources = game.main.db("SELECT rowid FROM data.resource")
		for (res,) in resources:
			self.inventory.addSlot(res, 30)
		self.inventory.alter_inventory(6, 20)
		self.inventory.alter_inventory(5, 20)
		self.inventory.alter_inventory(4, 20)

	def get_building(self, x, y):
		"""Returns the building at the position (x,y)
		@param x: int x coordinate
		@param y: int y coordinate
		@returns: Building class instance or None if none is found.
		"""
		for b in self.buildings:
			if b.x <= x < b.x + b.__class__.size[0] and b.y <= y < b.y + b.__class__.size[1]:
				return b
		else:
			return None

	def add_inhabitants(self, num):
		self._inhabitants += num

	def rem_inhabitants(self, num):
		self._inhabitants -= num
