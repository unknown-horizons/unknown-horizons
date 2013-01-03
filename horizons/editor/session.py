# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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
from horizons.session import Session
from horizons.manager import SPManager
from horizons.timer import Timer


class EditorSession(Session):

	def __init__(self, *args, **kwargs):
		kwargs['ingame_gui_class'] = IngameGui
		super(EditorSession, self).__init__(*args, **kwargs)
		self.world_editor = None

	def create_manager(self):
		return SPManager(self)

	def create_rng(self, seed=None):
		return random.Random()

	def create_timer(self):
		return Timer()

	def load(self, *args, **kwargs):
		super(EditorSession, self).load(*args, **kwargs)
		self.world_editor = WorldEditor(self.world)
		self.ingame_gui.setup()
		# editor "games" start right away
		self.start()

	def autosave(self):
		# TODO see issue 1935
		pass

	def quicksave(self):
		# TODO see issue 1935
		pass

	def save(self, name):
		self.world_editor.save_map(PATHS.USER_MAPS_DIR, name)
