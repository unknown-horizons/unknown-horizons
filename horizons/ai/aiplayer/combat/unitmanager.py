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
from operator import itemgetter
from horizons.ai.aiplayer.combat.fleet import Fleet
from horizons.component.healthcomponent import HealthComponent
from horizons.component.selectablecomponent import SelectableComponent
from horizons.util.shapes.circle import Circle
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
		super(UnitManager, self).__init__()
		self.__init(owner)

	def __init(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session

		# quickly get fleet assigned to given ship. Ship -> Fleet dictionary
		self.ships = weakref.WeakKeyDictionary()

		# fleets
		self.fleets = set()

		self.filtering_rules = collections.namedtuple('FilteringRules', 'not_owned, hostile, ship_type, selectable,'
			'ship_state, not_in_fleet, working, pirate, fighting')(not_owned=self._not_owned_rule, hostile=self._hostile_rule,
			ship_type=self._ship_type_rule, selectable=self._selectable_rule, ship_state=self._ship_state_rule,
			not_in_fleet=self._ship_not_in_fleet, working=self._is_worker, pirate=self._is_pirate, fighting=self._is_fighter)

	def get_ships(self, filtering_rules=None):
		ships = [ship for ship in self.owner.ships]
		if filtering_rules:
			ships = self.filter_ships(ships, filtering_rules)
		return ships

	def remove_unit(self, ship):
		if ship in self.ships:
			del self.ships[ship]

	def save(self, db):
		for fleet in list(self.fleets):
			fleet.save(db)

	def _load(self, db, owner):
		self.__init(owner)
		fleets_id = db("SELECT fleet_id from fleet where owner_id = ?", self.owner.worldid)
		for (fleet_id,) in fleets_id:
			fleet = Fleet.load(fleet_id, owner, db)
			self.fleets.add(fleet)
			for ship in fleet.get_ships():
				self.ships[ship] = fleet

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls)
		self._load(db, owner)
		return self

	def create_fleet(self, ships, destroy_callback=None):
		fleet = Fleet(ships, destroy_callback)
		for ship in ships:
			self.ships[ship] = fleet
		self.fleets.add(fleet)
		return fleet

	def destroy_fleet(self, fleet):
		for ship in fleet.get_ships():
			if ship in self.ships:
				del self.ships[ship]
		if fleet in self.fleets:
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
	# we have ships = filter_ships(other_ships, [get_hostile_rule(), get_ship_type_rule((PirateShip,)), ... ])
	def _is_fighter(self):
		"""
		Rule stating that ship is a fighting ship, but not a pirate ship.
		"""
		return lambda ship: isinstance(ship, FightingShip) and not isinstance(ship, PirateShip)

	def _is_pirate(self):
		return lambda ship: isinstance(ship, PirateShip)

	def _is_worker(self):
		return lambda ship: ship.name == "Huker"

	def _ship_type_rule(self, ship_types):
		"""
		Rule stating that ship is any of ship_types instances
		"""
		return lambda ship: isinstance(ship, ship_types)

	def _not_owned_rule(self):
		"""
		Rule stating that ship is another player's ship
		"""
		return lambda ship: self.owner != ship.owner

	def _hostile_rule(self):
		"""
		Rule selecting only hostile ships
		"""
		return lambda ship: self.session.world.diplomacy.are_enemies(self.owner, ship.owner)

	def _ship_state_rule(self, state_dict, ship_states):
		"""
		Rule stating that ship has to be in any of given states.
		"""
		if not isinstance(ship_states, collections.Iterable):
			ship_states = (ship_states,)
		return lambda ship: (state_dict[ship] in ship_states)

	def _ship_not_in_fleet(self):
		"""
		Rule stating that ship is not assigned to any of the fleets.
		"""
		return lambda ship: (ship not in self.ships)

	def _selectable_rule(self):
		"""
		Rule stating that ship has to be selectable.
		"""
		return lambda ship: ship.has_component(SelectableComponent)

	def filter_ships(self, ships, rules):
		"""
		This method allows for flexible ship filtering.
		usage:
		other_ships = unit_manager.filter_ships(other_ships, [_not_owned_rule(), _ship_type_rule([PirateShip])])

		@param ships: iterable of ships to filter
		@type ships: iterable
		@param rules: conditions each ship has to meet (AND)
		@type rules: iterable of lambda(ship) or single lambda(ship)
		"""
		if not isinstance(rules, collections.Iterable):
			rules = (rules,)
		return [ship for ship in ships if all((rule(ship) for rule in rules))]

	@classmethod
	def get_lowest_hp_ship(cls, ship_group):
		return min(ship_group, key=lambda ship: ship.get_component(HealthComponent).health)

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
	def get_best_targets_for_each(cls, ship_group, enemies):
		"""
		For each ship in ship_group return an index of ship from enemies that is the closest to given ship.
		For example ship_group=[A, B, C] , enemies = [X, Y, Z],
		could return [(A,X), (B,Y), (C,Y)] if X was the closest to A and Y was the closest ship to both B and C
		"""
		pass

	@classmethod
	def calculate_power_balance(cls, ship_group, enemy_ship_group):
		"""
		Calculate power balance between two groups of ships.

		@param ship_group: iterable of ships to be counted as a numerator
		@type ship_group: Iterable
		@param enemy_ship_group: iterable of ships to be counted as denominator
		@type enemy_ship_group: Iterable
		@return: power balance between two ship groups
		@rtype: float
		"""

		assert len(ship_group), "Request to calculate balance with 0 ships in ship_group"
		assert len(enemy_ship_group), "Request to calculate balance with 0 ships in enemy_ship_group"

		# dps_multiplier - 4vs2 ships equal 2 times more DPS. Multiply that factor when calculating power balance.
		dps_multiplier = len(ship_group) / float(len(enemy_ship_group))

		self_hp = float(sum((ship.get_component(HealthComponent).health for ship in ship_group)))
		enemy_hp = float(sum((ship.get_component(HealthComponent).health for ship in enemy_ship_group)))

		return (self_hp / enemy_hp) * dps_multiplier

	@classmethod
	def calculate_ship_dispersion(cls, ship_group):
		"""
		There are many solutions to solve the problem of caculating ship_group dispersion efficiently.
		We generally care about computing that in linear time, rather than having accurate numbers in O(n^2).
		We settle for a diagonal of a bounding box for the whole group.
		@return: dispersion factor
		@rtype: float
		"""
		positions = [ship.position for ship in ship_group]
		bottom_left = Point(min(positions, key=lambda position: position.x).x, min(positions, key=lambda position: position.y).y)
		top_right = Point(max(positions, key=lambda position: position.x).x, max(positions, key=lambda position: position.y).y)
		diagonal = bottom_left.distance_to_point(top_right)
		return diagonal

	def find_ships_near_group(self, ship_group, radius):
		other_ships_set = set()
		for ship in ship_group:
			nearby_ships = ship.find_nearby_ships(radius)
			# return only other player's ships, since we want that in most cases anyway
			other_ships_set |= set(self.filter_ships(nearby_ships, [self._not_owned_rule(), self._selectable_rule()]))
		return list(other_ships_set)

	def tick(self):
		self.check_for_dead_fleets()

	def get_player_islands(self, player):
		return [settlement.island for settlement in self.session.world.settlements if settlement.owner == player]

	def get_player_ships(self, player):
		return [ship for ship in self.session.world.ships if ship.owner == player and ship.has_component(SelectableComponent)]

	def get_warehouse_point(self, settlement):
		"""
		Return point of given settlement's warehouse.
		Be careful with sailing directly to given warehouse
		"""
		target_point = settlement.warehouse.position
		(x, y) = target_point.get_coordinates()[4]
		return Point(x, y)

	def get_warehouse_area(self, settlement, range=10):
		return Circle(self.get_warehouse_point(settlement), range)
