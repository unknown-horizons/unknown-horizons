# -*- coding: utf-8 -*-
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

from horizons.world.settlement import Settlement
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED
from horizons.world.component.storagecomponent import StorageComponent

class Disaster(object):
	"""Prototype class for disasters."""
	log = logging.getLogger("world.disaster")

	# Chance this disaster is seeded into a settlement in a tick of  the
	# disaster manager
	SEED_CHANCE = 0.5

	# Time in ticks this disasters pauses between each expansion
	EXPANSION_TIME = GAME_SPEED.TICKS_PER_SECOND * 5

	# Resource to distribute to infected buildings
	#	This is how preventory units (doctors) spot affected buildings.
	DISASTER_RES = None

	def __init__(self, settlement, manager):
		"""
		@param settlement: Settlement instance this disaster operates on
		@param manager: The disaster manager that initiated this disaster
		"""
		assert isinstance(settlement, Settlement), "Not a settlement!"
		self._settlement = settlement
		self._manager = manager
		Scheduler().add_new_object(self.expand, self, run_in=self.EXPANSION_TIME, loops=-1)

	def evaluate(self):
		"""Called to evaluate if this disaster is still active"""
		raise NotImplementedError()

	def expand(self):
		"""Called to make the disaster expand further"""
		raise NotImplementedError()

	def infect(self, building):
		"""Used to expand disaster to this building. Usually called by expand and breakout"""
		if self.DISASTER_RES is not None:
			remnant = building.get_component(StorageComponent).inventory.alter(self.DISASTER_RES, 1)
			assert remnant == 0

	def breakout(self):
		"""Picks (a) object(s) to start a breakout.
		@return bool: If breakout was successful or not"""
		raise NotImplementedError()
		return False

	def wreak_havoc(self):
		"""The implementation to whatever the disaster does to affected
		objects goes here"""
		raise NotImplementedError()

	@classmethod
	def can_breakout(cls, settlement):
		"""Returns whether or not a disaster can break out in the
		settlement"""
		raise NotImplementedError()

	def end(self):
		"""End this class, used for cleanup. Called by the DisasterManager
		in end_disaster() automatically"""
		pass
