# ###################################################
# Copyright (C) 2008-2014 The Unknown Horizons Team
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

import horizons.main
from horizons.session import Session
from horizons.manager import MPManager
from horizons.timer import Timer
from horizons.savegamemanager import SavegameManager
from horizons.command.game import SaveCommand

class MPSession(Session):
	"""Session class for multiplayer games."""

	def __init__(self, db, network_interface, **kwargs):
		"""
		@param network_interface: instance of NetworkInterface to use for this game
		@param rng_seed: seed for random number generator
		"""
		self.__network_interface = network_interface
		self.__network_interface.subscribe("game_starts", self._start_game)
		self.__network_interface.subscribe("error", self._on_error)
		super(MPSession, self).__init__(db, **kwargs)

	def _start_game(self, game):
		horizons.main.start_multiplayer(game)

	def _on_error(self, exception, fatal=True):
		"""Error callback"""
		if fatal:
			self.timer.ticks_per_second = 0
			self.ingame_gui.windows.open_popup(_("Fatal Network Error"),
		                                       _("Something went wrong with the network:") + u'\n' +
		                                       unicode(exception) )
			self.quit()
		else:
			self.ingame_gui.open_popup(_("Error"), unicode(exception))

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
		self.__network_interface.unsubscribe("error", self._on_error)
		self.__network_interface.unsubscribe("game_starts", self._start_game)
		self.__network_interface.disconnect()
		super(MPSession, self).end()

	def autosave(self):
		self.ingame_gui.open_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))
		return  #TODO disabled for now, see #2151 for details
		SaveCommand( SavegameManager.create_multiplayer_autosave_name() ).execute(self)

	def quicksave(self):
		self.ingame_gui.open_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))
		return  #TODO disabled for now, see #2151 for details
		SaveCommand( SavegameManager.create_multiplayer_quicksave_name() ).execute(self)

	def quickload(self):
		self.ingame_gui.open_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))

	def save(self, savegamename=None):
		self.ingame_gui.open_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))
		return  #TODO disabled for now, see #2151 for details
		if savegamename is None:
			def sanity_checker(string):
				try:
					SavegameManager.create_multiplayersave_filename(string)
				except RuntimeError:
					return False
				else:
					return True
			sanity_criteria = _(
				"The filename must consist only of letters, numbers, spaces "
				"and these characters: _ . -"
			)
			savegamename = self.ingame_gui.show_select_savegame(mode='mp_save', sanity_checker=sanity_checker,
			                                                    sanity_criteria=sanity_criteria)
			if savegamename is None:
				return True # user aborted dialog

		SaveCommand( savegamename ).execute(self)
		return True
