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

import horizons.main

from horizons.util import Callback, random_map
from horizons.savegamemanager import SavegameManager
from horizons.gui.modules import AIDataSelection, PlayerDataSelection
from horizons.constants import AI
from horizons.gui.widgets.minimap import Minimap

class SingleplayerMenu(object):
	def show_single(self, show = 'scenario'): # tutorial
		"""
		@param show: string, which type of games to show
		"""
		# save player name before removing playerdata container
		self._save_player_name()
		self.hide()

		# start with default single player settings
		self.widgets.reload('singleplayermenu')
		self._switch_current_widget('singleplayermenu', center=True)
		self.activeRightSide = None

		for spShow in ('random', 'scenario', 'campaign', 'free_maps'):
			self.widgets.reload('sp_%s' % spShow)
			right_side = self.widgets['sp_%s' % spShow]
			self.current.findChild(name="right_side_box").addChild(right_side)
			right_side.parent.hideChild(right_side)

		# create and add permanent left side widgets
		self.current.playerdata = PlayerDataSelection(self.current, self.widgets)
		self.current.aidata = AIDataSelection(self.current, self.widgets)

		show = "free_maps"
		self.__select_single(show)

	def __select_single(self, show):
		assert show in ('random', 'scenario', 'campaign', 'free_maps')
		self.hide()
		eventMap = {
			'cancel'    : Callback.ChainedCallbacks(self._save_player_name, self.show_main),
			'okay'      : self.start_single,
			'scenario'  : Callback(self.__select_single, show='scenario'),
			'campaign'  : Callback(self.__select_single, show='campaign'),
			'random'    : Callback(self.__select_single, show='random'),
			'free_maps' : Callback(self.__select_single, show='free_maps')
		}

		# init gui for subcategory
		del eventMap[show]
		right_side = self.widgets['sp_%s' % show]
		show_ai_options = False
		self.current.findChild(name=show).marked = True
		self.current.aidata.hide()

		# hide previous widget, unhide new right side widget
		if self.activeRightSide is not None:
			self.activeRightSide.parent.hideChild(self.activeRightSide)
		right_side.parent.showChild(right_side)
		self.activeRightSide = right_side

		if show == 'random':
			show_ai_options = True
			self.__setup_random_map_selection(right_side)
			self.__setup_game_settings_selection()
		elif show == 'free_maps':
			self.current.files, maps_display = SavegameManager.get_maps()

			self.current.distributeInitialData({ 'maplist' : maps_display, })
			def _update_infos():
				number_of_players = SavegameManager.get_recommended_number_of_players( self.__get_selected_map() )
				#xgettext:python-format
				self.current.findChild(name="recommended_number_of_players_lbl").text = \
				    _("Recommended number of players: {number}").format(number=number_of_players)
				from fife import fife
				minimap_icon = self.current.findChild(name="map_preview_minimap")
				"""
				from horizons.world import World
				from horizons.util import SavegameAccessor, WorldObject, Rect, Point
				WorldObject.reset()
				world = World(session=None)
				world.inited = True
				world.load_raw_map( SavegameAccessor( self.__get_selected_map() ), preview=True )
				if hasattr(self, "minimap"):
					self.minimap.end()
				r = Rect.init_from_topleft_and_size(0,0,200,200)
				from fife import fife
				#rend = fife.OffRenderer( horizons.main.fife.engine.getRenderBackend() )
				rend = horizons.main.fife.engine.getOffRenderer()
				print rend.isEnabled()
				rend.setEnable(True)
				print rend.isEnabled()
				self.minimap = Minimap(r,
				                  session=None,
				                  view=None,
				                  world=world,
				                  renderer=rend,
				                  targetrenderer=horizons.main.fife.targetrenderer,
				                  imagemanager=horizons.main.fife.imagemanager,
				                  cam_border=False,
				                  use_rotation=False,
				                  preview=True)
				self.minimap.draw()
				"""
				targetrenderer=horizons.main.fife.targetrenderer

				imgman = horizons.main.fife.imagemanager
				img = imgman.loadBlank(100,100)

				rt = targetrenderer.createRenderTarget( img )
				targetrenderer.setRenderTarget( rt.getTarget().getName(), False, 0 )

				rt.addQuad( "foo",
		                           fife.Point(0,0),
		                           fife.Point(0, 100),
		                           fife.Point(100, 100),
		                           fife.Point(100, 0),
		                           255,0,0)
				rt.addLine("bar", fife.Point(10,10), fife.Point(10,50), 0, 255, 0)


				#img = imgman.load('content/gui/images/cursors/cursor_pipette.png')
				minimap_icon.image = fife.GuiImage(img)
				print 'yay'


			if len(maps_display) > 0:
				# select first entry
				self.current.distributeData({ 'maplist' : 0, })
				_update_infos()
			self.current.findChild(name="maplist").capture(_update_infos)
			show_ai_options = True
			self.__setup_game_settings_selection()
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
						except InvalidScenarioFileFormat as e:
							self.__show_invalid_scenario_file_popup(e)
							return
						self.current.findChild(name="map_difficulty").text = \
						        _("Difficulty: {difficulty}").format(difficulty=difficulty) #xgettext:python-format
						self.current.findChild(name="map_author").text = \
						        _("Author: {author}").format(author=author) #xgettext:python-format
						self.current.findChild(name="map_desc").text = \
						        _("Description: {desc}").format(desc=desc) #xgettext:python-format
						#self.current.findChild(name="map_desc").parent.adaptLayout()
				elif show == 'campaign': # update infos for campaign
					def _update_infos():
						"""Fill in infos of selected campaign to label"""
						campaign_info = SavegameManager.get_campaign_info(filename = self.__get_selected_map())
						if not campaign_info:
							# TODO : an "invalid campaign popup"
							self.__show_invalid_scenario_file_popup(e)
							return
						self.current.findChild(name="map_difficulty").text = \
						        _("Difficulty: {difficulty}").format(difficulty=campaign_info.get('difficulty', '')) #xgettext:python-format
						self.current.findChild(name="map_author").text = \
						        _("Author: {author}").format(author=campaign_info.get('author', '')) #xgettext:python-format
						self.current.findChild(name="map_desc").text = \
						        _("Description: {desc}").format(desc=campaign_info.get('description', '')) #xgettext:python-format

				self.current.findChild(name="maplist").capture(_update_infos)
				_update_infos()


		self.current.mapEvents(eventMap)

		if show_ai_options:
			self.current.aidata.show()
		self.current.show()
		self.on_escape = self.show_main

	def start_single(self):
		""" Starts a single player horizons. """
		assert self.current is self.widgets['singleplayermenu']
		playername = self.current.playerdata.get_player_name()
		if len(playername) == 0:
			self.show_popup(_("Invalid player name"), _("You entered an invalid playername."))
			return
		playercolor = self.current.playerdata.get_player_color()
		self._save_player_name()

		if self.current.collectData('random'):
			map_file = self.__get_random_map_file()
		else:
			assert self.current.collectData('maplist') != -1
			map_file = self.__get_selected_map()

		is_scenario = bool(self.current.collectData('scenario'))
		is_campaign = bool(self.current.collectData('campaign'))
		if not is_scenario and not is_campaign:
			ai_players = int(self.current.aidata.get_ai_players())
			horizons.main.fife.set_uh_setting("AIPlayers", ai_players)
		horizons.main.fife.save_settings()

		self.show_loading_screen()
		if is_scenario:
			from horizons.scenario import InvalidScenarioFileFormat
			try:
				horizons.main.start_singleplayer(map_file, playername, playercolor, is_scenario=is_scenario)
			except InvalidScenarioFileFormat as e:
				self.__show_invalid_scenario_file_popup(e)
				self.__select_single(show = 'scenario')
		elif is_campaign:
			campaign_info = SavegameManager.get_campaign_info(filename = map_file)
			if not campaign_info:
				# TODO : an "invalid campaign popup"
				self.__show_invalid_scenario_file_popup(e)
				self.__select_single(show = 'campaign')
			scenario = campaign_info.get('scenarios')[0].get('level')
			map_file = campaign_info.get('scenario_files').get(scenario)
			# TODO : why this does not work ?
			#
			#	horizons.main.start_singleplayer(map_file, playername, playercolor, is_scenario = True, campaign = {
			#		'campaign_name': campaign_info.get('codename'), 'scenario_index': 0, 'scenario_name': scenario
			#		})
			#
			horizons.main._start_map(scenario, ai_players=0, human_ai=False, is_scenario=True, campaign={
				'campaign_name': campaign_info.get('codename'), 'scenario_index': 0, 'scenario_name': scenario
				})
		else: # free play/random map
			horizons.main.start_singleplayer(map_file, playername, playercolor, ai_players = ai_players, \
				human_ai = AI.HUMAN_AI, trader_enabled = self.widgets['game_settings'].findChild(name = 'free_trader').marked, \
				pirate_enabled = self.widgets['game_settings'].findChild(name = 'pirates').marked, \
				natural_resource_multiplier = self.__get_natural_resource_multiplier())

	# random map options
	map_sizes = [50, 100, 150, 200, 250]
	water_percents = [20, 30, 40, 50, 60, 70, 80]
	island_sizes = [30, 40, 50, 60, 70]
	island_size_deviations = [5, 10, 20, 30, 40]

	def __setup_random_map_selection(self, widget):
		map_size_slider = widget.findChild(name = 'map_size_slider')
		def on_map_size_slider_change():
			widget.findChild(name = 'map_size_lbl').text = _('Map size:') + u' ' + \
				unicode(self.map_sizes[int(map_size_slider.value)])
			horizons.main.fife.set_uh_setting("RandomMapSize", map_size_slider.value)
			horizons.main.fife.save_settings()
		map_size_slider.capture(on_map_size_slider_change)
		map_size_slider.value = horizons.main.fife.get_uh_setting("RandomMapSize")

		water_percent_slider = widget.findChild(name = 'water_percent_slider')
		def on_water_percent_slider_change():
			widget.findChild(name = 'water_percent_lbl').text = _('Water:') + u' ' + \
				unicode(self.water_percents[int(water_percent_slider.value)]) + u'%'
			horizons.main.fife.set_uh_setting("RandomMapWaterPercent", water_percent_slider.value)
		water_percent_slider.capture(on_water_percent_slider_change)
		water_percent_slider.value = horizons.main.fife.get_uh_setting("RandomMapWaterPercent")

		max_island_size_slider = widget.findChild(name = 'max_island_size_slider')
		def on_max_island_size_slider_change():
			widget.findChild(name = 'max_island_size_lbl').text = _('Max island size:') + u' ' + \
				unicode(self.island_sizes[int(max_island_size_slider.value)])
			horizons.main.fife.set_uh_setting("RandomMapMaxIslandSize", max_island_size_slider.value)
		max_island_size_slider.capture(on_max_island_size_slider_change)
		max_island_size_slider.value = horizons.main.fife.get_uh_setting("RandomMapMaxIslandSize")

		preferred_island_size_slider = widget.findChild(name = 'preferred_island_size_slider')
		def on_preferred_island_size_slider_change():
			widget.findChild(name = 'preferred_island_size_lbl').text = _('Preferred island size:') + u' ' + \
				unicode(self.island_sizes[int(preferred_island_size_slider.value)])
			horizons.main.fife.set_uh_setting("RandomMapPreferredIslandSize", preferred_island_size_slider.value)
		preferred_island_size_slider.capture(on_preferred_island_size_slider_change)
		preferred_island_size_slider.value = horizons.main.fife.get_uh_setting("RandomMapPreferredIslandSize")

		island_size_deviation_slider = widget.findChild(name = 'island_size_deviation_slider')
		def on_island_size_deviation_slider_change():
			widget.findChild(name = 'island_size_deviation_lbl').text = _('Island size deviation:') + u' ' + \
				unicode(self.island_size_deviations[int(island_size_deviation_slider.value)])
			horizons.main.fife.set_uh_setting("RandomMapIslandSizeDeviation", island_size_deviation_slider.value)
		island_size_deviation_slider.capture(on_island_size_deviation_slider_change)
		island_size_deviation_slider.value = horizons.main.fife.get_uh_setting("RandomMapIslandSizeDeviation")

		on_map_size_slider_change()
		on_water_percent_slider_change()
		on_max_island_size_slider_change()
		on_preferred_island_size_slider_change()
		on_island_size_deviation_slider_change()

	# game options
	resource_densities = [0.5, 0.7, 1, 1.4, 2]

	def __setup_game_settings_selection(self):
		widget = self.widgets['game_settings']
		if widget.parent is not None:
			widget.parent.removeChild(widget)
		self.current.findChild(name = 'game_settings_box').addChild(widget)

		resource_density_slider = widget.findChild(name = 'resource_density_slider')
		def on_resource_density_slider_change():
			widget.findChild(name = 'resource_density_lbl').text = _('Resource density:') + u' ' + \
				unicode(self.resource_densities[int(resource_density_slider.value)]) + u'x'
			horizons.main.fife.set_uh_setting("MapResourceDensity", resource_density_slider.value)
		resource_density_slider.capture(on_resource_density_slider_change)
		resource_density_slider.value = horizons.main.fife.get_uh_setting("MapResourceDensity")

		on_resource_density_slider_change()

	def __get_random_map_file(self):
		map_size = self.map_sizes[int(self.current.findChild(name = 'map_size_slider').value)]
		water_percent = self.water_percents[int(self.current.findChild(name = 'water_percent_slider').value)]
		max_island_size = self.island_sizes[int(self.current.findChild(name = 'max_island_size_slider').value)]
		preferred_island_size = self.island_sizes[int(self.current.findChild(name = 'preferred_island_size_slider').value)]
		island_size_deviation = self.island_size_deviations[int(self.current.findChild(name = 'island_size_deviation_slider').value)]
		return random_map.generate_map(None, map_size, water_percent, max_island_size, preferred_island_size, island_size_deviation)

	def __get_natural_resource_multiplier(self):
		return self.resource_densities[int(self.widgets['game_settings'].findChild(name = 'resource_density_slider').value)]

	def __get_selected_map(self):
		"""Returns map file, that is selected in the maplist widget"""
		return self.current.files[ self.current.collectData('maplist') ]

	def __show_invalid_scenario_file_popup(self, exception):
		"""Shows a popup complaining about invalid scenario file.
		@param exception: InvalidScenarioFile exception instance"""
		print "Error: ", unicode(str(exception))
		self.show_error_popup(_("Invalid scenario file"), \
		                description=_("The selected file is not a valid scenario file."),
		                details=_("Error message:") + u' ' + unicode(str(exception)),
		                advice=_("Please report this to the author."))

	def _save_player_name(self):
		if hasattr(self.current, 'playerdata'):
			playername = self.current.playerdata.get_player_name()
			horizons.main.fife.set_uh_setting("Nickname", playername)
