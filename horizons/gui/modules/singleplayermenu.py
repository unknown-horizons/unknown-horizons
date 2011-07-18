# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

import horizons.main

from horizons.util import Callback, random_map
from horizons.savegamemanager import SavegameManager
from horizons.gui.modules import PlayerDataSelection

class SingleplayerMenu(object):
	def show_single(self, show = 'scenario'): # tutorial
		"""
		@param show: string, which type of games to show
		"""
		assert show in ('random', 'scenario', 'campaign', 'free_maps')
		self.hide()
		# reload since the gui is changed at runtime
		self.widgets.reload('singleplayermenu')
		self._switch_current_widget('singleplayermenu', center=True)
		eventMap = {
			'cancel'    : self.show_main,
			'okay'      : self.start_single,
			'scenario'  : Callback(self.show_single, show='scenario'),
			'campaign'  : Callback(self.show_single, show='campaign'),
			'random'    : Callback(self.show_single, show='random'),
			'free_maps' : Callback(self.show_single, show='free_maps')
		}


		# init gui for subcategory
		del eventMap[show]
		self.current.findChild(name=show).marked = True
		right_side = self.widgets['sp_%s' % show]
		self.current.findChild(name="right_side_box").addChild(right_side)
		if show == 'random':
			game_settings = self.widgets['game_settings']
			self.current.findChild(name="game_settings_box").addChild(game_settings)
		elif show == 'free_maps':
			self.current.files, maps_display = SavegameManager.get_maps()
			game_settings = self.widgets['game_settings']
			self.current.findChild(name="game_settings_box").addChild(game_settings)
			self.current.distributeInitialData({ 'maplist' : maps_display, })
			if len(maps_display) > 0:
				# select first entry
				self.current.distributeData({ 'maplist' : 0, })
		else:
			choosable_locales = ['en', horizons.main.fife.get_locale()]
			if show == 'campaign':
				self.current.files, maps_display = SavegameManager.get_campaigns()
				# tell people that we don't have any content
				text = u"We currently don't have any campaigns available for you. " + \
				u"If you are interested in adding campaigns to Unknown Horizons, " + \
				u"please contact us via our website (http://www.unknown-horizons.org)!"
				self.show_popup("No campaigns available yet", text)
			elif show == 'scenario':
				self.current.files, maps_display = SavegameManager.get_available_scenarios(locales = choosable_locales)

			# get the map files and their display names
			self.current.distributeInitialData({ 'maplist' : maps_display, })
			if len(maps_display) > 0:
				# select first entry
				self.current.distributeData({ 'maplist' : 0, })

				if show == 'scenario': # update infos for scenario
					from horizons.scenario import ScenarioEventHandler, InvalidScenarioFileFormat
					def _update_infos():
						"""Fill in infos of selected scenario to label"""
						try:
							difficulty = ScenarioEventHandler.get_difficulty_from_file( self.__get_selected_map() )
							desc = ScenarioEventHandler.get_description_from_file( self.__get_selected_map() )
							author = ScenarioEventHandler.get_author_from_file( self.__get_selected_map() )
						except InvalidScenarioFileFormat, e:
							self.__show_invalid_scenario_file_popup(e)
							return
						self.current.findChild(name="map_difficulty").text = _("Difficulty: ") + unicode( difficulty )
						self.current.findChild(name="map_author").text = _("Author: ") + unicode( author )
						self.current.findChild(name="map_desc").text =  _("Description: ") + unicode( desc )
						#self.current.findChild(name="map_desc").parent.adaptLayout()
				elif show == 'campaign': # update infos for campaign
					def _update_infos():
						"""Fill in infos of selected campaign to label"""
						campaign_info = SavegameManager.get_campaign_info(filename = self.__get_selected_map())
						if not campaign_info:
							# TODO : an "invalid campaign popup"
							self.__show_invalid_scenario_file_popup(e)
							return
						self.current.findChild(name="map_difficulty").text = _("Difficulty: ") + unicode(campaign_info.get('difficulty', ''))
						self.current.findChild(name="map_author").text = _("Author: ") + unicode(campaign_info.get('author', ''))
						self.current.findChild(name="map_desc").text = _("Description: ") + unicode(campaign_info.get('description', ''))

				self.current.findChild(name="maplist").capture(_update_infos)
				_update_infos()


		self.current.mapEvents(eventMap)

		self.current.playerdata = PlayerDataSelection(self.current, self.widgets)
		self.current.show()
		self.on_escape = self.show_main

	def start_single(self):
		""" Starts a single player horizons. """
		assert self.current is self.widgets['singleplayermenu']
		playername = self.current.playerdata.get_player_name()
		if len(playername) == 0:
			self.show_popup(_("Invalid player name"), _("You entered an invalid playername"))
			return
		playercolor = self.current.playerdata.get_player_color()
		horizons.main.fife.set_uh_setting("Nickname", playername)
		horizons.main.fife.save_settings()

		if self.current.collectData('random'):
			map_file = random_map.generate_map()
		else:
			assert self.current.collectData('maplist') != -1
			map_file = self.__get_selected_map()

		is_scenario = bool(self.current.collectData('scenario'))
		is_campaign = bool(self.current.collectData('campaign'))
		self.show_loading_screen()
		if is_scenario:
			from horizons.scenario import InvalidScenarioFileFormat
			try:
				horizons.main.start_singleplayer(map_file, playername, playercolor, is_scenario=is_scenario)
			except InvalidScenarioFileFormat, e:
				self.__show_invalid_scenario_file_popup(e)
				self.show_single(show = 'scenario')
		elif is_campaign:
			campaign_info = SavegameManager.get_campaign_info(filename = map_file)
			if not campaign_info:
				# TODO : an "invalid campaign popup"
				self.__show_invalid_scenario_file_popup(e)
				self.show_single(show = 'campaign')
			scenario = campaign_info.get('scenarios')[0].get('level')
			map_file = campaign_info.get('scenario_files').get(scenario)
			# TODO : why this does not work ?
			#
			#	horizons.main.start_singleplayer(map_file, playername, playercolor, is_scenario = True, campaign = {
			#		'campaign_name': campaign_info.get('codename'), 'scenario_index': 0, 'scenario_name': scenario
			#		})
			#
			horizons.main._start_map(scenario, is_scenario = True, campaign = {
				'campaign_name': campaign_info.get('codename'), 'scenario_index': 0, 'scenario_name': scenario
				})
		else: # free play/random map
			horizons.main.start_singleplayer(map_file, playername, playercolor)

	def __get_selected_map(self):
		"""Returns map file, that is selected in the maplist widget"""
		return self.current.files[ self.current.collectData('maplist') ]


	def __show_invalid_scenario_file_popup(self, exception):
		"""Shows a popup complaining about invalid scenario file.
		@param exception: InvalidScenarioFile exception instance"""
		print "Error: ", unicode(str(exception))
		self.show_popup(_("Invalid scenario file"), \
		                _("The selected file is not a valid scenario file.\nError message: ") + \
		                unicode(str(exception)) + _("\nPlease report this to the author."))

