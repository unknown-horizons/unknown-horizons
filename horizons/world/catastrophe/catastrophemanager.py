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

from horizons.world.catastrophe.firecatastrophe import FireCatastrophe
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED

class CatastropheManager(object):
	"""The catastrophe manager manages catastrophes. It seeds them into the
	game world and makes all requirements for a catastrophe are met before
	seeding it."""

	# Number of ticks between calls to run()
	CALL_EVERY = GAME_SPEED.TICKS_PER_SECOND * 5

	def __init__(self, session):
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		# List of possible catastrophe classes
		self.catastrophes = [FireCatastrophe]

		# Mapping settlement -> active catastrophes
		self._active_catastrophe = {}

		Scheduler().add_new_object(self.run, self, run_in = self.CALL_EVERY, loops = -1)

	def tick(self):
		pass

	def run(self):
		for settlement in self.session.world.settlements:
			for catastrophe in self.catastrophes:
				if not settlement in self._active_catastrophe:
					if self.session.random.random() <= catastrophe.SEED_CHANCE:
						if catastrophe.can_breakout(settlement):
							print "Seeding catastrophe:", catastrophe
							cata = catastrophe(settlement, self)
							cata.breakout()
							self._active_catastrophe[settlement] = cata

	def end_catastrophe(self, settlement):
		# End the catastrophe
		self._active_catastrophe[settlement].end()
		del self._active_catastrophe[settlement]


