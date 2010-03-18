# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import random
import logging

import horizons.main

from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject, Circle
from horizons.constants import RES, UNITS, BUILDINGS
from horizons.ext.enum import Enum
from horizons.ai.generic import AIPlayer
from horizons.world.storageholder import StorageHolder
from horizons.command.unit import CreateUnit


class Pirate(AIPlayer):
	"""A pirate ship moving randomly around. If another ship comes into the reach
	of it, it will be followed for a short time."""

	log = logging.getLogger("ai.pirate")

	def __init__(self, session, id, name, color, **kwargs):
		super(Pirate, self).__init__(session, id, name, color, **kwargs)

		# create a ship and place it randomly (temporary hack)
		point = self.session.world.get_random_possible_ship_position()
		ship = CreateUnit(self.getId(), UNITS.PIRATE_SHIP_CLASS, point.x, point.y).execute(self.session)
		self.ships[ship] = self.shipStates.idle
		for ship in self.ships.keys():
			Scheduler().add_new_object(Callback(self.send_ship, ship), self)
			Scheduler().add_new_object(Callback(self.lookout, ship), self, 8, -1)
	
	@staticmethod
	def get_nearest_ship(base_ship):
		lowest_distance = None
		nearest_ship = None
		for ship in base_ship.find_nearby_ships():
			distance = base_ship.position.distance_to_point(ship.position)
			if lowest_distance is None or distance < lowest_distance:
				nearest_ship = ship
		return nearest_ship
	
	def lookout(self, pirate_ship):
		ship = self.get_nearest_ship(pirate_ship)
		if ship:
			self.log.debug("Pirate: Scout found ship: %s" % ship.name)
	
	def save(self, db):
		super(Pirate, self).save(db)
		db("UPDATE player SET is_pirate = 1 WHERE rowid = ?", self.getId())

		for ship in self.ships:
			ship_state = self.ships[ship]

			db("INSERT INTO pirate_ships(rowid, state) VALUES(?, ?)",
				ship.getId(), ship_state.index) #, remaining_ticks)

	def load_ship_states(self, db):
		# load ships one by one from db (ship instances themselves are loaded already, but
		# we have to use them here)
		for ship_id, state_id, remaining_ticks in \
				db("SELECT rowid, state, remaining_ticks FROM pirate_ships"):
			state = self.shipStates[state_id]
			ship = WorldObject.get_object_by_id(ship_id)
			self.ships[ship] = state
