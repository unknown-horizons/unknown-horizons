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

from game.world.storage import Storage
from game.util import WorldObject, Color
import game.main

class Player(WorldObject):
	"""Class representing a player"""

	def __init__(self, id, name, color):
		"""
		@param id: unique player id
		@param name: user-chosen name
		@param color: color of player (as Color)
		"""
		self.id = id
		self.name = name
		self.color = color
		assert hasattr(self.color, "id"), "Player color has to be a default color"

		self.setup_inventory()

		self.inventory.alter_inventory(1, 9999)

	def setup_inventory(self):
		self.inventory = Storage()
		self.inventory.addSlot(1, -1)

	def save(self, db):
		"""
		@param db: db that the player is saved to.
		"""
		# Since the player isn't implemented fully by now,
		# saving and loading implementation will have to be changed
		db("INSERT INTO player(rowid, name, color, client_id) VALUES(?, ?, ?, ?)", self.getId(), self.name, self.color.id, "NULL" if self is not game.main.session.world.player else game.main.settings.client_id)
		self.inventory.save(db, self.getId())

	@classmethod
	def load(cls, db, worldid):
		self = Player.__new__(Player)
		super(Player, self).load(db, worldid)

		color, self.name = db("SELECT color, name FROM player WHERE rowid = ?", worldid)[0]
		self.color = Color[color]
		assert hasattr(self.color, "id"), "Player color has to be a default color"

		self.setup_inventory()
		self.inventory.load(db, worldid)
		return self


