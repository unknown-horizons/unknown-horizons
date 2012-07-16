# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from collections import defaultdict

import horizons.main

from horizons.entities import Entities
from horizons.command import Command
from horizons.command.uioptions import TransferResource
from horizons.util import Point
from horizons.util.worldobject import WorldObject, WorldObjectNotFound
from horizons.scenario import CONDITIONS
from horizons.constants import BUILDINGS, RES
from horizons.component.storagecomponent import StorageComponent

class Build(Command):
	"""Command class that builds an object."""
	def __init__(self, building, x, y, island, rotation=45, ship=None, ownerless=False,
	             settlement=None, tearset=None, data=None, action_set_id=None):
		"""Create the command
		@param building: building class that is to be built or the id of the building class.
		@param x, y: int coordinates where the object is to be built.
		@param ship: ship instance
		@param island: BuildingOwner instance. Might be Island or World.
		@param settlement: settlement worldid or None
		@param tearset: set of worldids of objs to tear before building
		@param data: data required for building construction
		@param action_set_id: use this particular action set, don't choose at random
		"""
		if hasattr(building, 'id'):
			self.building_class = building.id
		else:
			assert type(building) == int
			self.building_class = building
		self.ship = None if ship is None else ship.worldid
		self.x = int(x)
		self.y = int(y)
		self.rotation = int(rotation)
		self.ownerless = ownerless
		self.island = island.worldid
		self.settlement = settlement.worldid if settlement is not None else None
		self.tearset = set() if not tearset else tearset
		self.data = {} if not data else data
		self.action_set_id = action_set_id

	def __call__(self, issuer=None):
		"""Execute the command
		@param issuer: the issuer (player, owner of building) of the command
		"""
		self.log.debug("Build: building type %s at (%s,%s)", self.building_class, self.x, self.y)

		island = WorldObject.get_object_by_id(self.island)
		# slightly ugly workaround to retrieve world and session instance via pseudo-singleton
		session = island.session

		# check once agaion. needed for MP because of the execution delay.
		buildable_class = Entities.buildings[self.building_class]
		build_position = buildable_class.check_build(session, Point(self.x, self.y),
			rotation=self.rotation,
			check_settlement=issuer is not None,
			ship=WorldObject.get_object_by_id(self.ship) if self.ship is not None else None,
			issuer=issuer)

		# it's possible that the build check requires different actions now,
		# so update our data
		self.x, self.y = build_position.position.origin.to_tuple()
		self.rotation = build_position.rotation
		self.tearset = build_position.tearset

		if build_position.buildable and issuer:
			# building seems to buildable, check res too now
			res_sources = [ None if self.ship is None else WorldObject.get_object_by_id(self.ship),
			                None if self.settlement is None else WorldObject.get_object_by_id(self.settlement) ]

			(build_position.buildable, missing_res) = \
			 self.check_resources({}, buildable_class.costs, issuer, res_sources)
		if not build_position.buildable:
			self.log.debug("Build aborted. Seems like circumstances changed during EXECUTIONDELAY.")
			# TODO: maybe show message to user
			return

		# collect data before objs are torn
		# required by e.g. the mines to find out about the status of the resource deposit
		if hasattr(Entities.buildings[self.building_class], "get_prebuild_data"):
			self.data.update(
			  Entities.buildings[self.building_class].get_prebuild_data(session, Point(self.x, self.y))
			  )

		for worldid in sorted(self.tearset): # make sure iteration is the same order everywhere
			try:
				obj = WorldObject.get_object_by_id(worldid)
				Tear(obj)(issuer=None) # execute right now, not via manager
			except WorldObjectNotFound: # obj might have been removed already
				pass

		building = Entities.buildings[self.building_class](
			session=session, x=self.x, y=self.y, rotation=self.rotation,
			island=island, action_set_id=self.action_set_id, instance=None,
			owner=issuer if not self.ownerless else None,
			**self.data
		)
		building.initialize(**self.data)
		# initialize must be called immediately after the construction
		# the building is not usable before this call

		island.add_building(building, issuer)


		if self.settlement is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.settlement)
		elif self.ship is not None:
			secondary_resource_source = WorldObject.get_object_by_id(self.ship)
		elif island is not None:
			secondary_resource_source = island.get_settlement(Point(self.x, self.y))

		if issuer: # issuer is None if it's a global game command, e.g. on world setup
			for (resource, value) in building.costs.iteritems():
				# remove from issuer, and remove rest from secondary source (settlement or ship)
				first_source_remnant = issuer.get_component(StorageComponent).inventory.alter(resource, -value)
				if first_source_remnant != 0 and secondary_resource_source is not None:
					second_source_remnant = secondary_resource_source.get_component(StorageComponent).inventory.alter(resource, first_source_remnant)
					assert second_source_remnant == 0
				else: # first source must have covered everything
					assert first_source_remnant == 0

		# building is now officially built and existent
		building.start()

		# unload the remaining resources on the human player ship if we just founded a new settlement
		from horizons.world.player import HumanPlayer
		if building.id == BUILDINGS.WAREHOUSE \
		and isinstance(building.owner, HumanPlayer) \
		and horizons.main.fife.get_uh_setting("AutoUnload"):
			ship = WorldObject.get_object_by_id(self.ship)
			ship_inv = ship.get_component(StorageComponent).inventory
			settlement_inv = building.settlement.get_component(StorageComponent).inventory
			# copy the inventory first because otherwise we would modify it while iterating
			for res, amount in ship_inv.get_dump().iteritems():
				amount = min(amount, settlement_inv.get_free_space_for(res))
				# execute directly, we are already in a command
				TransferResource(amount, res, ship, building.settlement)(issuer=issuer)

		# NOTE: conditions are not MP-safe! no problem as long as there are no MP-scenarios
		session.scenario_eventhandler.schedule_check(CONDITIONS.building_num_of_type_greater)

		return building

	@staticmethod
	def check_resources(needed_res, costs, issuer, res_sources):
		"""Check if there are enough resources available to cover the costs
		@param needed_res: awkward dict from BuildingTool.preview_build, use {} everywhere else
		@param costs: building costs (as in buildingclass.costs)
		@param issuer: player that builds the building
		@param res_sources: list of objects with inventory attribute. None values are discarded.
		@return tuple(bool, missing_resource), True means buildable"""
		for resource in costs:
			needed_res[resource] = needed_res.get(resource, 0) + costs[resource]

		reserved_res = defaultdict(lambda : 0) # res needed for sth else but still present
		if hasattr(issuer.session.manager, "get_builds_in_construction"):
			# mp game, consider res still to be subtracted
			builds = issuer.session.manager.get_builds_in_construction()
			for build in builds:
				reserved_res.update( Entities.buildings[build.building_class].costs )

		for resource in needed_res:
			# check player, ship and settlement inventory
			available_res = 0
			# player
			available_res += issuer.get_component(StorageComponent).inventory[resource] if resource == RES.GOLD else 0
			# ship or settlement
			for res_source in res_sources:
				if res_source is not None:
					available_res += res_source.get_component(StorageComponent).inventory[resource]

			if (available_res - reserved_res[resource]) < needed_res[resource]:
				return (False, resource)
		return (True, None)

Command.allow_network(Build)
Command.allow_network(set)

class Tear(Command):
	"""Command class that tears an object."""
	def __init__(self, building):
		"""Create the command
		@param building: building that is to be teared.
		"""
		self.building = building.worldid

	def __call__(self, issuer):
		"""Execute the command
		@param issuer: the issuer of the command
		"""
		try:
			building = WorldObject.get_object_by_id(self.building)
		except WorldObjectNotFound:
			self.log.debug("Tear: building %s already gone, not tearing it again.", self.building)
			return # invalid command, possibly caused by mp delay
		if building is None or building.fife_instance is None:
			self.log.warning("Tear: attempting to tear down a building that shouldn't exist %s", building)
			print "Tear: attempting to tear down a building that shouldn't exist %s" % building
		else:
			self.log.debug("Tear: tearing down %s", building)
			building.remove()

Command.allow_network(Tear)
