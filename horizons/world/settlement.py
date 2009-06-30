# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
from storage import SizedSlotStorage
from horizons.util import WorldObject, WeakList
from tradepost import TradePost

class Settlement(TradePost, WorldObject):
	"""The Settlement class describes a settlement and stores all the necessary information
	like name, current inhabitants, lists of tiles and houses, etc belonging to the village."""
	def __init__(self, owner):
		"""
		@param owner: Player object that owns the settlement
		"""
		super(Settlement, self).__init__()
		self.name = horizons.main.db("SELECT name FROM data.citynames WHERE for_player = 1 ORDER BY random() LIMIT 1")[0][0]
		self.owner = owner
		self.buildings = WeakList() # List of all the buildings belonging to the settlement

		self.setup_storage()

	@property
	def inhabitants(self):
		"""Returns number of inhabitants (sum of inhabitants of its buildings)"""
		return sum([building.inhabitants for building in self.buildings])

	def setup_storage(self):
		self.inventory = SizedSlotStorage(0)
		self.inventory.addChangeListener(self._changed)

	def get_building(self, point):
		"""Returns the building at the position (x, y)
		@param point: position to look at
		@return: Building class instance or None if none is found.
		"""
		for b in self.buildings:
			if b.position.contains(point):
				return b
		else:
			return None

	def save(self, db, islandid):
		super(Settlement, self).save(db)

		db("INSERT INTO settlement (rowid, island, owner) VALUES(?, ?, ?)",
			self.getId(), islandid, self.owner.getId())
		db("INSERT INTO name (rowid, name) VALUES(?, ?)",
			self.getId(), self.name)
		self.inventory.save(db, self.getId())

	@classmethod
	def load(cls, db, worldid):
		self = cls.__new__(cls)

		super(Settlement, self).load(db, worldid)

		self.owner = db("SELECT owner FROM settlement WHERE rowid = ?", worldid)[0][0]
		self.owner = WorldObject.get_object_by_id(self.owner)

		self.name = db("SELECT name FROM name WHERE rowid = ?", worldid)[0][0]

		self.setup_storage()
		self.inventory.load(db, worldid)

		# load all buildings from this settlement
		# the buildings will expand the area of the settlement by adding everything,
		# that is in the radius of the building, to the settlement.
		self.buildings = WeakList()
		for building_id, building_type in \
				db("SELECT rowid, type FROM building WHERE location = ?", worldid):
			buildingclass = horizons.main.session.entities.buildings[building_type]
			buildingclass.load(db, building_id)

		return self
