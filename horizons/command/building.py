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
from horizons.world.building.building import *

class Build(object):
	"""Command class that builds an object."""
	def __init__(self, building, x, y, rotation, instance = None, ship = None, tear = None, ownerless=False, island=None, settlement=None,**trash):
		"""Create the command
		@param building: building class that is to be built.
		@param x, y: int coordinates where the object is to be built.
		@param instance: preview instance, can then be reused for the final building (only singleplayer)
		@param tear: list of buildings to be teared
		@param ship: ship instance
		@param island: island worldid
		"""
		self.building_class = building.id
		self._instance = instance
		self.tear = tear or []
		self.ship = None if ship is None else ship.getId()
		self.x = int(x)
		self.y = int(y)
		self.rotation = int(rotation)
		self.ownerless = ownerless
		self.island = island.getId() if island is not None else None
		self.settlement = settlement.getId() if settlement is not None else None

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		for ident in self.tear:
			building = WorldObject.get_object_by_id(ident)
			horizons.main.session.manager.execute(Tear(building))


		if self.island is not None:
			island = WorldObject.get_object_by_id(self.island)
		else:
			island = horizons.main.session.world.get_island(self.x, self.y)
		building = horizons.main.session.entities.buildings[self.building_class](x=self.x, y=self.y,\
			rotation=self.rotation, owner=issuer if not self.ownerless else None, \
			instance=(self._instance if hasattr(self, '_instance') and issuer == horizons.main.session.world.player else None))

		island.add_building(building, issuer)
		if self.settlement is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.settlement)
		elif self.ship is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.ship)
		else:
			secondary_resource_source = island.get_settlement(Point(self.x, self.y))
		if secondary_resource_source is not None:
			for (resource, value) in building.costs.items():
				# remove from issuer, and remove remaining rest from secondary source (settlement or ship)y
				remnant = secondary_resource_source.inventory.alter(resource, issuer.inventory.alter(resource, -value))
				assert(remnant == 0)
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
		building = WorldObject.get_object_by_id(self.building)
		building.remove()
		# Note: this is weak - if there is a memleak, this del will not work...
		del building

from horizons.util.encoder import register_classes
register_classes(Build, Tear)
