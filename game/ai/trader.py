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

import random

import game.main

from game.util import Point
from game.world.player import Player
from game.world.storageholder import StorageHolder

class Trader(Player, StorageHolder):
	"""A trader represents the free trader that travels arround the map with his trading ship(s) and
	sells resources to players and buys resources from them. This is a very simple form of AI, as it
	doesn't do any more then drive to a place on water or a branchoffice randomly and then buys and
	sells resources. A game should not have more then one free trader (it could though)
	@param id: int - player id, every Player needs a unique id, as the freetrader is a Player instance, he also does.
	@param name: Traders name, also needed for the Player class.
	@param color: util.Color instance with the traders banner color, also needed for the Player class"""

	def __init__(self, id, name, color, **kwargs):
		super(Trader, self).__init__(id=id, name=name, color=color, **kwargs)
		#print "Initing Trader..."
		self.ships = [] # Put all the traders ships in here
		self.office = None # This is used to store the branchoffice the trader is currently heading to
		assert len(game.main.session.world.water)>0, "You're doing it wrong, this is not allowed to happen."
		(x, y) = game.main.session.world.water[random.randint(0,len(game.main.session.world.water)-1)]
		self.ships.append(game.main.session.entities.units[6](x, y))
		game.main.session.scheduler.add_new_object(lambda: self.send_ship_random(self.ships[0]),self)


	def send_ship_random(self, ship):
		"""Sends a ship to a random position on the map.
		@param ship: Ship instance that is to be used"""
		#print "min:", game.main.session.world.min_x
		#print "max:", game.main.session.world.max_x
		assert len(game.main.session.world.water)>0, \
			   "You're doing it wrong, this is not allowed to happen."
		(x, y) = game.main.session.world.water[random.randint(0,len(game.main.session.world.water)-1)]
		#print "sending ship to", x,y
		ship.move(Point(x, y), lambda: self.ship_idle(ship.id))


	def send_ship_random_branch(self, ship):
		"""Sends a ship to a random branch office on the map
		@param ship: Ship instance that is to be used"""
		# maybe this kind of list should be saved somewhere, as this is pretty performance intense
		branchoffices = []
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
		for res, limit in settlement.buy_list.iteritems(): # check for resources that the settlement wants to buy
			rand = random.randint(1,4) # select a random amount to sell
			if settlement.inventory[res] >= limit:
				continue # continue if there are more resources in the inventory than the settlement wants to buy
			else:
				alter = rand if limit-settlement.inventory[res] >= rand else limit-settlement.inventory[res]
				ret = settlement.owner.inventory.alter(1, -alter*\
					int(float(game.main.db("SELECT value FROM resource WHERE rowid=?",res)[0][0])*1.5))
				if ret == 0: # check if enough money was in the inventory
					settlement.inventory.alter(res, alter)
				else: # if not, return the money taken
					settlement.owner.inventory.alter(1, alter*\
						int(float(game.main.db("SELECT value FROM resource WHERE rowid=?",res)[0][0])*1.5)-ret)
		for res, limit in settlement.sell_list.iteritems():
			rand = random.randint(0,settlement.inventory.limit-limit) # select a random amount to buy from the settlement
			if settlement.inventory[res] <= limit:
				continue # continue if there are fewer resources in the inventory than the settlement wants to sell
			else:
				alter = -rand if settlement.inventory[res]-limit >= rand else -(settlement.inventory[res]-limit)
				#print "Altering:", alter
				# Pay for bought resources
				settlement.owner.inventory.alter(1, alter*\
					int(float(game.main.db("SELECT value FROM resource WHERE rowid=?",res)[0][0])*0.9))
				settlement.inventory.alter(res, alter)
		self.office = None
		# wait 2 seconds before going on to the next island
		game.main.session.scheduler.add_new_object(lambda: self.ship_idle(id), self, 32) # wait 2 seconds before going on to the next island


	def ship_idle(self, id):
		"""Called if a ship is idle
		@param id: int with the ships key for self.ships"""
		cur_ship = None
		for ship in self.ships:
			if ship.id == id:
				cur_ship = ship
		if cur_ship is not None:
			if random.randint(0,100) < 66:
				game.main.session.scheduler.add_new_object(lambda: self.send_ship_random(ship), self) # delay one tick, to allow old movement calls to completely finish
			else:
				game.main.session.scheduler.add_new_object(lambda: self.send_ship_random_branch(ship), self)






