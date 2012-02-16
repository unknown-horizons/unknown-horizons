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

class MPSession(Session):
	"""Session class for multiplayer games."""

	def __init__(self, gui, db, network_interface, **kwargs):
		"""
		@param network_interface: instance of NetworkInterface to use for this game
		@param rng_seed: seed for random number generator
		"""
		self.__network_interface = network_interface
		super(MPSession, self).__init__(gui, db, **kwargs)
		self.disable_speed_buttons()

	def create_manager(self):
		return MPManager(self, self.__network_interface)

	def create_rng(self, seed=None):
		return random.Random(seed)

	def create_timer(self):
		return Timer(freeze_protection=False)

	def speed_set(self, ticks, suggestion=False):
		if suggestion:
			# ignore suggested speed changes in multiplayer
			return
		self.gui.show_popup(_("Can't change speed of network game."), _("You cannot change the speed of a multiplayer game"))

	def disable_speed_buttons(self):
		up_icon = self.ingame_gui.widgets['minimap'].findChild(name='speedUp')
		down_icon = self.ingame_gui.widgets['minimap'].findChild(name='speedDown')
		up_icon.set_inactive()
		down_icon.set_inactive()
		self.ingame_gui.display_game_speed(u'')

	def end(self):
		self.__network_interface.disconnect()
		super(MPSession, self).end()

	def autosave(self):
		self.gui.show_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))
	def quicksave(self):
		self.gui.show_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))
	def quickload(self):
		self.gui.show_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))
	def save(self, savegame=None):
		self.gui.show_popup(_("Not possible"), _("Save/load for multiplayer games is not possible yet"))
