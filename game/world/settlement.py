# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
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
import game.main
from game.world.storage import SizedSlotStorage
from game.util import WorldObject, Point, WeakList
from game.world.tradepost import TradePost

class Settlement(TradePost, WorldObject):
	"""The Settlement class describes a settlement and stores all the necessary information
	like name, current inhabitants, lists of tiles and houses, etc belonging to the village."""
	def __init__(self, owner):
		"""
		@param owner: Player object that owns the settlement
		"""
		super(Settlement, self).__init__()
		self.name = game.main.db("SELECT name FROM data.citynames WHERE for_player = 1 ORDER BY random() LIMIT 1")[0][0]
		self.owner = owner
		self._inhabitants = 0
		self.buildings = WeakList() # List of all the buildings belonging to the settlement

		self.setup_storage()

	def setup_storage(self):
		self.inventory = SizedSlotStorage(0)
		self.inventory.addChangeListener(self._changed)

	def get_building(self, point):
		"""Returns the building at the position (x,y)
		@param point: position to look at
		@return: Building class instance or None if none is found.
		"""
		for b in self.buildings:
			if b.position.contains(point):
				return b
		else:
			return None

	def add_inhabitants(self, num):
		self._inhabitants += num

	def rem_inhabitants(self, num):
		self._inhabitants -= num

	def save(self, db, islandid):
		super(Settlement, self).save(db)

		db("INSERT INTO settlement (rowid, island, owner, inhabitants) VALUES(?, ?, ?, ?)",
			self.getId(), islandid, self.owner.getId(), self._inhabitants)
		db("INSERT INTO name (rowid, name) VALUES(?, ?)",
			self.getId(), self.name)
		self.inventory.save(db, self.getId())

		# TODO:
		# Tiles

	@classmethod
	def load(cls, db, worldid):
		self = cls.__new__(cls)

		super(Settlement, self).load(db, worldid)

		self.owner = db("SELECT owner FROM settlement WHERE rowid = ?", worldid)[0][0]
		self.owner = WorldObject.getObjectById(self.owner)

		self._inhabitants = int(db("SELECT inhabitants FROM settlement WHERE rowid = ?", worldid)[0][0])
		self.name = db("SELECT name FROM name WHERE rowid = ?", worldid)[0][0]

		self.setup_storage()
		self.inventory.load(db, worldid)

		self.buildings = WeakList()
		for building_id, building_type in \
				db("SELECT rowid, type FROM building WHERE location = ?", worldid):
			buildingclass = game.main.session.entities.buildings[building_type]
			building = buildingclass.load(db, building_id)

		return self

