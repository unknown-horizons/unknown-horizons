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
from collections import Counter
from weakref import WeakKeyDictionary
from horizons.component.namedcomponent import NamedComponent
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.shapes.circle import Circle
from horizons.util.shapes.point import Point
from horizons.util.worldobject import WorldObject
from horizons.world.units.movingobject import MoveNotPossible


class Fleet(WorldObject):
	"""
	Fleet object is responsible for moving a group of ship around the map in an ordered manner, that is:
	1. provide a single move callback for a fleet as a whole,
	2. resolve self-blocks in a group of ships
	3. resolve MoveNotPossible exceptions.
	"""

	log = logging.getLogger("ai.aiplayer.fleet")

	# ship states inside a fleet, fleet doesn't care about AIPlayer.shipStates since it doesn't do any reasoning.
	# all fleet cares about is to move ships from A to B.
	shipStates = Enum('idle', 'moving', 'blocked', 'reached')

	# state for a fleet as a whole
	fleetStates = Enum('idle', 'moving')

	def __init__(self, ships):
		super(Fleet, self).__init__()

		assert len(ships) > 0, "request to create a fleet from  %s ships" % (len(ships))
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
		# TODO: Check if fleet has 0 members, then request to get destroyed OR make unitmanager check for that in it's tick.

	def _get_ship_states_count(self):
		"""
		Returns Counter about how many ships are in state idle, moving, reached.
		"""
		return Counter(self._ships.values())

	def _was_target_reached(self):
		"""
		Checks whether required ratio of ships reached the target.
		"""
		state_counts = self._get_ship_states_count()

		# below: include blocked ships as "reached" as well since there's not much more left to do,
		# and it's better than freezing the whole fleet
		reached = state_counts[self.shipStates.reached] + state_counts[self.shipStates.blocked]
		total = len(self._ships)
		print reached, total, self.ratio
		if self.ratio <= float(reached) / total:
			return True
		else:
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

		if self.callback:
			self.callback()

	def _move_ship(self, ship, destination, callback):
		# retry ad infinitum. Not the most elegant solution but will do for a while.
		# TODO: Think of a better way to resolve self-blocks
		# Idea: mark ship as "blocked" through state and check whether they all are near the destination anyway
		# 1. If they don't make them sail again.
		# 2. If they do, assume they reached the spot.
		try:
			ship.move(destination, callback=callback, blocked_callback=Callback(self._move_ship, ship, destination, callback))
		except MoveNotPossible:
			self._ships[ship] = self.shipStates.blocked

	def _get_circle_size(self):
		"""
		Destination circle size for movement calls that involve more than one ship.
		"""

		return 5
		#return min(self.size(), 5)

	def move(self, destination, callback=None, ratio=1.0):
		"""
		Move fleet to a destination.
		@param ratio: what percentage of ships has to reach destination in order for the move to be considered done:
			0.0 - None (not really useful, executes the callback right away)
			0.0001 - effectively ANY ship
			1.0 - ALL of the ships
			0.5 - at least half of the ships
			etc.
		"""
		assert self.size() > 0, "ordered to move a fleet consisting of 0 ships"

		# it's ok to specify single point for a destination only when there's only one ship in a fleet
		if isinstance(destination, Point) and self.size() > 1:
			destination = Circle(destination, self._get_circle_size())

		self.state = self.fleetStates.moving
		self.ratio = ratio

		self.callback = callback

		# This is a good place to do something fancier later like preserving ship formation instead sailing to the same point
		for ship in self._ships.keys():
			self._ships[ship] = self.shipStates.moving
			self._move_ship(ship, destination, Callback(self._ship_reached, ship))

	def size(self):
		return len(self._ships)

	def __str__(self):
		ships_str = "\n " + "\n ".join(["%s (fleet:%s, global:%s)" % (ship.get_component(NamedComponent).name, self._ships[ship], self.owner.ships[ship]) for ship in self._ships.keys()])
		return "Fleet: %s (%s) %s" % (self.worldid, self.state, ships_str)
