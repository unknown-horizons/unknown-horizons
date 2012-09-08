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

class CommandLineGameManager(multiprocessing.Process):
	def __init__(self, options, events):
		super(CommandLineGameManager, self).__init__()
		self.options = options
		self.events = events

	def run(self):
		print 'get the right game options'
		import run_uh
		run_uh.main(self.options)

		import horizons.main
		horizons.main.init(self.options, self.events)
		horizons.main.start_game(self.options)

		# We get here once the game has been somehow closed
		print 'end the game'

class StartGameFromCommandLineEvent(LauncherEvent):
	def execute(self, launcher):
		assert launcher.menu is None
		game = CommandLineGameManager(launcher.options, launcher.events)
		game.start()
		# This assignment is done after the start method returns because this makes it
		# easy to detect whether the process has crashed.
		launcher.game = game
