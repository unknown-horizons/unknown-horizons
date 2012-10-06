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

from horizons.constants import AI

class StartGameOptions(object):
	def __init__(self, savegame):
		self.trader_enabled = True
		self.pirate_enabled = True
		self.natural_resource_multiplier = 1
		self.disasters_enabled = True
		self.force_player_id = None
		self.is_map = False
		self.is_multiplayer = False
		self.is_scenario = False
		self.campaign = None
		self.players = None

		self.savegame = savegame
		self.player_name = 'Player'
		self.player_color = None
		self.ai_players = 0
		self.human_ai = AI.HUMAN_AI

	def init_new_world(self, session):
		# NOTE: this must be sorted before iteration, cause there is no defined order for
		#       iterating a dict, and it must happen in the same order for mp games.
		for i in sorted(self.players, lambda p1, p2: cmp(p1['id'], p2['id'])):
			session.world.setup_player(i['id'], i['name'], i['color'], i['clientid'] if self.is_multiplayer else None, i['local'], i['ai'], i['difficulty'])
		session.world.set_forced_player(self.force_player_id)
		center = session.world.init_new_world(self.trader_enabled, self.pirate_enabled, self.natural_resource_multiplier)
		session.view.center(center[0], center[1])

	def set_human_data(self, player_name, player_color):
		self.player_name = player_name
		self.player_color = player_color

	@classmethod
	def create(cls, savegame, players, trader_enabled, pirate_enabled,
	           natural_resource_multiplier, is_scenario=False, campaign=None,
	           force_player_id=None, disasters_enabled=True, is_multiplayer=False,
	           is_map=False):
		options = StartGameOptions(savegame)
		options.players = players
		options.trader_enabled = trader_enabled
		options.pirate_enabled = pirate_enabled
		options.natural_resource_multiplier = natural_resource_multiplier
		options.is_scenario = is_scenario
		options.campaign = campaign
		options.force_player_id = force_player_id
		options.disasters_enabled = disasters_enabled
		options.is_multiplayer = is_multiplayer
		options.is_map = is_map
		return options

	@classmethod
	def create_start_singleplayer(cls, map_file, playername='Player', playercolor=None,
	                              is_scenario=False, campaign=None, ai_players=0,
	                              human_ai=False, trader_enabled=True, pirate_enabled=True,
	                              natural_resource_multiplier=1, force_player_id=None,
	                              disasters_enabled=True, is_map=False):
		options = StartGameOptions(map_file)
		options.player_name = playername
		options.player_color = playercolor
		options.is_scenario = is_scenario
		options.campaign = campaign
		options.ai_players = ai_players
		options.human_ai = human_ai
		options.trader_enabled = trader_enabled
		options.pirate_enabled = pirate_enabled
		options.natural_resource_multiplier = natural_resource_multiplier
		options.force_player_id = force_player_id
		options.disasters_enabled = disasters_enabled
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
		return options

	@classmethod
	def create_start_scenario(cls, scenario_file, player_name, player_color):
		options = StartGameOptions(scenario_file)
		options.player_name = player_name
		options.player_color = player_color
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
