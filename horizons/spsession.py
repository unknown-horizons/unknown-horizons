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

import horizons.main

from horizons.session import Session
from horizons.manager import SPManager
from horizons.constants import SINGLEPLAYER
from horizons.savegamemanager import SavegameManager
from horizons.timer import Timer

class SPSession(Session):
	"""Session tailored for singleplayer games."""

	def create_manager(self):
		return SPManager(self)

	def create_rng(self, seed=None):
		return random.Random(seed if seed is not None else SINGLEPLAYER.SEED)

	def create_timer(self):
		return Timer(freeze_protection=True)

	def load(self, *args, **kwargs):
		super(SPSession, self).load(*args, **kwargs)
		# single player games start right away
		self.start()

	def autosave(self):
		"""Called automatically in an interval"""
		self.log.debug("Session: autosaving")
		success = self._do_save(SavegameManager.create_autosave_filename())
		if success:
			SavegameManager.delete_dispensable_savegames(autosaves = True)
			self.ingame_gui.message_widget.add(point=None, string_id='AUTOSAVE')

	def quicksave(self):
		"""Called when user presses the quicksave hotkey"""
		self.log.debug("Session: quicksaving")
		# call saving through horizons.main and not directly through session, so that save errors are handled
		success = self._do_save(SavegameManager.create_quicksave_filename())
		if success:
			SavegameManager.delete_dispensable_savegames(quicksaves = True)
			self.ingame_gui.message_widget.add(point=None, string_id='QUICKSAVE')
		else:
			headline = _(u"Failed to quicksave.")
			descr = _(u"An error happened during quicksave. Your game has not been saved.")
			advice = _(u"If this error happens again, please contact the development team:") + \
			           u"unknown-horizons.org/support/"
			self.gui.show_error_popup(headline, descr, advice)

	def save(self, savegamename=None):
		"""Saves a game
		@param savegamename: string with the full path of the savegame file or None to let user pick one
		@return: bool, whether no error happened (user aborting dialog means success)
		"""
		if savegamename is None:
			savegamename = self.gui.show_select_savegame(mode='save')
			if savegamename is None:
				return True # user aborted dialog
			savegamename = SavegameManager.create_filename(savegamename)

		success= self._do_save(savegamename)
		if success:
			self.ingame_gui.message_widget.add(point=None, string_id='SAVED_GAME')
		return success
