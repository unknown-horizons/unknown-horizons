# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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


from horizons.world.providerhandler import ProviderHandler
from horizons.util import decorators


"""
Simple building management functionality.
Inherited mainly by Island, but also by World for buildings at sea such as fish.
Island adds more functionality to these functions (e.g. settlement handling),
this implementation can be viewed as the the common denominator of building handling
required by World and Island.
The instances need to provide a get_tile function.
"""
class BuildingOwner(object):
	def __init__(self, *args, **kwargs):
		super(BuildingOwner, self).__init__(*args, **kwargs)
		self.provider_buildings = ProviderHandler()
		self.buildings = []

	def add_building(self, building, player):
		"""Adds a building to the island at the position x, y with player as the owner.
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement"""
		# Set all tiles in the buildings position(rect)
		for point in building.position:
			tile = self.get_tile(point)
			tile.blocked = True # Set tile blocked
			tile.object = building # Set tile's object to the building
			if hasattr(self, "path_nodes"):
				self.path_nodes.reset_tile_walkability(point.to_tuple())
		self.buildings.append(building)
		building.init()
		return building

	def remove_building(self, building):
		assert building.island == self

		# Reset the tiles this building was covering
		for point in building.position:
			tile = self.get_tile(point)
			tile.blocked = False
			tile.object = None
			self.path_nodes.reset_tile_walkability(point.to_tuple())

		# Remove this building from the buildings list
		self.buildings.remove(building)
		assert building not in self.buildings


	@decorators.make_constants()
	def get_providers_in_range(self, circle, res=None, reslist=None, player=None):
		"""Returns all instances of provider within the specified circle.
		NOTE: Specifing the res parameter is usually a huge speed gain.
		@param circle: instance of Circle
		@param res: optional; only return providers that provide res.  conflicts with reslist
		@param reslist: optionally; list of res to search providers for. conflicts with res
		@param player: Player instance, only buildings belonging to this player
		@return: list of providers"""
		assert not (bool(res) and bool(reslist))
		if res is not None:
			provider_list = self.provider_buildings.provider_by_resources[res]
		elif reslist:
			provider_list = set()
			for _res in reslist:
				provider_list = provider_list.union(self.provider_buildings.provider_by_resources[_res])
		else:
			# worst case: search all provider buildings
			provider_list = self.provider_buildings
		possible_providers = []
		for provider in provider_list:
			if (player is None or player == provider.owner) and \
				 provider.position.distance_to_circle(circle) == 0:
				possible_providers.append(provider)
		return possible_providers

	def save(self, db):
		for building in self.buildings:
			building.save(db)



