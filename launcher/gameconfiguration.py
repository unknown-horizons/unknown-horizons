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

class GameConfiguration(object):
	def __init__(self, map_file, playername="Player", player_color_tuple=None, is_scenario=False,
				campaign=None, ai_players=0, human_ai=False, trader_enabled=True,
				pirate_enabled=True, natural_resource_multiplier=1, force_player_id=None,
				disasters_enabled=True):
		self.map_file = map_file
		self.playername = playername
		self.player_color_tuple = player_color_tuple
		self.is_scenario = is_scenario
		self.campaign = campaign
		self.ai_players = ai_players
		self.human_ai = human_ai
		self.trader_enabled = trader_enabled
		self.pirate_enabled = pirate_enabled
		self.natural_resource_multiplier = natural_resource_multiplier
		self.force_player_id = force_player_id
		self.disasters_enabled = disasters_enabled

	@classmethod
	def create_scenario(cls, map_file, playername, playercolor):
		return GameConfiguration(map_file, playername, playercolor, is_scenario=True)

	@classmethod
	def create_normal(cls, map_file, playername, player_color_tuple, ai_players, human_ai,
					  trader_enabled, pirate_enabled, disasters_enabled,
					  natural_resource_multiplier):
		return GameConfiguration(map_file, playername, player_color_tuple, ai_players=ai_players,
								 human_ai=human_ai, trader_enabled=trader_enabled,
								 pirate_enabled=pirate_enabled,
								 disasters_enabled=disasters_enabled,
								 natural_resource_multiplier=natural_resource_multiplier)

	@classmethod
	def create_loader(cls, savegame, is_scenario, campaign, ai_players, human_ai,
					pirate_enabled, trader_enabled, force_player_id):
		return GameConfiguration(savegame, is_scenario=is_scenario, campaign=campaign,
								 ai_players=ai_players, human_ai=human_ai,
								 trader_enabled=trader_enabled,
								 pirate_enabled=pirate_enabled,
								 force_player_id=force_player_id)
