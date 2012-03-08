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


from horizons.world.providerhandler import ProviderHandler
from horizons.util import decorators, Point
from horizons.util.shapes.radiusshape import RadiusRect

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

	def add_building(self, building, player, load=False):
		"""Adds a building to the island at the position x, y with player as the owner.
		@param building: Building class instance of the building that is to be added.
		@param player: int id of the player that owns the settlement"""
		# Set all tiles in the buildings position(rect)
		for point in building.position:
			tile = self.get_tile(point)
			tile.blocked = True # Set tile blocked
			tile.object = building # Set tile's object to the building
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

		# Remove this building from the buildings list
		self.buildings.remove(building)
		assert building not in self.buildings

	def get_settlements(self, rect, player = None):
		"""Returns the list of settlements for the coordinates describing a rect.
		@param rect: Area to search for settlements
		@return: list of Settlement instances at that position."""
		settlements = set()
		for point in rect:
			try:
				if player is None or self.get_tile(point).settlement.owner == player:
					settlements.add( self.get_tile(point).settlement )
			except AttributeError:
				# some tiles don't have settlements, we don't explicitly check for them cause
				# its faster this way.
				pass
		settlements.discard(None) # None values might have been added, we don't want them
		return list(settlements)

	def get_building(self, point):
		"""Returns the building at the point
		@param point: position of the tile to look on
		@return: Building class instance or None if none is found.
		"""
		try:
			return self.get_tile(point).object
		except AttributeError:
			return None

	def get_settlement(self, point):
		"""Look for a settlement at a specific coordinate
		@return: Settlement at point, or None"""
		try:
			return self.get_tile(point).settlement
			# some tiles might be none, so we have to catch that error here
		except AttributeError:
			return None

	def get_tile(self, point):
		"""Returns the tile at Point or None"""
		assert isinstance(point, Point)
		raise NotImplementedError

	@decorators.make_constants()
	def get_providers_in_range(self, radiusrect, res=None, reslist=None, player=None):
		"""Returns all instances of provider within the specified shape.
		NOTE: Specifing the res parameter is usually a huge speed gain.
		@param radiusrect: instance of RadiusShape
		@param res: optional; only return providers that provide res.  conflicts with reslist
		@param reslist: optionally; list of res to search providers for. conflicts with res
		@param player: Player instance, only buildings belonging to this player
		@return: list of providers"""
		assert not (bool(res) and bool(reslist))
		assert isinstance(radiusrect, RadiusRect)
		# find out relevant providers
		if res is not None:
			provider_list = self.provider_buildings.provider_by_resources[res]
		elif reslist:
			provider_list = set()
			for _res in reslist:
				provider_list = provider_list.union(self.provider_buildings.provider_by_resources[_res])
		else:
			# worst case: search all provider buildings
			provider_list = self.provider_buildings
		# filter out those that aren't in range
		r2 = radiusrect.center
		radius_squared = radiusrect.radius ** 2
		for provider in provider_list:
			if (player is None or player == provider.owner):
				# inline of :
				#provider.position.distance_to_rect(radiusrect.center) <= radiusrect.radius:
				r1 = provider.position
				if ((max(r1.left - r2.right, 0, r2.left - r1.right) ** 2) + (max(r1.top - r2.bottom, 0, r2.top - r1.bottom) ** 2)) <= radius_squared:
					yield provider

	def save(self, db):
		for building in self.buildings:
			building.save(db)

	def end(self):
		if self.buildings is not None:
			# remove all buildings
			# this iteration style is the most robust; sometimes the ai reacts to removals
			# by building/tearing, effectively changing the list, therefore iterating over a
			# copy would either miss instances or remove some twice.
			while self.buildings:
				self.buildings[-1].remove()
		self.provider_buildings = None
		self.buildings = None
