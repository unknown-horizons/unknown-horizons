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

from horizons.world.settlement import Settlement
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED

class Catastrophe(object):
	"""Prototype class for catastrophes."""

	# Change this catastrophe is seeded into a settlement in a tick of  the
	# catastrophe manager
	SEED_CHANCE = 0.5

	# Time in ticks this catastrophes pauses between each expansion
	EXPANSION_TIME = GAME_SPEED.TICKS_PER_SECOND * 5

	def __init__(self, settlement, manager):
		"""
		@param settlement: Settlement instance this catastrophe operates on
		@param manager: The catastrophe manager that initiated this catastrophe
		"""
		assert isinstance(settlement, Settlement), "Not a settlement!"
		self._settlement = settlement
		self._manager = manager
		Scheduler().add_new_object(self.expand, self, run_in=self.EXPANSION_TIME, loops=-1)

	def evaluate(self):
		"""Called to evaluate if this catastrophe is still active"""
		raise NotImplementedError()

	def expand(self):
		"""Called to make the catastrophe expand further"""
		raise NotImplementedError()

	def breakout(self):
		"""Picks (a) object(s) to start a breakout.
		@return bool: If breakout was successful or not"""
		raise NotImplementedError()
		return False

	def wreak_havoc(self):
		"""The implementation to whatever the catastrophe does to affected
		objects goes here"""
		raise NotImplementedError()

	@classmethod
	def can_breakout(cls, settlement):
		"""Returns whether or not a catastrophe can break out in the
		settlement"""
		raise NotImplementedError()

	def end(self):
		"""End this class, used for cleanup. Called by the CatastropheManager
		in end_catastrophe() automatically"""
		pass