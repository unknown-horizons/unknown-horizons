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

from horizons.world.disaster.firedisaster import FireDisaster
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED

class DisasterManager(object):
	"""The disaster manager manages disasters. It seeds them into the
	game world and makes all requirements for a disaster are met before
	seeding it."""

	# Number of ticks between calls to run()
	CALL_EVERY = GAME_SPEED.TICKS_PER_SECOND * 5

	def __init__(self, session):
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		# List of possible disaster classes
		self.disasters = [FireDisaster]

		# Mapping settlement -> active disasters
		self._active_disaster = {}

		Scheduler().add_new_object(self.run, self, run_in = self.CALL_EVERY, loops = -1)

	def tick(self):
		pass

	def run(self):
		for settlement in self.session.world.settlements:
			for disaster in self.disasters:
				if not settlement in self._active_disaster:
					if self.session.random.random() <= disaster.SEED_CHANCE:
						if disaster.can_breakout(settlement):
							print "Seeding disaster:", disaster
							cata = disaster(settlement, self)
							cata.breakout()
							self._active_disaster[settlement] = cata

	def end_disaster(self, settlement):
		# End the disaster
		self._active_disaster[settlement].end()
		del self._active_disaster[settlement]


