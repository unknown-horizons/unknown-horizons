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
		Scheduler().add_new_object(Callback(self.send_ship_random, self.ships.keys()[0]), self)
