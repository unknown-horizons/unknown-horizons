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

import logging
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip
from horizons.world.units.ship import PirateShip


class UnitManager(WorldObject):
	"""
	UnitManager objects is responsible for handling units in game.
	1.Grouping combat ships into easy to handle fleets,
	2.Distributing ships for missions when requested by other managers.
	"""
	log = logging.getLogger("ai.aiplayer.unitmanager")

	def __init__(self, owner):
		super(UnitManager, self).__init__()
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.ship_groups = []

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

	def filter_enemy_ships(self, ships):
		# TODO: Should take diplomacy into account
		return [ship for ship in ships if ship.owner != self.owner and isinstance(ship, (FightingShip, PirateShip))]

	def find_ships_near_group(self, ship_group):
		enemy_set = set()
		for ship in ship_group:
			ships_around = ship.find_nearby_ships()
			enemy_set |= set(self.filter_enemy_ships(ships_around))
		return list(enemy_set)

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

