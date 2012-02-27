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

import random

from horizons.session import Session
from horizons.manager import MPManager
from horizons.timer import Timer
from horizons.savegamemanager import SavegameManager
from horizons.command.game import SaveCommand

class MPSession(Session):
	"""Session class fo multiplayer games."""

	def __init__(self, gui, db, network_interface, **kwargs):
		"""
		@param network_interface: instance of NetworkInterface to use for this game
		@param rng_seed: seed for random number generator
		"""
		self.__network_interface = network_interface
		super(MPSession, self).__init__(gui, db, **kwargs)

	def speed_set(self, ticks, suggestion=False):
		"""Set game speed to ticks ticks per second"""
		if not suggestion:
			super(MPSession, self).speed_set(ticks, suggestion)

	def create_manager(self):
		return MPManager(self, self.__network_interface)

	def create_rng(self, seed=None):
		return random.Random(seed)

	def create_timer(self):
		return Timer(freeze_protection=False)

	def end(self):
		self.__network_interface.disconnect()
		super(MPSession, self).end()

	def autosave(self):
		SaveCommand( SavegameManager.create_multiplayer_autosave_name() ).execute(self)

	def quicksave(self):
		SaveCommand( SavegameManager.create_multiplayer_quicksave_name() ).execute(self)

	def quickload(self):
		self.gui.show_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))

	def save(self, savegamename=None):
		if savegamename is None:
			def sanity_checker(string):
				try:
					SavegameManager.create_multiplayersave_filename(string)
				except RuntimeError:
					return False
				else:
					return True
			sanity_criteria = _("The filename must consist only of letters, numbers, spaces and _.-")
			savegamename = self.gui.show_select_savegame(mode='mp_save', sanity_checker=sanity_checker,
			                                             sanity_criteria=sanity_criteria)
			if savegamename is None:
				return True # user aborted dialog

		SaveCommand( savegamename ).execute(self)
		return True
