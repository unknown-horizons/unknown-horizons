# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.constants import PATHS
from horizons.editor.gui import IngameGui
from horizons.editor.worldeditor import WorldEditor
from horizons.i18n import gettext as T
from horizons.manager import SPManager
from horizons.session import Session
from horizons.timer import Timer


class EditorSession(Session):

	def __init__(self, *args, **kwargs):
		kwargs['ingame_gui_class'] = IngameGui
		super().__init__(*args, **kwargs)
		self.world_editor = None

	def create_manager(self):
		return SPManager(self)

	def create_rng(self, seed=None):
		return random.Random()

	def create_timer(self):
		return Timer()

	def load(self, *args, **kwargs):
		super().load(*args, **kwargs)
		self.world_editor = WorldEditor(self.world)
		self.ingame_gui.setup()
		# editor "games" start right away
		self.start()

	def autosave(self):
		"""Called automatically in an interval"""
		self.log.debug("Session: autosaving map")
		success = self.world_editor.save_map(PATHS.USER_MAPS_DIR, 'autosave')
		if success:
			self.ingame_gui.message_widget.add('AUTOSAVE')

	def quicksave(self):
		"""Called when user presses the quicksave hotkey"""
		self.log.debug("Session: quicksaving map")
		success = self.world_editor.save_map(PATHS.USER_MAPS_DIR, 'quicksave')
		if success:
			self.ingame_gui.message_widget.add('QUICKSAVE')
		else:
			headline = T("Failed to quicksave.")
			descr = T("An error happened during quicksave.") + "\n" + T("Your map has not been saved.")
			advice = T("If this error happens again, please contact the development team: "
				   "{website}").format(website="http://unknown-horizons.org/support/")
			self.ingame_gui.open_error_popup(headline, descr, advice)

	def save(self, savegamename):
		success = self.world_editor.save_map(PATHS.USER_MAPS_DIR, savegamename)
		return success
