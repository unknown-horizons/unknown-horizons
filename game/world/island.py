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

class Island(object):
	"""The Island class represents an Island by keeping a list of all instances on the map,
	that belong to the island. The island variable is also set on every instance that belongs
	to an island, making it easy to determine to which island the instance belongs, when
	selected.
	An Island instance is created at map creation, when all tiles are added to the map.
	"""

	def __init__(self, x, y, file):
		self.file = file
		self.x, self.y = x, y
		game.main.db("attach ? as island", file)
		self.width, self.height = game.main.db("select (1 + max(x) - min(x)), (1 + max(y) - min(y)) from island.ground")[0]
		self.grounds = []
		for (rel_x, rel_y, ground_id) in game.main.db("select x, y, ground_id from island.ground"):
			self.grounds.append(game.main.game.entities.grounds[ground_id](x + rel_x, y + rel_y))
		game.main.db("detach island")

	def save(self, db = 'savegame'):
		id = game.main.db(("INSERT INTO %s.island (x, y, file) VALUES (?, ?, ?)" % db), self.x, self.y, self.file).id
