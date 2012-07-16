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

from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject, Circle
from horizons.constants import UNITS
from horizons.ext.enum import Enum
from horizons.ai.generic import GenericAI
from horizons.command.unit import CreateUnit
from horizons.world.units.ship import PirateShip, TradeShip
from horizons.world.units.movingobject import MoveNotPossible
from horizons.component.namedcomponent import NamedComponent
from horizons.component.selectablecomponent import SelectableComponent


class Pirate(GenericAI):
	"""A pirate ship moving randomly around. If another ship comes into the reach
	of it, it will be followed for a short time."""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'chasing_ship', 'going_home')

	log = logging.getLogger("ai.pirate")
	regular_player = False

	caught_ship_radius = 5
	home_radius = 2

	def __init__(self, session, id, name, color, **kwargs):
		super(Pirate, self).__init__(session, id, name, color, **kwargs)

		# choose a random water tile on the coast and call it home
		self.home_point = self.session.world.get_random_possible_coastal_ship_position()
		self.log.debug("Pirate: home at (%d, %d), radius %d" % (self.home_point.x, self.home_point.y, self.home_radius))

		# create a ship and place it randomly (temporary hack)
		point = self.session.world.get_random_possible_ship_position()
		ship = CreateUnit(self.worldid, UNITS.PIRATE_SHIP, point.x, point.y)(issuer=self.session.world.player)
		self.ships[ship] = self.shipStates.idle

		for ship in self.ships.keys():
			Scheduler().add_new_object(Callback(self.send_ship, ship), self)
			Scheduler().add_new_object(Callback(self.lookout, ship), self, 8, -1)

	@staticmethod
	def get_nearest_player_ship(base_ship):
		lowest_distance = None
		nearest_ship = None
		for ship in base_ship.find_nearby_ships():
			if isinstance(ship, (PirateShip, TradeShip)) or not ship.has_component(SelectableComponent):
				continue # don't attack these ships
			distance = base_ship.position.distance_to_point(ship.position)
			if lowest_distance is None or distance < lowest_distance:
				lowest_distance = distance
				nearest_ship = ship
		return nearest_ship

	def lookout(self, pirate_ship):
		if self.ships[pirate_ship] != self.shipStates.going_home:
			ship = self.get_nearest_player_ship(pirate_ship)
			if ship:
				self.log.debug("Pirate: Scout found ship: %s" % ship.get_component(NamedComponent).name)
				self.send_ship(pirate_ship)

	def save(self, db):
		super(Pirate, self).save(db)
		db("UPDATE player SET is_pirate = 1 WHERE rowid = ?", self.worldid)
		db("INSERT INTO pirate_home_point(x, y) VALUES(?, ?)", self.home_point.x, self.home_point.y)

		for ship in self.ships:
			# prepare values
			ship_state = self.ships[ship]
			current_callback = Callback(self.lookout, ship)
			calls = Scheduler().get_classinst_calls(self, current_callback)
			assert len(calls) == 1, "got %s calls for saving %s: %s" %(len(calls), current_callback, calls)
			remaining_ticks = max(calls.values()[0], 1)

			db("INSERT INTO pirate_ships(rowid, state, remaining_ticks) VALUES(?, ?, ?)",
				ship.worldid, ship_state.index, remaining_ticks)

	def _load(self, db, worldid):
		super(Pirate, self)._load(db, worldid)
		home = db("SELECT x, y FROM pirate_home_point")[0]
		self.home_point = Point(home[0], home[1])
		self.log.debug("Pirate: home at (%d, %d), radius %d" % (self.home_point.x, self.home_point.y, self.home_radius))

	def load_ship_states(self, db):
		# load ships one by one from db (ship instances themselves are loaded already, but
		# we have to use them here)
		for ship_id, state_id, remaining_ticks in \
				db("SELECT rowid, state, remaining_ticks FROM pirate_ships"):
			state = self.shipStates[state_id]
			ship = WorldObject.get_object_by_id(ship_id)
			self.ships[ship] = state
			assert remaining_ticks is not None
			Scheduler().add_new_object(Callback(self.lookout, ship), self, remaining_ticks, -1, 8)
			ship.add_move_callback(Callback(self.ship_idle, ship))

	def send_ship(self, pirate_ship):
		self.log.debug('Pirate %s: send_ship(%s) start transition: %s' % (self.worldid, pirate_ship.get_component(NamedComponent).name, self.ships[pirate_ship]))
		done = False

		#transition the pirate ship state to 'idle' once it is inside home circumference
		if pirate_ship.position.distance(self.home_point) <= self.home_radius and self.ships[pirate_ship] == self.shipStates.going_home:
			self.ships[pirate_ship] = self.shipStates.idle
			self.log.debug('Pirate %s: send_ship(%s) reached home' % (self.worldid, pirate_ship.get_component(NamedComponent).name))

		if self.ships[pirate_ship] != self.shipStates.going_home:
			if self._chase_closest_ship(pirate_ship):
				done = True

		if not done:
			ship = self.get_nearest_player_ship(pirate_ship)
			if self.ships[pirate_ship] == self.shipStates.chasing_ship and (ship is None or
					ship.position.distance(pirate_ship.position) <= self.caught_ship_radius):
				# caught the ship, go home
				try:
					pirate_ship.move(Circle(self.home_point, self.home_radius), Callback(self.send_ship, pirate_ship))
					self.log.debug('Pirate %s: send_ship(%s) going home' % (self.worldid, pirate_ship.get_component(NamedComponent).name))
					self.ships[pirate_ship] = self.shipStates.going_home
					done = True
				except MoveNotPossible:
					self.log.debug('Pirate %s: send_ship(%s) unable to go home' % (self.worldid, pirate_ship.get_component(NamedComponent).name))

		# the ship has no other orders so it should move to a random point
		if not done and self.ships[pirate_ship] != self.shipStates.going_home:
			self.send_ship_random(pirate_ship)
		self.log.debug('Pirate %s: send_ship(%s) new state: %s' % (self.worldid, pirate_ship.get_component(NamedComponent).name, self.ships[pirate_ship]))

	def _chase_closest_ship(self, pirate_ship):
		ship = self.get_nearest_player_ship(pirate_ship)
		if ship:
			if ship.position.distance(pirate_ship.position) <= self.caught_ship_radius:
				self.ships[pirate_ship] = self.shipStates.chasing_ship
				self.log.debug('Pirate %s: _chase_closest_ship(%s) caught %s' % (self.worldid, pirate_ship.get_component(NamedComponent).name, ship.get_component(NamedComponent).name))
				return False # already caught it

			# move ship there:
			try:
				pirate_ship.move(Circle(ship.position, self.caught_ship_radius - 1), Callback(self.send_ship, pirate_ship))
				self.log.debug('Pirate %s: _chase_closest_ship(%s) chasing %s' % (self.worldid, pirate_ship.get_component(NamedComponent).name, ship.get_component(NamedComponent).name))
				self.ships[pirate_ship] = self.shipStates.chasing_ship
				return True
			except MoveNotPossible:
				self.log.debug('Pirate %s: _chase_closest_ship(%s) unable to chase the closest ship %s' % (self.worldid, pirate_ship.get_component(NamedComponent).name, ship.get_component(NamedComponent).name))
		return False


	def remove_unit(self, unit):
		"""Called when a ship which is owned by the pirate is removed or killed."""
		del self.ships[unit]
		Scheduler().rem_call(self, Callback(self.lookout, unit))
