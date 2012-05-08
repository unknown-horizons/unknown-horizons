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
from horizons.util.pathfinding.pather import StaticPather
from horizons.component.storagecomponent import StorageComponent


class CONDITIONS(object):
	"""
	Class that holds all available conditions.

	These are functions, that perform a certain check at one point in time.
	There is no memory, e.g. if you lose progress, conditions just aren't true any more.

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
	"""Returns whether the number of player settlements is greater than *limit*."""
	return len(_get_player_settlements(session)) > limit

@register()
def settler_level_greater(session, limit):
	"""Returns whether the highest increment reached in any player settlement is greater than *limit*."""
	return (session.world.player.settler_level > limit)

@register(periodically=True)
def player_gold_greater(session, limit):
	"""Returns whether the player has more gold than *limit*."""
	return (session.world.player.get_component(StorageComponent).inventory[RES.GOLD] > limit)

@register(periodically=True)
def player_gold_less(session, limit):
	"""Returns whether the player has less gold than *limit*."""
	return (session.world.player.get_component(StorageComponent).inventory[RES.GOLD] < limit)

@register(periodically=True)
def settlement_balance_greater(session, limit):
	"""Returns whether the balance of at least one player settlement is higher than *limit*."""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.balance > limit)

@register(periodically=True)
def player_balance_greater(session, limit):
	"""Returns whether the cumulative balance of all player settlements is higher than *limit*."""
	return (sum(settlement.balance for settlement in _get_player_settlements(session)) > limit)

@register(periodically=True)
def settlement_inhabitants_greater(session, limit):
	"""Returns whether at least one player settlement has more than *limit* inhabitants."""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.inhabitants > limit)

@register(periodically=True)
def player_inhabitants_greater(session, limit):
	"""Returns whether all player settlements combined have more than *limit* inhabitants."""
	return (sum(settlement.inhabitants for settlement in _get_player_settlements(session)) > limit)

@register()
def building_num_of_type_greater(session, building_class, limit):
	"""Returns whether any player settlement has more than *limit* buildings of type *building_class*."""
	for settlement in _get_player_settlements(session):
		if len(settlement.buildings_by_id[building_class]) > limit:
			return True
	return False

@register(periodically=True)
def player_res_stored_greater(session, resource, limit):
	"""Returns whether all player settlements combined have more than *limit*
	of *resource* in their inventories."""
	return (sum(settlement.get_component(StorageComponent).inventory[resource] for settlement in _get_player_settlements(session)) > limit)

@register(periodically=True)
def player_res_stored_less(session, resource, limit):
	"""Returns whether all player settlements combined have less than *limit*
	of *resource* in their inventories."""
	return (sum(settlement.get_component(StorageComponent).inventory[resource] for settlement in _get_player_settlements(session)) < limit)

@register(periodically=True)
def settlement_res_stored_greater(session, resource, limit):
	"""Returns whether at least one player settlement has more than *limit*
	of *resource* in its inventory."""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.get_component(StorageComponent).inventory[resource] > limit)

@register(periodically=True)
def player_total_earnings_greater(session, limit):
	"""Returns whether the player has earned more than *limit* money with
	trading in all settlements combined. Profit = sell_income - buy_expenses."""
	total_earning = 0
	for settlement in _get_player_settlements(session):
		total_earning += settlement.total_earnings
	return total_earning > limit

@register(periodically=True)
def settlement_produced_res_greater(session, resource, limit):
	"""Returns whether more than *limit* resource have been produced in any player settlement."""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.produced_res.get(resource, 0) > limit)

@register(periodically=True)
def player_produced_res_greater(session, resource, limit):
	"""Returns whether more than *limit* of the resource *resource*
	have been produced in all player settlements combined."""
	return sum(settlement.produced_res.get(resource, 0) for settlement in _get_player_settlements(session)) > limit

@register(periodically=True)
def buildings_connected_to_warehouse_gt(session, building_class, limit):
	"""Checks whether more than *limit* of *building_class* type buildings are
	connected to a warehouse or storage."""
	return (_building_connected_to_any_of(session, building_class, \
	        BUILDINGS.WAREHOUSE, BUILDINGS.STORAGE) > limit )

@register(periodically=True)
def buildings_connected_to_warehouse_lt(session, building_class, limit):
	"""Checks whether less than *limit* of *building_class* type buildings are
	connected to a warehouse or storage."""
	return (_building_connected_to_any_of(session, building_class, \
	        BUILDINGS.WAREHOUSE, BUILDINGS.STORAGE) < limit )

@register(periodically=True)
def buildings_connected_to_building_gt(session, building_class, class2, limit):
	"""Checks whether more than *limit* of *building_class* type buildings are
	connected to any building of type *class2*."""
	return (_building_connected_to_any_of(session, building_class, class2) > limit )

@register(periodically=True)
def buildings_connected_to_building_lt(session, building_class, class2, limit):
	"""Checks whether less than *limit* of *building_class* type buildings are
	connected to any building of type *class2*."""
	return (_building_connected_to_any_of(session, building_class, class2) < limit )

@register(periodically=True)
def time_passed(session, seconds):
	"""Returns whether at least *seconds* seconds have passed since the game started."""
	return (Scheduler().cur_tick >= Scheduler().get_ticks(seconds))

@register()
def var_eq(session, variable, value):
	"""Returns whether *variable* has a value equal to *value*.
	Returns False if variable was never set in the current session."""
	if not variable in _get_scenario_vars(session):
		return False
	return (_get_scenario_vars(session)[variable] == value)

@register()
def var_gt(session, variable, value):
	"""Returns whether *variable* has a value greater than *value*.
	Returns False if variable was never set in the current session."""
	if not variable in _get_scenario_vars(session):
		return False
	return (_get_scenario_vars(session)[variable] > value)

@register()
def var_lt(session, variable, value):
	"""Returns whether *variable* has a value less than *value*.
	Returns False if variable was never set in the current session."""
	if not variable in _get_scenario_vars(session):
		return False
	return (_get_scenario_vars(session)[variable] < value)

def _get_player_settlements(session):
	"""Helper generator, returns settlements of local player."""
	return session.world.player.settlements

def _get_scenario_vars(session):
	return session.scenario_eventhandler._scenario_variables

def _building_connected_to_any_of(session, building_class, *classes):
	"""Returns the exact amount of buildings of type *building_class* that are
	connected to any building of a class in the building type list *classes*.
	Counts all player settlements."""
	building_to_check = []
	check_connection = []
	for settlement in _get_player_settlements(session):
		building_to_check.extend(settlement.buildings_by_id[building_class])
		for b_class in classes:
			for building in settlement.buildings_by_id[b_class]:
				check_connection.append(building)
	found_connected = 0
	for building in building_to_check:
		for check in check_connection:
			if StaticPather.get_path_on_roads(building.island, building, check):
				found_connected += 1
				break
	return found_connected

@register(periodically=True)
def player_number_of_ships_gt(session, player_id, limit):
	"""Returns whether the number of ships owned by the player *player_id* is greater than *limit*."""
	number_of_ships = len([s for s in session.world.ships if s.owner.worldid == player_id])
	return number_of_ships > limit

@register(periodically=True)
def player_number_of_ships_lt(session, player_id, limit):
	"""Returns whether the number of ships owned by the player *player_id* is less than *limit*."""
	number_of_ships = len([s for s in session.world.ships if s.owner.worldid == player_id])
	return number_of_ships < limit

def _building_connected_to_all_of(session, building_class, *classes):
	"""Returns the exact amount of buildings of type *building_class* that are
	connected to any building of each class in *classes*. Counts all player settlements."""
	#TODO
