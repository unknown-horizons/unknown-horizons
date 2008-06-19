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

class Player(object):
	"""Class representing a player"""

	def __init__(self, id, name):
		"""
		@param id: unique player id
		@param name: str containing the players name
		"""
		self.id = id
		self.name = name
		self.inventory = Storage()

		self.inventory.alter_inventory(1, 9999)

	def save(self, db = 'savegame'):
		game.main.db(("INSERT INTO %s.player (rowid, name) VALUES (?, ?, ?)" % db), self.id, self.name)
