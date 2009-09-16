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

from horizons.world.storageholder import StorageHolder
from storage import PositiveStorage
from horizons.util import WorldObject, Color

class Player(StorageHolder, WorldObject):
	"""Class representing a player"""

	def __init__(self, id, name, color, inventory = {}):
		"""
		@param id: unique player id
		@param name: user-chosen name
		@param color: color of player (as Color)
		@param inventory: {res: value} that are put in the players inventory
		"""
		super(Player, self).__init__()
		self.__init(id, name, color)

		for res, value in inventory.iteritems():
			self.inventory.alter(res, value)

	def __init(self, id, name, color, settlerlevel = 0):
		assert isinstance(color, Color)
		assert (isinstance(name, str) or isinstance(name, unicode)) and len(name) > 0
		self.id = id
		self.name = name
		self.color = color
		self.settler_level = settlerlevel
		assert hasattr(self.color, "id"), "Player color has to be a default color"

	def create_inventory(self):
		self.inventory = PositiveStorage()

	def save(self, db):
		super(Player, self).save(db)
		client_id = None if self is not horizons.main.session.world.player \
							else horizons.main.settings.client_id
		db("INSERT INTO player(rowid, name, color, client_id) VALUES(?, ?, ?, ?)", \
			 self.getId(), self.name, self.color.id, client_id)
		self.inventory.save(db, self.getId())

	@classmethod
	def load(cls, db, worldid):
		self = Player.__new__(Player)
		self._load(db, worldid)
		return self

	def _load(self, db, worldid):
		"""This function makes it possible to load playerdata into an already allocated
		Player instance, which is used e.g. in Trader.load"""
		super(Player, self).load(db, worldid)

		color, name = db("SELECT color, name FROM player WHERE rowid = ?", worldid)[0]
		self.__init(worldid, name, Color[color])

		self.inventory.load(db, worldid)

	def notify_unit_path_blocked(self, unit):
		"""Notify the user that a unit stopped moving
		NOTE: this is just a quick fix for a release
		      a signaling concept for such events is planned.
		"""
		pass

	def notify_settler_reached_level(self, settler):
		"""Settler calls this to notify the player
		@param settler: instance of Settler
		@return: bool, True if level is greater than the current maximum level"""
		if settler.level > self.settler_level:
			self.settler_level = settler.level
			coords = (settler.position.center().x, settler.position.center().y)
			horizons.main.session.ingame_gui.message_widget.add(coords[0], coords[1], \
			                                                    'SETTLER_LEVEL_UP',
			                                                    {'level': settler.level})
			return True
		return False


"""
class HumanPlayer(Player):
	""Class for players that physically sit in front of the machine where the game is run""
	def notify_settler_reached_level(self, settler):
		reached_new_level = super(HumanPlayer, self).notify_settler_reached_level(settler)
		if reached_new_level:
			coords = (settler.position.center().x, settler.position.center().y)
			horizons.main.session.ingame_gui.message_widget.add(coords[0], coords[1], \
			                                                    'SETTLER_LEVEL_UP',
			                                                    {'level': settler.level})
"""

