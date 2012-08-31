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
from horizons.ai.aiplayer.behavior import BehaviorManager
from horizons.ai.aiplayer.behavior.behaviorcomponents import BehaviorMoveCallback
from horizons.ai.aiplayer.behavior.profile import BehaviorProfileManager
from horizons.ai.aiplayer.combat.combatmanager import  PirateCombatManager
from horizons.ai.aiplayer.combat.unitmanager import UnitManager
from horizons.ai.aiplayer.strategy.strategymanager import PirateStrategyManager
from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject
from horizons.constants import UNITS
from horizons.ext.enum import Enum
from horizons.ai.generic import GenericAI
from horizons.command.unit import CreateUnit
from horizons.world.units.ship import TradeShip
from horizons.world.units.pirateship import PirateShip
from horizons.component.namedcomponent import NamedComponent
from horizons.component.selectablecomponent import SelectableComponent


class Pirate(GenericAI):
	"""A pirate ship moving randomly around. If another ship comes into the reach
	of it, it will be followed for a short time."""

	# TODO: Move on_a_mission to GenericAI
	shipStates = Enum.get_extended(GenericAI.shipStates, 'on_a_mission', 'chasing_ship', 'going_home')

	log = logging.getLogger("ai.pirate")
	regular_player = False

	caught_ship_radius = 5
	home_radius = 2

	ship_count = 1

	tick_interval = 32
	tick_long_interval = 128

	def __init__(self, session, id, name, color, **kwargs):
		super(Pirate, self).__init__(session, id, name, color, **kwargs)

		# choose a random water tile on the coast and call it home
		self.home_point = self.session.world.get_random_possible_coastal_ship_position()
		self.log.debug("Pirate: home at (%d, %d), radius %d", self.home_point.x, self.home_point.y, self.home_radius)
		self.__init()

		# create a ship and place it randomly (temporary hack)
		for i in xrange(self.ship_count):
			self.create_ship_at_random_position()

		Scheduler().add_new_object(Callback(self.tick), self, 1, -1, self.tick_interval)
		Scheduler().add_new_object(Callback(self.tick_long), self, 1, -1, self.tick_long_interval)

	def __init(self):
		self.world = self.session.world
		self.unit_manager = UnitManager(self)
		self.combat_manager = PirateCombatManager(self)
		self.strategy_manager = PirateStrategyManager(self)
		self.behavior_manager = BehaviorManager(self)

	@staticmethod
	def get_nearest_player_ship(base_ship):
		lowest_distance = None
		nearest_ship = None
		for ship in base_ship.find_nearby_ships():
			if isinstance(ship, (PirateShip, TradeShip)) or not ship.has_component(SelectableComponent):
				continue  # don't attack these ships
			distance = base_ship.position.distance_to_point(ship.position)
			if lowest_distance is None or distance < lowest_distance:
				lowest_distance = distance
				nearest_ship = ship
		return nearest_ship

	def tick(self):
		self.combat_manager.tick()

		# Temporary function for pirates respawn
		self.maintain_ship_count()

	def tick_long(self):
		self.strategy_manager.tick()

	def get_random_profile(self, token):
		return BehaviorProfileManager.get_random_pirate_profile(self, token)

	def create_ship_at_random_position(self):
		point = self.session.world.get_random_possible_ship_position()
		ship = CreateUnit(self.worldid, UNITS.PIRATE_SHIP, point.x, point.y)(issuer=self.session.world.player)
		self.ships[ship] = self.shipStates.idle
		self.combat_manager.add_new_unit(ship)

	def maintain_ship_count(self):
		if len(self.ships.keys()) < self.ship_count:
			self.create_ship_at_random_position()

	def save(self, db):
		super(Pirate, self).save(db)
		db("UPDATE player SET is_pirate = 1 WHERE rowid = ?", self.worldid)
		db("INSERT INTO pirate_home_point(x, y) VALUES(?, ?)", self.home_point.x, self.home_point.y)

		current_callback = Callback(self.tick)
		calls = Scheduler().get_classinst_calls(self, current_callback)
		assert len(calls) == 1, "got %s calls for saving %s: %s" % (len(calls), current_callback, calls)
		remaining_ticks = max(calls.values()[0], 1)

		current_callback_long = Callback(self.tick_long)
		calls = Scheduler().get_classinst_calls(self, current_callback_long)
		assert len(calls) == 1, "got %s calls for saving %s: %s" % (len(calls), current_callback_long, calls)
		remaining_ticks_long = max(calls.values()[0], 1)

		db("INSERT INTO ai_pirate(rowid, remaining_ticks, remaining_ticks_long) VALUES(?, ?, ?)", self.worldid,
			remaining_ticks, remaining_ticks_long)

		for ship in self.ships:
			ship_state = self.ships[ship]
			db("INSERT INTO pirate_ships(rowid, state) VALUES(?, ?)",
				ship.worldid, ship_state.index)

		# save unit manager
		self.unit_manager.save(db)

		# save combat manager
		self.combat_manager.save(db)

		# save strategy manager
		self.strategy_manager.save(db)

		# save behavior manager
		self.behavior_manager.save(db)

	def _load(self, db, worldid):
		super(Pirate, self)._load(db, worldid)
		self.__init()

		remaining_ticks, = db("SELECT remaining_ticks FROM ai_pirate WHERE rowid = ?", worldid)[0]
		Scheduler().add_new_object(Callback(self.tick), self, remaining_ticks, -1, self.tick_interval)

		remaining_ticks_long, = db("SELECT remaining_ticks_long FROM ai_pirate WHERE rowid = ?", worldid)[0]
		Scheduler().add_new_object(Callback(self.tick_long), self, remaining_ticks_long, -1, self.tick_interval)

		home = db("SELECT x, y FROM pirate_home_point")[0]
		self.home_point = Point(home[0], home[1])

		self.log.debug("Pirate: home at (%d, %d), radius %d", self.home_point.x, self.home_point.y, self.home_radius)

	def finish_loading(self, db):
		# load ships one by one from db (ship instances themselves are loaded already, but
		# we have to use them here)

		for ship_id, state_id in db("SELECT rowid, state FROM pirate_ships"):
			state = self.shipStates[state_id]
			ship = WorldObject.get_object_by_id(ship_id)
			self.ships[ship] = state

		# load unit manager
		self.unit_manager = UnitManager.load(db, self)

		# load combat manager
		self.combat_manager = PirateCombatManager.load(db, self)

		# load strategy manager
		self.strategy_manager = PirateStrategyManager.load(db, self)

		# load BehaviorManager
		self.behavior_manager = BehaviorManager.load(db, self)

	def remove_unit(self, unit):
		"""Called when a ship which is owned by the pirate is removed or killed."""
		del self.ships[unit]
		self.combat_manager.remove_unit(unit)
		self.unit_manager.remove_unit(unit)
