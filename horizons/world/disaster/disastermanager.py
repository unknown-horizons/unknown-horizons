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

from horizons.world.disaster.firedisaster import FireDisaster
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED
from horizons.util import WorldObject

class DisasterManager(object):
	"""The disaster manager manages disasters. It seeds them into the
	game world and makes all requirements for a disaster are met before
	seeding it."""
	log = logging.getLogger("world.disaster")

	# Number of ticks between calls to run()
	CALL_EVERY = GAME_SPEED.TICKS_PER_SECOND * 60
	#CALL_EVERY =  1 # to conjure the demons of armageddon

	def __init__(self, session, disabled=False):
		"""
		@param disabled: Don't do anything at all if true (but be responsive to normal calls)"""
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		self.disabled = disabled
		# List of possible disaster classes
		self.disasters = [FireDisaster]

		# Mapping settlement -> active disasters
		self._active_disaster = {}

		# keep call also when disabled, simplifies save/load
		Scheduler().add_new_object(self.run, self, run_in=self.CALL_EVERY, loops=-1)

	def save(self, db):
		ticks = Scheduler().get_remaining_ticks(self, self.run, True)
		db("INSERT INTO disaster_manager(remaining_ticks) VALUES(?)", ticks)
		for disaster in self._active_disaster.itervalues():
			disaster.save(db)

	def load(self, db):
		db_data = db("SELECT remaining_ticks FROM disaster_manager")
		if db_data:
			Scheduler().rem_all_classinst_calls(self)
			ticks = db_data[0][0] # only one row in table
			Scheduler().add_new_object(self.run, self, run_in=ticks,
			                           loop_interval=self.CALL_EVERY, loops = -1)

		for disaster_id, disaster_type, settlement_id in db("SELECT rowid, type, settlement FROM disaster"):
			settlement = WorldObject.get_object_by_id(settlement_id)
			klass = (i for i in  self.disasters if i.TYPE == disaster_type).next()
			cata = klass(settlement, self)
			self._active_disaster[settlement] = cata
			cata.load(db, disaster_id)

	def run(self):
		if self.disabled:
			return
		for settlement in self.session.world.settlements:
			for disaster in self.disasters:
				if not settlement in self._active_disaster:
					if self.session.random.random() <= disaster.SEED_CHANCE:
						if disaster.can_breakout(settlement):
							self.log.debug("Seeding disaster: %s", disaster)
							cata = disaster(settlement, self)
							cata.breakout()
							self._active_disaster[settlement] = cata
						else:
							self.log.debug("Disaster %s would breakout apply but can't breakout",
							               disaster)

	def end_disaster(self, settlement):
		# End the disaster
		self.log.debug("ending desaster in %s", settlement)
		self._active_disaster[settlement].end()
		del self._active_disaster[settlement]

	def is_affected(self, settlement):
		"""Returns whether there is currently a disaster in a settlement"""
		return settlement in self._active_disaster



