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

from horizons.constants import RES
from horizons.constants import BUILDINGS
from horizons.scheduler import Scheduler
from horizons.util import Registry
from horizons.world.pathfinding.pather import StaticPather
from horizons.world.component.storagecomponent import StorageComponent


class CONDITIONS(object):
	"""
	Class that holds all available conditions.

	Condition checking is split up in 2 types:

	  1. possible condition change is notified somewhere in the game code
	  2. condition is checked periodically
	"""
	__metaclass__ = Registry

	check_periodically = []

	@classmethod
	def register_function(cls, func, periodically=False):
		"""Register condition.

		`periodically` means that this condition function will be called periodically
		by the ScenarioEventHandler.
		"""
		name = func.__name__
		cls.registry[name] = func
		# allow CONDITIONS.example_condition_name to work, used as identifier to notify
		# about condition change (see 1)
		setattr(cls, name, name)

		if periodically:
			cls.check_periodically.append(name)


register = CONDITIONS.register


@register()
def settlements_num_greater(session, limit):
	"""Returns whether the number of settlements owned by the human player is greater than limit."""
	return len(_get_player_settlements(session)) > limit

@register()
def settler_level_greater(session, limit):
	"""Returns wheter the max level of settlers is greater than limit"""
	return (session.world.player.settler_level > limit)

@register(periodically=True)
def player_gold_greater(session, limit):
	"""Returns whether the player has more gold then limit"""
	return (session.world.player.get_component(StorageComponent).inventory[RES.GOLD_ID] > limit)

@register(periodically=True)
def player_gold_less(session, limit):
	"""Returns whether the player has less gold then limit"""
	return (session.world.player.get_component(StorageComponent).inventory[RES.GOLD_ID] < limit)

@register(periodically=True)
def settlement_balance_greater(session, limit):
	"""Returns whether at least one settlement of player has a balance > limit"""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.balance > limit)

@register(periodically=True)
def player_balance_greater(session, limit):
	"""Returns whether the cumulative balance of all player settlements is > limit"""
	return (sum(settlement.balance for settlement in _get_player_settlements(session)) > limit)

@register(periodically=True)
def settlement_inhabitants_greater(session, limit):
	"""Returns whether at least one settlement of player has more than limit inhabitants"""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.inhabitants > limit)

@register(periodically=True)
def player_inhabitants_greater(session, limit):
	"""Returns whether all settlements of player combined have more than limit inhabitants"""
	return (sum(settlement.inhabitants for settlement in _get_player_settlements(session)) > limit)

@register()
def building_num_of_type_greater(session, building_class, limit):
	"""Check if player has more than limit buildings on a settlement"""
	for settlement in _get_player_settlements(session):
		if len([building for building in settlement.buildings if \
		       building.id == building_class]) > limit:
			return True
	return False

@register(periodically=True)
def player_res_stored_greater(session, res, limit):
	"""Returns whether all settlements of player combined have more than limit of res"""
	return (sum(settlement.get_component(StorageComponent).inventory[res] for settlement in _get_player_settlements(session)) > limit)

@register(periodically=True)
def player_res_stored_less(session, res, limit):
	"""Returns whether all settlements of player combined have less than limit of res"""
	return (sum(settlement.get_component(StorageComponent).inventory[res] for settlement in _get_player_settlements(session)) < limit)

@register(periodically=True)
def settlement_res_stored_greater(session, res, limit):
	"""Returs whether at least one settlement of player has more than limit of res"""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.get_component(StorageComponent).inventory[res] > limit)

@register(periodically=True)
def player_total_earnings_greater(session, total):
	"""Returns whether the player has earned more then 'total' money with trading
	earning = sell_income - buy_expenses"""
	total_earning = 0
	for settlement in _get_player_settlements(session):
		total_earning += settlement.total_earnings
	return total_earning > total

@register(periodically=True)
def settlement_produced_res_greater(session, res, limit):
	"""Returns whether more than limit res have been produced at one of the player's settlements"""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.produced_res.get(res, 0) > limit)

@register(periodically=True)
def player_produced_res_greater(session, res, limit):
	"""Returns whether more than limit res have been produced at all of the player's settlements combined"""
	return sum(settlement.produced_res.get(res, 0) for settlement in _get_player_settlements(session)) > limit

@register(periodically=True)
def buildings_connected_to_warehouse_gt(session, building_class, number):
	"""Checks whether more than number of building_class type buildings are
	connected to a warehouse or storage."""
	return (_building_connected_to_any_of(session, building_class, \
	        BUILDINGS.WAREHOUSE_CLASS, BUILDINGS.STORAGE_CLASS) > number )

@register(periodically=True)
def buildings_connected_to_warehouse_lt(session, building_class, number):
	"""Checks whether less than number of building_class type buildings are
	connected to a warehouse or storage."""
	return (_building_connected_to_any_of(session, building_class, \
	        BUILDINGS.WAREHOUSE_CLASS, BUILDINGS.STORAGE_CLASS) < number )

@register(periodically=True)
def buildings_connected_to_building_gt(session, building_class, class2, number):
	"""Checks whether more than number of building_class type buildings are
	connected to any building of type class2."""
	return (_building_connected_to_any_of(session, building_class, class2) > number )

@register(periodically=True)
def buildings_connected_to_building_lt(session, building_class, class2, number):
	"""Checks whether less than number of building_class type buildings are
	connected to any building of type class2."""
	return (_building_connected_to_any_of(session, building_class, class2) < number )

@register(periodically=True)
def time_passed(session, secs):
	"""Returns whether at least secs seconds have passed since start."""
	return (Scheduler().cur_tick >= Scheduler().get_ticks(secs))

@register()
def var_eq(session, name, value):
	if not name in _get_scenario_vars(session):
		return False
	return (_get_scenario_vars(session)[name] == value)

@register()
def var_gt(session, name, value):
	"""Variable greater than..."""
	if not name in _get_scenario_vars(session):
		return False
	return (_get_scenario_vars(session)[name] > value)

@register()
def var_lt(session, name, value):
	"""Variable less than..."""
	if not name in _get_scenario_vars(session):
		return False
	return (_get_scenario_vars(session)[name] < value)

def _get_player_settlements(session):
	"""Helper generator, returns settlements of local player"""
	return session.world.player.settlements

def _get_scenario_vars(session):
	return session.scenario_eventhandler._scenario_variables

@register()
def _building_connected_to_any_of(session, building_class, *classes):
	"""Returns the exact amount of buildings of type building_class that are
	connected to any building of a class in classes. Counts all settlements."""
	building_to_check = []
	check_connection = []
	for settlement in _get_player_settlements(session):
		for building in settlement.buildings:
			if building.id == building_class:
				building_to_check.append(building)
			else:
				for b_class in classes:
					if building.id == b_class:
						check_connection.append(building)
						break
	found_connected = 0
	for building in building_to_check:
		for check in check_connection:
			if StaticPather.get_path_on_roads(building.island, building, check):
				found_connected += 1
				break
	return found_connected

@register(periodically=True)
def player_number_of_ships_gt(session, player_id, number):
	number_of_ships = len([s for s in session.world.ships if s.owner.worldid == player_id])
	return number_of_ships > number

@register(periodically=True)
def player_number_of_ships_lt(session, player_id, number):
	number_of_ships = len([s for s in session.world.ships if s.owner.worldid == player_id])
	return number_of_ships < number

@register()
def _building_connected_to_all_of(session, building_class, *classes):
	"""Returns the exact amount of buildings of type building_class that are
	connected to any building of each class in classes. Counts all settlements."""
	#TODO
