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
	def __init__(self, building, x, y, instance = None, ship = None, tear = [], **trash):
		"""Create the command
		@param building: building class that is to be built.
		@param x,y: int coordinates where the object is to be built.
		@param instance: preview instance, can then be reused for the final building (only singleplayer)
		@param tear: list of buildings to be teared
		@param ship: ship instance
		"""
		self.building_class = building.id
		self.instance = None if instance is None else instance.getId()
		self.layer = 2 if instance is None else int(instance.getLocationRef().getLayer().getId())
		self.tear = []
		for obj in tear:
			self.tear.append(obj.getId())
		self.ship = None if ship is None else ship.getId()
		self.x = int(x)
		self.y = int(y)

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		for id in self.tear:
			WorldObject.getObjectById(id).remove()

		island = game.main.session.world.get_island(self.x, self.y)
		building = game.main.session.entities.buildings[self.building_class](x=self.x, y=self.y, owner=issuer, instance=game.main.session.view.layers[self.layer].getInstance(self.instance) if self.instance is not None and issuer == game.main.session.world.player else None)

		island.add_building(self.x, self.y, building, issuer)
		secondary_resource_source = island.get_settlements(self.x, self.y).pop() if self.ship is None else game.main.session.world.ships[self.ship]
		for (resource, value) in building.costs.items():
			# remove from issuer, and remove remaining rest from secondary source (settlement or ship)
			assert(secondary_resource_source.inventory.alter_inventory(resource, issuer.inventory.alter_inventory(resource, -value)) == 0)
		building.start()

class Tear(object):
	"""Command class that tears an object."""
	def __init__(self, building):
		"""Create the command
		@param building: building that is to be teared.
		"""
		self.building = building.getId()

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		WorldObject.getObjectById(self.building).remove()
