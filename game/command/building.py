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

from game.world.building.building import *
import game.main

class Build(object):
	"""Command class that builds an object."""
	def __init__(self, building, x, y, instance = None, ship = None, **trash):
		"""Create the command
		@param building_class: building class that is to be built.
		@param x,y: int coordinates where the object is to be built.
		@param instance: preview instance, can then be reused for the final building (only singleplayer)
		@param ship: ship instance
		"""
		self.building_class = building.id
		self.instance = None if instance == None else instance.getId()
		self.ship = None if ship == None else game.main.session.world.ships.index(ship)
		self.x = int(x)
		self.y = int(y)

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		island = game.main.session.world.get_island(self.x, self.y)
		building = game.main.session.entities.buildings[self.building_class](self.x, self.y, issuer, game.main.session.view.layers[1].getInstance(self.instance) if self.instance != None and issuer == game.main.session.world.player else None)

		island.add_building(self.x, self.y, building, issuer)
		secondary_ressource_source = island.get_settlements(self.x, self.y).pop() if self.ship == None else game.main.session.world.ships[self.ship]
		for (ressource, value) in building.costs.items():
			# remove from issuer, and remove remaining rest from secondary source (settlement or ship)
			assert(secondary_ressource_source.inventory.alter_inventory(ressource, issuer.inventory.alter_inventory(ressource, -value)) == 0)

class Tear(object):
	"""Command class that tears an object."""
	def __init__(self, building):
		"""Create the command
		@param building: building that is to be teared.
		"""
		for id, i in game.main.session.world.islands.iteritems():
			if i == building.island:
				self.island_id = id
				break
		if hasattr(building, 'settlement'):
			for id, s in building.island.settlements.iteritems():
				if s == building.settlement:
					self.settlement_id = id
					break
		else:
			self.settlement_id = None
		for id, b in (building.island if self.settlement_id == None else building.settlement).buildings.iteritems():
			if b == building:
				self.building_id = id
				break

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		(game.main.session.world.islands[self.island_id] if self.settlement_id == None else game.main.session.world.islands[self.island_id].settlements[self.settlement_id]).buildings[self.building_id].remove()

