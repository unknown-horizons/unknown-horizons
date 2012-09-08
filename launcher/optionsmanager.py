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

import optparse

from horizons.constants import AI, GAME, SINGLEPLAYER

class OptionsManager(object):
	__startup_options = ['start_map', 'start_random_map', 'start_specific_random_map',
						 'start_scenario', 'start_campaign', 'start_dev_map', 'load_map',
						 'load_quicksave', 'stringpreview', 'gui_test',
						 'generate_minimap', 'create_mp_game', 'join_mp_game']

	def __init__(self):
		self._options = self.__get_parser().parse_args()[0]

		# This points to the run_uh setup_debugging function
		# TODO: find a better way to handle it
		self.setup_debugging_func = None

	def clear_startup_options(self):
		"""
		Clear options that avoid opening the main menu.
		
		This is necessary because otherwise the same option would be applied after ending
		the session and trying to start a new one.
		"""

		for option in self.__startup_options:
			setattr(self._options, option, None)

	def opening_menu(self):
		for option in self.__startup_options:
			if getattr(self._options, option) is not None:
				return False
		return True

	def __getattr__(self, name):
		"""Redirect options queries to the options object."""
		if name == '_options':
			return None
		return getattr(self._options, name)

	def set_runtime_constants(self):
		if self._options.ai_highlights:
			AI.HIGHLIGHT_PLANS = True
		if self._options.ai_combat_highlights:
			AI.HIGHLIGHT_COMBAT = True
		if self._options.human_ai:
			AI.HUMAN_AI = True

		if self._options.max_ticks:
			GAME.MAX_TICKS = self._options.max_ticks

		if self._options.sp_seed:
			SINGLEPLAYER.SEED = self._options.sp_seed

	@classmethod
	def __get_parser(cls):
		"""Returns inited OptionParser object"""
		from horizons.constants import VERSION
		p = optparse.OptionParser(usage="%prog [options]", version=VERSION.string())
		p.add_option("-d", "--debug", dest="debug", action="store_true",
		             default=False, help="Enable debug output to stderr and a logfile.")
		p.add_option("--fife-path", dest="fife_path", metavar="<path>",
		             help="Specify the path to FIFE root directory.")
		p.add_option("--restore-settings", dest="restore_settings", action="store_true", default=False,
		             help="Restores the default settings. "
		                  "Useful if Unknown Horizons crashes on startup due to misconfiguration.")
		p.add_option("--mp-master", dest="mp_master", metavar="<ip:port>",
		             help="Specify alternative multiplayer master server.")
		p.add_option("--mp-bind", dest="mp_bind", metavar="<ip:port>",
		             help="Specify network address to bind local network client to. "
		                  "This is useful if NAT holepunching is not working but you can forward a static port.")

		start_uh = optparse.OptionGroup(p, "Starting Unknown Horizons")
		start_uh.add_option("--start-map", dest="start_map", metavar="<map>",
		             help="Starts <map>. <map> is the mapname.")
		start_uh.add_option("--start-random-map", dest="start_random_map", action="store_true",
		             help="Starts a random map.")
		start_uh.add_option("--start-specific-random-map", dest="start_specific_random_map",
		             metavar="<seed>", help="Starts a random map with seed <seed>.")
		start_uh.add_option("--start-scenario", dest="start_scenario", metavar="<scenario>",
		             help="Starts <scenario>. <scenario> is the scenarioname.")
		start_uh.add_option("--start-campaign", dest="start_campaign", metavar="<campaign>",
		             help="Starts <campaign>. <campaign> is the campaign name.")
		start_uh.add_option("--start-dev-map", dest="start_dev_map", action="store_true",
		             default=False, help="Starts the development map without displaying the main menu.")
		start_uh.add_option("--load-map", dest="load_map", metavar="<save>",
		             help="Loads a saved game. <save> is the savegamename.")
		start_uh.add_option("--load-last-quicksave", dest="load_quicksave", action="store_true",
		             help="Loads the last quicksave.")
		p.add_option_group(start_uh)

		ai_group = optparse.OptionGroup(p, "AI options")
		ai_group.add_option("--ai-players", dest="ai_players", metavar="<ai_players>",
		             type="int", default=0,
		             help="Uses <ai_players> AI players (excludes the possible human-AI hybrid; defaults to 0).")
		ai_group.add_option("--human-ai-hybrid", dest="human_ai", action="store_true",
		             help="Makes the human player a human-AI hybrid (for development only).")
		ai_group.add_option("--force-player-id", dest="force_player_id",
		             metavar="<force_player_id>", type="int", default=None,
		             help="Set the player with id <force_player_id> as the active (human) player.")
		ai_group.add_option("--ai-highlights", dest="ai_highlights", action="store_true",
		             help="Shows AI plans as highlights (for development only).")
		ai_group.add_option("--ai-combat-highlights", dest="ai_combat_highlights", action="store_true",
		             help="Highlights combat ranges for units controlled by AI Players (for development only).")
		p.add_option_group(ai_group)

		dev_group = optparse.OptionGroup(p, "Development options")
		dev_group.add_option("--debug-log-only", dest="debug_log_only", action="store_true",
		             default=False, help="Write debug output only to logfile, not to console. Implies -d.")
		dev_group.add_option("--debug-module", action="append", dest="debug_module",
		             metavar="<module>", default=[],
		             help="Enable logging for a certain logging module (for developing only).")
		dev_group.add_option("--logfile", dest="logfile", metavar="<filename>",
		             help="Writes log to <filename> instead of to the uh-userdir")
		dev_group.add_option("--fife-in-library-path", dest="fife_in_library_path", action="store_true",
		             default=False, help="For internal use only.")
		dev_group.add_option("--profile", dest="profile", action="store_true",
		             default=False, help="Enable profiling (for developing only).")
		dev_group.add_option("--max-ticks", dest="max_ticks", metavar="<max_ticks>", type="int",
		             help="Run the game for <max_ticks> ticks.")
		dev_group.add_option("--string-previewer", dest="stringpreview", action="store_true",
		             default=False, help="Enable the string previewer tool for scenario writers")
		dev_group.add_option("--game-speed", dest="gamespeed", metavar="<game_speed>", type="float",
		             help="Run the game in the given speed (Values: 0.5, 1, 2, 3, 4, 6, 8, 11, 20)")
		dev_group.add_option("--gui-test", dest="gui_test", metavar="<test>",
		             default=False, help="INTERNAL. Use run_tests.py instead.")
		dev_group.add_option("--gui-log", dest="log_gui", action="store_true",
		             default=False, help="Log gui interactions")
		dev_group.add_option("--sp-seed", dest="sp_seed", metavar="<seed>", type="int",
		             help="Use this seed for singleplayer sessions.")
		dev_group.add_option("--generate-minimap", dest="generate_minimap",
		             metavar="<parameters>", help="Generate a minimap for a map")
		dev_group.add_option("--create-mp-game", action="store_true", dest="create_mp_game",
		             help="Create an multiplayer game with default settings.")
		dev_group.add_option("--join-mp-game", action="store_true", dest="join_mp_game",
		             help="Join first multiplayer game.")
		dev_group.add_option("--interactive-shell", action="store_true", dest="interactive_shell",
		             help="Starts an IPython kernel. Connect to the shell with: ipython console --existing")
		p.add_option_group(dev_group)

		return p
