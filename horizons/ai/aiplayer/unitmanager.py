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

import logging, collections
from operator import itemgetter
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip
from horizons.world.units.ship import PirateShip


class UnitManager(WorldObject):
	"""
	UnitManager objects is responsible for handling units in game.
	1.Grouping combat ships into easy to handle fleets,
	2.Ship filtering.
	3.Distributing ships for missions when requested by other managers.
	"""

	log = logging.getLogger("ai.aiplayer.unitmanager")

	def __init__(self, owner):
		super(UnitManager, self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.ship_groups = []
		self.filtering_rules = collections.namedtuple('FilteringRules', 'not_owned, hostile, ship_type')(not_owned=self._not_owned_rule,
			hostile=self._hostile_rule, ship_type=self._ship_type_rule)

	def get_my_ships(self):
		return [ship for ship in self.world.ships if ship.owner == self.owner and isinstance(ship, FightingShip)]

	def get_available_ship_groups(self, purpose):
		# TODO: should check out if ship group is on a mission first (priority)
		# purpose dict should contain all required info (request priority, amount of ships etc.)
		return self.ship_groups

	def regroup_ships(self):
		group_size = 3  # TODO move to behaviour/Personalities later
		self.ship_groups = []
		ships = self.get_my_ships()
		for i in xrange(0, len(ships), group_size):
			self.ship_groups.append(ships[i:i + group_size])

	# Filtering rules
	# Use filter_ships method along with rules defined below:
	# This approach simplifies code (does not aim to make it shorter)
	# Instead having [ship for ship in ships if ... and ... and ... and ...]
	# we have ships = filter_ships(player, other_ships, [get_hostile_rule(), get_ship_type_rule((PirateShip,)), ... ])

	def _not_owned_rule(self):
		"""
		Rule stating that ship is another player's ship
		"""
		return lambda player, ship: player != ship.owner

	def _hostile_rule(self):
		"""
		Rule selecting only hostile ships
		"""
		return lambda player, ship: self.session.world.diplomacy.are_enemies(player, ship.owner)

	def _ship_type_rule(self, ship_types):
		"""
		Rule stating that ship is any of ship_types instances
		"""
		return lambda player, ship: isinstance(ship, ship_types)

	def filter_ships(self, player, ships, rules):
		"""
		This method allows for flexible ship filtering.
		usage:
		other_ships = unit_manager.filter_ships(self.owner, other_ships, [_enemy_rule(), _ship_type_rule([PirateShip])])
		"""
		return [ship for ship in ships if all([rule(player, ship) for rule in rules])]

	@classmethod
	def get_closest_ships_for_each(cls, ship_group, enemies):
		"""
		For each ship in ship_group return an index of ship from enemies that is the closest to given ship.
		For example ship_group=[A, B, C] , enemies = [X, Y, Z],
		could return [(A,X), (B,Y), (C,Y)] if X was the closest to A and Y was the closest ship to both B and C
		"""
		# TODO: make faster than o(n^2)
		closest = []
		for ship in ship_group:
			distances = ((e, ship.position.distance(e.position)) for e in enemies)
			closest.append((ship, min(distances, key=itemgetter(1))[0]))
		return closest

	@classmethod
	def calculate_power_balance(cls, ship_group, enemies):
		"""
		Calculate power balance between two ship groups.
		"""
		return 1.2 # TODO: implement power balance calculation

	def find_ships_near_group(self, ship_group):
		other_ships_set = set()
		for ship in ship_group:
			nearby_ships = ship.find_nearby_ships()
			# return only other player's ships, since we want that in most cases anyway
			other_ships_set |= set(self.filter_ships(self.owner, nearby_ships, [self._not_owned_rule()]))
		return list(other_ships_set)

	def tick(self):
		self.regroup_ships()  # TODO will be called on shipstate change (sank/built)

	def save(self, db):
		pass

	def _load(self, db, player):
		pass

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls, owner)
		#self._load(db, player)
		return self

