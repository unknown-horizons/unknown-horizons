# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, Any

from horizons.constants import GAME_SPEED
from horizons.ext.enum import Enum
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.world.player import Player
from horizons.world.units.unitexeptions import MoveNotPossible

if TYPE_CHECKING:
    from horizons.session import Session
    from horizons.util.color import Color
    from horizons.world.units.ship import Ship


class GenericAI(Player):
	"""Class for AI players implementing generic stuff."""

	shipStates = Enum('idle', 'moving_random')

	def __init__(
		self,
		session: Session,
		id: int,
		name: str,
		color: Color,
		**kwargs: Any,
	) -> None:
		super().__init__(session, id, name, color, **kwargs)
		self._init_state()

	def _init_state(self) -> None:
		self.ships = weakref.WeakValueDictionary() # {ship : state}. used as list of ships and structure to know their state

	def _load(self, db, worldid: int) -> None:
		super()._load(db, worldid)
		self._init_state()

	def send_ship(self, ship: Ship) -> None:
		self.send_ship_random(ship)

	def send_ship_random(self, ship: Ship) -> None:
		"""Sends a ship to a random position on the map.
		@param ship: Ship instance that is to be used."""
		# find random position
		point = self.session.world.get_random_possible_ship_position()
		self.log.debug("%s %s: moving to random location %d, %d", self.__class__.__name__, self.worldid, point.x, point.y)
		# move ship there:
		try:
			ship.move(point, Callback(self.ship_idle, ship))
		except MoveNotPossible:
			self.log.info("%s %s: ship blocked", self.__class__.__name__, self.worldid)
			# retry moving ship in 2 secs
			Scheduler().add_new_object(Callback(self.ship_idle, ship), self,
			                           GAME_SPEED.TICKS_PER_SECOND * 2)
			return
		self.ships[ship] = self.shipStates.moving_random

	def ship_idle(self, ship: Ship) -> None:
		"""Called if a ship is idle. Sends ship to a random place.
		@param ship: ship instance"""
		self.log.debug("%s %s: idle, moving to random location", self.__class__.__name__, self.worldid)
		Scheduler().add_new_object(Callback(self.send_ship, ship), self)

	def end(self) -> None:
		self.ships = None
		super().end()
