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

import logging

import horizons.main
from horizons.entities import Entities
from horizons.command import Command
from horizons.util import Point, WorldObject
from horizons.campaign import CONDITIONS

class Build(Command):
	"""Command class that builds an object."""
	log = logging.getLogger("command")
	def __init__(self, session, building, x, y, rotation = 45, instance = None, ship = None, tear = None, ownerless=False, island=None, settlement=None,**trash):
		"""Create the command
		@param session: Session instance (not MP-able!)
		@param building: building class that is to be built or the id of the building class.
		@param x, y: int coordinates where the object is to be built.
		@param instance: preview instance, can then be reused for the final building (only singleplayer)
		@param tear: list of buildings to be teared
		@param ship: ship instance
		@param island: island instance
		@param settlement: settlement worldid or None
		"""
		if hasattr(building, 'id'):
			self.building_class = building.id
		else:
			assert type(building) == int
			self.building_class = building
		self.session = session
		self._instance = instance
		self.tear = tear or []
		self.ship = None if ship is None else ship.getId()
		self.x = int(x)
		self.y = int(y)
		self.rotation = int(rotation)
		self.ownerless = ownerless
		self.island = island.getId()
		self.settlement = settlement.getId() if settlement is not None else None

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer (player, owner of building) of the command
		"""
		self.log.debug("Build: building type %s at (%s,%s)", self.building_class, \
									 self.x, self.y)
		for ident in self.tear:
			building = WorldObject.get_object_by_id(ident)
			Tear(building).execute(self.session)

		island = WorldObject.get_object_by_id(self.island)

		building = Entities.buildings[self.building_class]( \
			session=self.session, \
			x=self.x, y=self.y, \
			rotation=self.rotation, owner=issuer if not self.ownerless else None, \
			island=island, \
			instance=(self._instance if issuer == self.session.world.player else None))

		island.add_building(building, issuer)
		if self.settlement is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.settlement)
		elif self.ship is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.ship)
		else:
			secondary_resource_source = island.get_settlement(Point(self.x, self.y))
		if secondary_resource_source is not None:
			for (resource, value) in building.costs.iteritems():
				# remove from issuer, and remove remaining rest from secondary source (settlement or ship)
				first_source_remnant = issuer.inventory.alter(resource, -value)
				second_source_remnant = secondary_resource_source.inventory.alter(resource, first_source_remnant)
				assert second_source_remnant == 0

		# building is now officially built and existent
		building.start()


		self.session.campaign_eventhandler.schedule_check(CONDITIONS.building_num_of_type_greater)

		return building

class Tear(Command):
	"""Command class that tears an object."""
	log = logging.getLogger("command")
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
		self.log.debug("Tear: tearing down %s", building)
		building.remove()

from horizons.util.encoder import register_classes
register_classes(Build, Tear)
