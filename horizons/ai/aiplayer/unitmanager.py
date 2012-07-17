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

import collections
import logging
import weakref
from math import sqrt
from operator import itemgetter
from horizons.ai.aiplayer.fleet import Fleet
from horizons.component.healthcomponent import HealthComponent
from horizons.component.selectablecomponent import SelectableComponent
from horizons.util.shapes.point import Point
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip
from horizons.world.units.pirateship import PirateShip


class UnitManager(object):
	"""
	UnitManager objects is responsible for handling units in game.
	1.Grouping combat ships into easy to handle fleets,
	2.Ship filtering.
	3.Distributing ships for missions when requested by other managers.
	"""

	log = logging.getLogger("ai.aiplayer.unitmanager")

	def __init__(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.ship_groups = []

		# quickly get fleet assigned to given ship. Ship -> Fleet dictionary
		self.ships = weakref.WeakKeyDictionary()

		# fleets
		self.fleets = set()

		self.filtering_rules = collections.namedtuple('FilteringRules', 'not_owned, hostile, ship_type, selectable,'
			'ship_state, not_in_fleet')(not_owned=self._not_owned_rule, hostile=self._hostile_rule,
			ship_type=self._ship_type_rule, selectable=self._selectable_rule, ship_state=self._ship_state_rule,
			not_in_fleet=self._ship_not_in_fleet)

	def get_fighting_ships(self, filtering_rules=None):
		ships = [ship for ship in self.owner.ships if isinstance(ship, FightingShip)]
		if filtering_rules:
			ships = self.filter_ships(self.owner, ships, filtering_rules)
		return ships

	def get_missions_in_combat(self):
		return [mission for mission in self.owner.strategy_manager.missions if mission.combat_phase]

	# TODO: depreciated
	def get_available_ship_groups(self, purpose):
		# TODO: should check out if ship group is on a mission first (priority)
		# purpose dict should contain all required info (request priority, amount of ships etc.)
		return self.ship_groups

	def create_fleet(self, ships):
		fleet = Fleet(ships)
		for ship in ships:
			self.ships[ship] = fleet
		self.fleets.add(fleet)
		return fleet

	def destroy_fleet(self, fleet):
		for ship in fleet.get_ships():
			del self.ships[ship]
		self.fleets.remove(fleet)

	def check_for_dead_fleets(self):
		pass
		#for fleet in self.fleets:
		#	if fleet.size() == 0:
		#		self.destroy_fleet(fleet)

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

	def _ship_state_rule(self, ship_states):
		"""
		Rule stating that ship has to be in any of given states.
		"""
		if not isinstance(ship_states, collections.Iterable):
			ship_states = (ship_states,)
		return lambda player, ship: (ship.owner.ships[ship] in ship_states)

	def _ship_not_in_fleet(self):
		"""
		Rule stating that ship is not assigned to any of the fleets.
		"""
		return lambda player, ship: (ship not in self.ships)

	def _selectable_rule(self):
		"""
		Rule stating that ship has to be selectable.
		"""
		return lambda player, ship: ship.has_component(SelectableComponent)

	def filter_ships(self, player, ships, rules):
		"""
		This method allows for flexible ship filtering.
		usage:
		other_ships = unit_manager.filter_ships(self.owner, other_ships, [_not_owned_rule(), _ship_type_rule([PirateShip])])

		Note that player is Player instance requesting for filtering, while ships is an iterable of ships.
		"""
		if not isinstance(rules, collections.Iterable):
			rules = (rules,)
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
	def calculate_power_balance(cls, ship_group, enemy_ship_group):
		"""
		Calculate power balance between two groups of ships.
		"""

		# dps_multiplier - 4vs2 ships equal 2 times more DPS. Multiply that factor when calculating power balance.
		dps_multiplier = len(ship_group) / float(len(enemy_ship_group))

		self_hp = 0.0
		enemy_hp = 0.0
		for unit in ship_group:
			self_hp += unit.get_component(HealthComponent).health
		for unit in enemy_ship_group:
			enemy_hp += unit.get_component(HealthComponent).health
		return (self_hp / enemy_hp) * dps_multiplier

	@classmethod
	def calculate_ship_dispersion(cls, ship_group):
		"""
		There are many solutions to solve the problem of caculating ship_group dispersion efficiently.
		We generally care about computing that in linear time, rather than having accurate numbers in O(n^2).
		We settle for a diagonal of a bounding box for the whole group.
		@return: dis
		"""
		positions = [ship.position for ship in ship_group]
		bottom_left = Point(min(positions, key=lambda position: position.x).x, min(positions, key=lambda position: position.y).y)
		top_right = Point(max(positions, key=lambda position: position.x).x, max(positions, key=lambda position: position.y).y)
		diagonal = bottom_left.distance_to_point(top_right)
		return diagonal

	def find_ships_near_group(self, ship_group):
		other_ships_set = set()
		for ship in ship_group:
			nearby_ships = ship.find_nearby_ships()
			# return only other player's ships, since we want that in most cases anyway
			other_ships_set |= set(self.filter_ships(self.owner, nearby_ships, [self._not_owned_rule(), self._selectable_rule()]))
		return list(other_ships_set)

	def tick(self):
		self.check_for_dead_fleets()

	# TODO: Consider refactoring below
	# World filtering utils (non-unit related) below, maybe consider creating a separate class for that or simply put in StrategyManager
	def get_player_settlements(self, player):
		return [settlement for settlement in self.session.world.settlements if settlement.owner == player]


