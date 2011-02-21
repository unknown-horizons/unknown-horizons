# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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
import os
import time
import shutil
import traceback

import horizons.main

from horizons.session import Session
from horizons.manager import SPManager
from horizons.extscheduler import ExtScheduler
from horizons.constants import PATHS, GAME_SPEED
from horizons.savegamemanager import SavegameManager
from horizons.util.dbreader import DbReader


class SPSession(Session):
	def create_manager(self):
		return SPManager(self)

	def create_rng(self):
		return random.Random()

	def load(self, *args, **kwargs):
		super(SPSession, self).load(*args, **kwargs)
		# single player games start right away
		self.start()

	def speed_set(self, ticks):
		"""Set game speed to ticks ticks per second"""
		old = self.timer.ticks_per_second
		self.timer.ticks_per_second = ticks
		self.view.map.setTimeMultiplier(float(ticks) / float(GAME_SPEED.TICKS_PER_SECOND))
		if old == 0 and self.timer.tick_next_time is None: #back from paused state
			if self.paused_time_missing is None:
				# happens if e.g. a dialog pauses the game during startup on hotkeypress
				self.timer.tick_next_time = time.time()
			else:
				self.timer.tick_next_time = time.time() + (self.paused_time_missing / ticks)
		elif ticks == 0 or self.timer.tick_next_time is None:
			# go into paused state or very early speed change (before any tick)
			if self.timer.tick_next_time is not None:
				self.paused_time_missing = (self.timer.tick_next_time - time.time()) * old
			else:
				self.paused_time_missing =  None
			self.timer.tick_next_time = None
		else:
			self.timer.tick_next_time += ((self.timer.tick_next_time - time.time()) * old / ticks)
		self.display_speed()

	def start(self):
		super(SPSession, self).start()
		interval = int(horizons.main.fife.get_uh_setting("AutosaveInterval"))
		# get_uh_setting returns floats like 4.0 and 42.0 since slider stepping is 1.0.
		if interval != 0: #autosave
			self.log.debug("Initing autosave every %s minutes", interval)
			ExtScheduler().add_new_object(self.autosave, self, interval * 60, -1)

	def autosave(self):
		"""Called automatically in an interval"""
		self.log.debug("Session: autosaving")
		# call saving through horizons.main and not directly through session, so that save errors are handled
		success = self.save(SavegameManager.create_autosave_filename())
		if success:
			SavegameManager.delete_dispensable_savegames(autosaves = True)

	def quicksave(self):
		"""Called when user presses the quicksave hotkey"""
		self.log.debug("Session: quicksaving")
		# call saving through horizons.main and not directly through session, so that save errors are handled
		success = self.save(SavegameManager.create_quicksave_filename())
		if success:
			self.ingame_gui.message_widget.add(None, None, 'QUICKSAVE')
			SavegameManager.delete_dispensable_savegames(quicksaves = True)
		else:
			self.gui.show_popup(_('Error'), _('Failed to quicksave.'))

	def quickload(self):
		"""Loads last quicksave"""
		files = SavegameManager.get_quicksaves(include_displaynames = False)[0]
		if len(files) == 0:
			self.gui.show_popup(_("No quicksaves found"), _("You need to quicksave before you can quickload."))
			return
		files.sort()
		horizons.main.load_game(files[-1])

	def save(self, savegamename=None):
		"""Saves a game
		@param savegamename: string with the full path of the savegame file or None to let user pick one
		@return: bool, whether save was successfull
		"""
		if savegamename is None:
			savegamename = self.gui.show_select_savegame(mode='save')
			if savegamename is None:
				return False # user aborted dialog
			savegamename = SavegameManager.create_filename(savegamename)

		savegame = savegamename
		assert os.path.isabs(savegame)
		self.log.debug("Session: Saving to %s", savegame)
		try:
			if os.path.exists(savegame):
				os.unlink(savegame)
			shutil.copyfile(PATHS.SAVEGAME_TEMPLATE, savegame)
			self.savecounter += 1

			db = DbReader(savegame)
		except IOError: # usually invalid filename
			self.gui.show_popup(_("Invalid filename"), _("You entered an invalid filename."))
			self.save() # retry with new savegamename entered by the user
			# this must not happen with quicksave/autosave
			return

		try:
			db("BEGIN")
			self.world.save(db)
			#self.manager.save(db)
			self.view.save(db)
			self.ingame_gui.save(db)
			self.campaign_eventhandler.save(db)

			for instance in self.selected_instances:
				db("INSERT INTO selected(`group`, id) VALUES(NULL, ?)", instance.worldid)
			for group in xrange(len(self.selection_groups)):
				for instance in self.selection_groups[group]:
					db("INSERT INTO selected(`group`, id) VALUES(?, ?)", group, instance.worldid)

			SavegameManager.write_metadata(db, self.savecounter)
			db("COMMIT")
			return True
		except:
			print "Save Exception"
			traceback.print_exc()
			db.close() # close db before delete
			os.unlink(savegame) # remove invalid savegamefile
