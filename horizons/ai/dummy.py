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
import horizons.main

from horizons.entities import Entities
from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject
from horizons.constants import RES, UNITS
from horizons.ext.enum import Enum
from horizons.ai.generic import AIPlayer
from horizons.world.units.movingobject import MoveNotPossible


class DummyAI(AIPlayer):
	"""A player that does predefined actions to make sure, that the game code supports
	AI. It is just for developing and testing."""
