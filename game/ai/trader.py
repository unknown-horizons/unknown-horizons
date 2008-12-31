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

from game.world.player import Player
from game.world.storageholder import StorageHolder
from game.util import Point
import game.main
import random
class Trader(Player, StorageHolder):

	def __init__(self, id, name, color, **kwargs):
		super(Trader, self).__init__(id=id, name=name, color=color, **kwargs)
		print "Initing Trader..."
		self.ships = [] # Put all the traders ships in here
		while True:
			x = random.randint(game.main.session.world.min_x, game.main.session.world.max_x)
			y = random.randint(game.main.session.world.min_y, game.main.session.world.max_y)
			if (x,y) in game.main.session.world.water:
				break
		self.ships.append(game.main.session.entities.units[6](x, y))
		game.main.session.scheduler.add_new_object(lambda: self.send_ship_random(self.ships[0]),self)


	def send_ship_random(self, ship):
		"""Sends a ship to a random position on the map.
		@param ship: Ship instance that is to be used"""
		print "min:", game.main.session.world.min_x
		print "max:", game.main.session.world.max_x
		while True:
			x = random.randint(game.main.session.world.min_x, game.main.session.world.max_x)
			y = random.randint(game.main.session.world.min_y, game.main.session.world.max_y)
			if (x,y) in game.main.session.world.water:
				break
		print "sending ship to", x,y
		ship.move(Point(x, y), lambda: self.ship_idle(ship.id))

	def ship_idle(self, id):
		cur_ship = None
		for ship in self.ships:
			if ship.id == id:
				cur_ship = ship
		if cur_ship is not None:
			game.main.session.scheduler.add_new_object(lambda: self.send_ship_random(ship), self)




