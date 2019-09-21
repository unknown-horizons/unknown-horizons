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

from operator import itemgetter

import horizons.globals
from horizons.constants import AI, COLORS
from horizons.util.color import Color
from horizons.util.difficultysettings import DifficultySettings


class StartGameOptions:

	def __init__(self, game_identifier):
		super().__init__() # TODO: check if this call is needed
		self.game_identifier = game_identifier
		self._player_list = None

		self.trader_enabled = True
		self.pirate_enabled = True
		self.natural_resource_multiplier = 1
		self.disasters_enabled = True
		self.force_player_id = None
		self.is_map = False
		self.is_multiplayer = False
		self.is_scenario = False

		self.player_name = 'Player'
		self.player_color = None
		self.ai_players = 0
		self.human_ai = AI.HUMAN_AI

		# this is used by the map editor to pass along the new map's size
		self.map_padding = None
		self.is_editor = False

	def init_new_world(self, session):
		# NOTE: this must be sorted before iteration, cause there is no defined order for
		#       iterating a dict, and it must happen in the same order for mp games.
		for i in sorted(self._get_player_list(), key=itemgetter('id')):
			session.world.setup_player(i['id'], i['name'], i['color'], i['clientid'] if self.is_multiplayer else None, i['local'], i['ai'], i['difficulty'])
		session.world.set_forced_player(self.force_player_id)
		center = session.world.init_new_world(self.trader_enabled, self.pirate_enabled, self.natural_resource_multiplier)
		session.view.center(center[0], center[1])

	def set_human_data(self, player_name, player_color):
		self.player_name = player_name
		self.player_color = player_color

	def _get_player_list(self):
		if self._player_list is not None:
			return self._player_list

		# for now just make it a bit easier for the AI
		difficulty_level = {False: DifficultySettings.DEFAULT_LEVEL, True: DifficultySettings.EASY_LEVEL}

		players = []
		players.append({
			'id': 1,
			'name': self.player_name,
			'color': Color.get(1) if self.player_color is None else self.player_color,
			'local': True,
			'ai': self.human_ai,
			'difficulty': difficulty_level[bool(self.human_ai)],
		})

		cur_locale = horizons.globals.fife.get_locale()

		# add AI players with a distinct color; if none can be found then use black
		for num in range(self.ai_players):
			color = Color.get(COLORS.BLACK) # if none can be found then be black
			for possible_color in Color.get_defaults():
				if possible_color == Color.get(COLORS.BLACK):
					continue # black is used by the trader and the pirate
				used = any(possible_color == player['color'] for player in players)
				if not used:
					color = possible_color
					break

			name = horizons.globals.db.get_random_ai_name(cur_locale, [p['name'] for p in players])
			# out of pre-defined names?
			if name is None:
				name = 'AI' + str(num + 1)

			players.append({
				'id': num + 2,
				'name': name,
				'color': color,
				'local': False,
				'ai': True,
				'difficulty': difficulty_level[True],
			})
		return players

	@classmethod
	def create_start_multiplayer(cls, game_file, player_list, is_map):
		options = StartGameOptions(game_file)
		options._player_list = player_list
		options.is_map = is_map
		options.is_multiplayer = True
		return options

	@classmethod
	def create_start_singleplayer(cls, game_identifier, is_scenario, ai_players,
		                          trader_enabled, pirate_enabled, force_player_id, is_map):
		options = StartGameOptions(game_identifier)
		options.is_scenario = is_scenario
		options.ai_players = ai_players
		options.trader_enabled = trader_enabled
		options.pirate_enabled = pirate_enabled
		options.force_player_id = force_player_id
		options.is_map = is_map
		return options

	@classmethod
	def create_start_random_map(cls, ai_players, seed, force_player_id):
		from horizons.util.random_map import generate_map_from_seed
		options = StartGameOptions(generate_map_from_seed(seed))
		options.ai_players = ai_players
		options.force_player_id = force_player_id
		options.is_map = True
		return options

	@classmethod
	def create_editor_load(cls, map_name):
		options = StartGameOptions(map_name)
		options.player_name = 'Editor'
		options.trader_enabled = False
		options.pirate_enabled = False
		options.natural_resource_multiplier = 0
		options.disasters_enabled = False
		options.is_map = True
		options.is_editor = True
		return options

	@classmethod
	def create_start_scenario(cls, scenario_file):
		options = StartGameOptions(scenario_file)
		options.is_scenario = True
		return options

	@classmethod
	def create_start_map(cls, map_name):
		options = StartGameOptions(map_name)
		options.is_map = True
		return options

	@classmethod
	def create_load_game(cls, saved_game, force_player_id):
		options = StartGameOptions(saved_game)
		options.force_player_id = force_player_id
		return options

	@classmethod
	def create_game_test(cls, game_identifier, player_list):
		options = StartGameOptions(game_identifier)
		options._player_list = player_list
		options.trader_enabled = False
		options.pirate_enabled = False
		options.natural_resource_multiplier = 0
		return options

	@classmethod
	def create_ai_test(cls, game_identifier, player_list):
		options = StartGameOptions(game_identifier)
		options._player_list = player_list
		options.is_map = True
		return options
