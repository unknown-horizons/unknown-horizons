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
from weakref import WeakKeyDictionary
from horizons.component.namedcomponent import NamedComponent
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.worldobject import WorldObject

class Fleet(WorldObject):

	log = logging.getLogger("ai.aiplayer.fleet")

	# ship states inside a fleet, fleet doesn't care about AIPlayer.shipStates since it doesn't do any reasoning.
	# all fleet cares about is to move ships from A to B.
	shipStates = Enum('idle', 'moving', 'reached')

	fleetStates = Enum('idle', 'moving')

	def __init__(self, ships):
		super(Fleet, self).__init__()
		self.__init(ships)

	def __init(self, ships):
		self.owner = ships[0].owner
		self._ships = WeakKeyDictionary()
		for ship in ships:
			self._ships[ship] = self.shipStates.idle
			ship.add_remove_listener(self._lost_ship)
		self.state = self.fleetStates.idle


	def get_ships(self):
		return self._ships.keys()

	def destroy(self):
		for ship in self._ships.keys():
			ship.remove_remove_listener(self._lost_ship)

	def _lost_ship(self):
		"""
		Used when fleet was on the move and one of the ships was killed during that.
		This way fleet has to check whether the target point was reached.
		"""
		if self._was_target_reached():
			self._fleet_reached()

	def _get_ship_states_count(self):
		counts = {
			self.shipStates.idle: 0,
			self.shipStates.moving: 0,
			self.shipStates.reached: 0,
		}
		for ship, state in self._ships.iteritems():
			counts[state]+=1
		return counts

	def _was_target_reached(self):
		"""
		Checks whether required ratio of ships reached the target.
		"""
		state_counts = self._get_ship_states_count()
		reached, total = state_counts[self.shipStates.reached], len(self._ships)
		if self.ratio <= float(reached)/total:
			return True
		return False

	def _ship_reached(self, ship):
		"""
		Called when a single ship reaches destination.
		"""
		self._ships[ship] = self.shipStates.reached
		if self._was_target_reached():
			self._fleet_reached()

	def _fleet_reached(self):
		"""
		Called when whole fleet reaches destination.
		"""
		self.state = self.fleetStates.idle
		for ship in self._ships.keys():
			self._ships[ship] = self.shipStates.idle

		self.callback()

	def move(self, destination, callback = None, ratio = 1.0):
		"""
		Move fleet to a destination.
		@param ratio: what percentage of ships has to reach destination in order for the move to be considered done (0.0 - 1.0)
		"""

		self.state = self.fleetStates.moving
		self.ratio = ratio

		# attach empty callback if not provided
		self.callback = callback if callback else lambda: None

		# This is a place to do something fancier later like preserving ship formation instead sailing to the same point
		for ship in self._ships.keys():
			self._ships[ship] = self.shipStates.moving
			ship.move(destination, Callback(self._ship_reached, ship))

	def size(self):
		return len(self._ships)

	def __str__(self):
		ships_str = "\n " + "\n ".join(["%s (%s)"%(ship.get_component(NamedComponent).name, self._ships[ship]) for ship in self._ships.keys()])
		return "Fleet: %s (%s) %s" % (self.worldid, self.state, ships_str)
