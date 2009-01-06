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
		self.office = None # This is used to store the branchoffice the trader is currently heading to
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


	def send_ship_random_branch(self, ship):
		"""Sends a ship to a random branch office on the map
		@param ship: Ship instance that is to be used"""
		branchoffices = [] # maybe this kind of list should be saved somewhere, as this is pretty performance intense
		for island in game.main.session.world.islands: # find all branch offices
			for settlement in island.settlements:
				for building in settlement.buildings:
					if isinstance(building,game.world.building.storages.BranchOffice):
						branchoffices.append(building)
		if len(branchoffices) == 0:
			self.send_ship_random(ship)
		else:
			if len(branchoffices) == 1: # select a branch office
				self.office = branchoffices[0]
			else:
				rand = random.randint(0,len(branchoffices)-1)
				self.office = branchoffices[rand]
			for water in game.main.session.world.water: # get a position near the branch office
				if Point(water[0],water[1]).distance(self.office.position) < 3:
					ship.move(Point(water[0],water[1]), lambda: self.reached_branch(ship.id))
					break
			else:
				self.send_ship_random(ship)

	def reached_branch(self, id):
		"""Actions that need to be taken when reaching a branch office
		@param id: ships id"""
		settlement = self.office.settlement
		for res, key in settlement.buy_list.iteritems():
			rand = random.randint(0,key)
			if settlement.inventory[res] >= key:
				continue # continue if there are more resources in the inventory then the settlement wants to buy
			else:
				settlement.inventory.alter(res, rand if key-settlement.inventory[res] >= rand else key-settlement.inventory[res])
		for res, key in settlement.sell_list.iteritems():
			rand = random.randint(0,key)
			if settlement.inventory[res] <= key:
				continue # continue if there are more resources in the inventory then the settlement wants to buy
			else:
				settlement.inventory.alter(res, -rand if settlement.inventory[res]-key >= rand else settlement.inventory[res]-key)
		game.main.session.scheduler.add_new_object(lambda: self.ship_idle(id), self, 32) # wait 2 seconds before going on to the next island

	def ship_idle(self, id):
		cur_ship = None
		for ship in self.ships:
			if ship.id == id:
				cur_ship = ship
		if cur_ship is not None:
			if random.randint(0,100) < 66:
				game.main.session.scheduler.add_new_object(lambda: self.send_ship_random(ship), self) # delay one tick, to allow old movement calls to completely finish
			else:
				game.main.session.scheduler.add_new_object(lambda: self.send_ship_random_branch(ship), self)






