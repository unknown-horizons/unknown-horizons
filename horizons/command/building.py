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
from horizons.constants import RES

class Build(Command):
	"""Command class that builds an object."""
	log = logging.getLogger("command")
	def __init__(self, building, x, y, island, rotation = 45, \
	             ship = None, ownerless=False, settlement=None,**trash):
		"""Create the command
		@param building: building class that is to be built or the id of the building class.
		@param x, y: int coordinates where the object is to be built.
		@param ship: ship instance
		@param island: island instance
		@param settlement: settlement worldid or None
		"""
		if hasattr(building, 'id'):
			self.building_class = building.id
		else:
			assert type(building) == int
			self.building_class = building
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

		island = WorldObject.get_object_by_id(self.island)
		session = island.session

		# check once agaion. needed for MP.
		buildable_class = Entities.buildings[self.building_class]
		buildable = buildable_class.check_build(session, Point(self.x, self.y), rotation = self.rotation,\
			check_settlement=issuer is not None, \
			ship=WorldObject.get_object_by_id(self.ship) if self.ship is not None else None,
			issuer=issuer)
		if buildable.buildable and issuer: # TODO: duplicated code from buildingtool.py:216
				neededResources= {}
				# building seems to buildable, check res too now
				for resource in buildable_class.costs:
					neededResources[resource] = neededResources.get(resource, 0) + \
					               buildable_class.costs[resource]
				for resource in neededResources:
					# check player, ship and settlement inventory
					available_res = 0
					# player
					available_res += issuer.inventory[resource] if \
					              resource == RES.GOLD_ID else 0
					# ship or settlement
					if self.ship is not None:
						available_res += WorldObject.get_object_by_id(self.ship).inventory[resource]
					elif self.settlement is not None:
						available_res += WorldObject.get_object_by_id(self.settlement).inventory[resource]

					if available_res < neededResources[resource]:
						# can't build, not enough res
						buildable.buildable = False
						break
		if not buildable.buildable:
			self.log.debug("Build aborted. Seems like circumstances changed during EXECUTIONDELAY.")
			# TODO: maybe show message to user
			return

		building = Entities.buildings[self.building_class]( \
			session=session, \
			x=self.x, y=self.y, \
			rotation=self.rotation, owner=issuer if not self.ownerless else None, \
			island=island, \
			instance=None)

		island.add_building(building, issuer)
		if self.settlement is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.settlement)
		elif self.ship is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.ship)
		else:
			secondary_resource_source = island.get_settlement(Point(self.x, self.y))

		if issuer: # issuer is None if it's a global game command, e.g. on world setup
			for (resource, value) in building.costs.iteritems():
				# remove from issuer, and remove rest from secondary source (settlement or ship)
				first_source_remnant = issuer.inventory.alter(resource, -value)
				if secondary_resource_source is not None:
					second_source_remnant = secondary_resource_source.inventory.alter(resource, first_source_remnant)
					assert second_source_remnant == 0
				else: # first source must have covered everything
					assert first_source_remnant == 0

		# building is now officially built and existent
		building.start()

		# NOTE: conditions are not MP-save! no problem as long as there are no MP-campaigns
		session.campaign_eventhandler.schedule_check(CONDITIONS.building_num_of_type_greater)

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
