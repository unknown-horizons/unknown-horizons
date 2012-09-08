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

import horizons.globals

class GameManager(multiprocessing.Process):
	def __init__(self, options, events, config):
		super(GameManager, self).__init__()
		self.options = options
		self.events = events
		self.config = config

	def run(self):
		print 'start single player game'
		import run_uh
		run_uh.main(self.options)

		c = self.config
		import horizons.main
		print 'before horizons.main.start'
		horizons.main.init(self.options, self.events)
		horizons.main.start_game(self.options)
		print 'after horizons.main.start'
		horizons.main.start_singleplayer(c.map_file, c.playername, self._get_playercolor(),
										 c.is_scenario, c.campaign, c.ai_players,
										 c.human_ai, c.trader_enabled, c.pirate_enabled,
										 c.natural_resource_multiplier, c.force_player_id,
										 c.disasters_enabled)
		print 'before horizons.globals.fife.run'
		horizons.globals.fife.run()
		print 'after horizons.globals.fife.run'

		# We get here once the game has been somehow closed
		print 'end single player game'

	def _get_playercolor(self):
		c = self.config.player_color_tuple
		if c is None:
			return None
		from horizons.util.color import Color
		return Color(*c)

class StartSinglePlayerGameEvent(LauncherEvent):
	def __init__(self, config):
		super(StartSinglePlayerGameEvent, self).__init__()
		self.config = config

	def execute(self, launcher):
		if launcher.game:
			launcher.close_game()

		assert launcher.game is None
		game = GameManager(launcher.options, launcher.events, self.config)
		game.start()

		# This assignment is done after the start method returns because this makes it
		# easy to detect whether the process has crashed.
		launcher.game = game
		launcher.close_menu()
