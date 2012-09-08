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

import multiprocessing

from launcher.events import LauncherEvent

class MenuManager(multiprocessing.Process):
	def __init__(self, options, events):
		super(MenuManager, self).__init__()
		self.options = options
		self.events = events

	def run(self):
		print 'start showing menu'
		import run_uh
		run_uh.main(self.options)

		import horizons.main
		horizons.main.init(self.options, self.events)
		horizons.main.start_game(self.options)
		import horizons.globals
		horizons.globals.fife.run()

		# We get here once the game has been somehow closed
		print 'stop showing menu'

class OpenMainMenuEvent(LauncherEvent):
	def execute(self, launcher):
		assert launcher.menu is None
		menu = MenuManager(launcher.options, launcher.events)
		menu.start()
		# This assignment is done after the start method returns because this makes it
		# easy to detect whether the process has crashed.
		launcher.menu = menu
