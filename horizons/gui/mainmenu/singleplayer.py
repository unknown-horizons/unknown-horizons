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

import json
import subprocess
import sys
import tempfile
import os
import locale

import horizons.globals
import horizons.main

from horizons.extscheduler import ExtScheduler
from horizons.savegamemanager import SavegameManager
from horizons.gui.mainmenu.aidataselection import AIDataSelection
from horizons.gui.mainmenu.playerdataselection import PlayerDataSelection
from horizons.constants import AI, LANGUAGENAMES
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.window import Window
from horizons.world import World
from horizons.util.python.callback import Callback
from horizons.util.random_map import generate_random_map, generate_random_seed
from horizons.util.savegameaccessor import SavegameAccessor
from horizons.util.shapes import Rect
from horizons.util.startgameoptions import StartGameOptions
from horizons.util.worldobject import WorldObject
from horizons.util.yamlcache import YamlCache
from horizons.i18n import find_available_languages
from horizons.scenario import ScenarioEventHandler, InvalidScenarioFileFormat


class SingleplayerMenu(Window):

	# game options
	resource_densities = [0.5, 0.7, 1, 1.4, 2]

	def show(self, show='scenario'): # show scenarios to highlight tutorials
		"""
		@param show: string, which type of games to show
		"""
		# save player name before removing playerdata container
		self._save_player_name()

		# start with default single player settings
		self._widget_loader.reload('singleplayermenu')
		self._widget = self._widget_loader['singleplayermenu']

		self.active_right_side = None

		for mode in ('random', 'scenario', 'campaign', 'free_maps'):
			self._widget_loader.reload('sp_%s' % mode)
			right_side = self._widget_loader['sp_%s' % mode]
			self._widget.findChild(name="right_side_box").addChild(right_side)
			right_side.parent.hideChild(right_side)

		# create and add permanent left side widgets
		self._playerdata = PlayerDataSelection(self._widget, self._widget_loader)
		self._aidata = AIDataSelection(self._widget, self._widget_loader)

		self.map_preview = MapPreview(lambda: self._widget)

		self._select_single(show)

	def hide(self):
		self._widget.hide()

	def on_escape(self):
		self._save_player_name()
		self.windows.close()

	def _select_single(self, show):
		assert show in ('random', 'scenario', 'campaign', 'free_maps')

		self._widget.hide()

		event_map = {
			# TODO get rid of the call to show main, someone else should be clever enough to figure out what
			# the last menu/dialog was
			'cancel'    : self.on_escape,
			'okay'      : self.start_single,
			'scenario'  : Callback(self._select_single, show='scenario'),
			'campaign'  : Callback(self._select_single, show='campaign'),
			'random'    : Callback(self._select_single, show='random'),
			'free_maps' : Callback(self._select_single, show='free_maps')
		}
		self._widget.mapEvents(event_map)
		self._capture_escape(self._widget)

		# init gui for subcategory
		right_side = self._widget_loader['sp_%s' % show]
		self._widget.findChild(name=show).marked = True
		self._aidata.hide()

		# hide previous widget, unhide new right side widget
		if self.active_right_side is not None:
			self.active_right_side.parent.hideChild(self.active_right_side)
		right_side.parent.showChild(right_side)
		self.active_right_side = right_side

		if show == 'random':
			self._setup_random_map_selection(right_side)
			self._setup_game_settings_selection()
			self._on_random_map_parameter_changed()
			self.active_right_side.findChild(name="open_random_map_archive").capture(self._open_random_map_archive)
			self._aidata.show()

		elif show == 'free_maps':
			self._files, maps_display = SavegameManager.get_maps()

			self.active_right_side.distributeInitialData({ 'maplist' : maps_display, })
			# update preview whenever something is selected in the list
			self.active_right_side.mapEvents({
			  'maplist/action': self._update_free_map_infos,
			})
			self._setup_game_settings_selection()
			if maps_display: # select first entry
				self.active_right_side.distributeData({'maplist': 0})
			self._aidata.show()
			self._update_free_map_infos()

		elif show == 'campaign':
			# tell people that we don't have any content
			text = u"We currently don't have any campaigns available for you. " + \
				u"If you are interested in adding campaigns to Unknown Horizons, " + \
				u"please contact us via our website (http://www.unknown-horizons.org)!"
			self.windows.show_popup("No campaigns available yet", text)

			self._files, maps_display = SavegameManager.get_campaigns()
			self.active_right_side.distributeInitialData({ 'maplist' : maps_display, })
			self.active_right_side.mapEvents({
				'maplist/action': self._update_campaign_infos
			})
			if maps_display: # select first entry
				self.active_right_side.distributeData({'maplist': 0})
			self._update_campaign_infos()

		elif show == 'scenario':
			self._files, maps_display = SavegameManager.get_available_scenarios(hide_test_scenarios=True)
			# get the map files and their display names. display tutorials on top.
			prefer_tutorial = lambda x : ('tutorial' not in x, x)
			maps_display.sort(key=prefer_tutorial)
			self._files.sort(key=prefer_tutorial)
			#add all locales to lang list, select current locale as default and sort
			lang_list = self._widget.findChild(name="uni_langlist")
			self.active_right_side.distributeInitialData({ 'maplist' : maps_display, })
			if maps_display: # select first entry
				self.active_right_side.distributeData({'maplist': 0})
			lang_list.items = self._get_available_languages()
			cur_locale = horizons.globals.fife.get_locale()
			if LANGUAGENAMES[cur_locale] in lang_list.items:
				lang_list.selected = lang_list.items.index(LANGUAGENAMES[cur_locale])
			else:
				lang_list.selected = 0
			self.active_right_side.mapEvents({
				'maplist/action': self._update_scenario_infos,
				'uni_langlist/action': self._update_scenario_infos,
			})
			self._update_scenario_infos()

		self._widget.show()
		self._focus(self._widget)

	def start_single(self):
		""" Starts a single player horizons. """
		playername = self._playerdata.get_player_name()
		if not playername:
			self.windows.show_popup(_("Invalid player name"), _("You entered an invalid playername."))
			return
		playercolor = self._playerdata.get_player_color()
		self._save_player_name()

		if self._widget.collectData('random'):
			map_file = self._get_random_map_file()
		else:
			assert self.active_right_side.collectData('maplist') != -1
			map_file = self._get_selected_map()

		is_scenario = bool(self._widget.collectData('scenario'))
		is_campaign = bool(self._widget.collectData('campaign'))
		if not is_scenario and not is_campaign:
			ai_players = int(self._aidata.get_ai_players())
			horizons.globals.fife.set_uh_setting("AIPlayers", ai_players)
		horizons.globals.fife.save_settings()

		self.hide()
		self._gui.show_loading_screen()
		if is_scenario:
			try:
				options = StartGameOptions.create_start_scenario(map_file)
				options.set_human_data(playername, playercolor)
				horizons.main.start_singleplayer(options)
			except InvalidScenarioFileFormat as e:
				self._show_invalid_scenario_file_popup(e)
				self._select_single(show='scenario')
		elif is_campaign:
			campaign_info = SavegameManager.get_campaign_info(filename=map_file)
			if not campaign_info:
				self._show_invalid_scenario_file_popup("Unknown Error")
				self._select_single(show='campaign')
			scenario = campaign_info.get('scenarios')[0].get('level')
			horizons.main._start_map(scenario, ai_players=0, is_scenario=True, campaign={
				'campaign_name': campaign_info.get('codename'), 'scenario_index': 0, 'scenario_name': scenario
			})
		else: # free play/random map
			options = StartGameOptions.create_start_map(map_file)
			options.set_human_data(playername, playercolor)
			options.ai_players = ai_players
			options.trader_enabled = self._widget_loader['game_settings'].findChild(name='free_trader').marked
			options.pirate_enabled = self._widget_loader['game_settings'].findChild(name='pirates').marked
			options.disasters_enabled = self._widget_loader['game_settings'].findChild(name='disasters').marked
			options.natural_resource_multiplier = self._get_natural_resource_multiplier()
			horizons.main.start_singleplayer(options)

		ExtScheduler().rem_all_classinst_calls(self)

	# random map options
	map_sizes = [50, 100, 150, 200, 250]
	water_percents = [20, 30, 40, 50, 60, 70, 80]
	island_sizes = [30, 40, 50, 60, 70]
	island_size_deviations = [5, 10, 20, 30, 40]

	def _setup_random_map_selection(self, widget):
		seed_string_field = widget.findChild(name='seed_string_field')
		seed_string_field.capture(self._on_random_map_parameter_changed)
		seed_string_field.text = generate_random_seed(seed_string_field.text)

		map_size_slider = widget.findChild(name='map_size_slider')
		def on_map_size_slider_change():
			widget.findChild(name='map_size_lbl').text = _('Map size:') + u' ' + \
				unicode(self.map_sizes[int(map_size_slider.value)])
			horizons.globals.fife.set_uh_setting("RandomMapSize", map_size_slider.value)
			horizons.globals.fife.save_settings()
			self._on_random_map_parameter_changed()
		map_size_slider.capture(on_map_size_slider_change)
		map_size_slider.value = horizons.globals.fife.get_uh_setting("RandomMapSize")

		water_percent_slider = widget.findChild(name='water_percent_slider')
		def on_water_percent_slider_change():
			widget.findChild(name='water_percent_lbl').text = _('Water:') + u' ' + \
				unicode(self.water_percents[int(water_percent_slider.value)]) + u'%'
			horizons.globals.fife.set_uh_setting("RandomMapWaterPercent", water_percent_slider.value)
			horizons.globals.fife.save_settings()
			self._on_random_map_parameter_changed()
		water_percent_slider.capture(on_water_percent_slider_change)
		water_percent_slider.value = horizons.globals.fife.get_uh_setting("RandomMapWaterPercent")

		max_island_size_slider = widget.findChild(name='max_island_size_slider')
		def on_max_island_size_slider_change():
			widget.findChild(name='max_island_size_lbl').text = _('Max island size:') + u' ' + \
				unicode(self.island_sizes[int(max_island_size_slider.value)])
			horizons.globals.fife.set_uh_setting("RandomMapMaxIslandSize", max_island_size_slider.value)
			horizons.globals.fife.save_settings()
			self._on_random_map_parameter_changed()
		max_island_size_slider.capture(on_max_island_size_slider_change)
		max_island_size_slider.value = horizons.globals.fife.get_uh_setting("RandomMapMaxIslandSize")

		preferred_island_size_slider = widget.findChild(name='preferred_island_size_slider')
		def on_preferred_island_size_slider_change():
			widget.findChild(name='preferred_island_size_lbl').text = _('Preferred island size:') + u' ' + \
				unicode(self.island_sizes[int(preferred_island_size_slider.value)])
			horizons.globals.fife.set_uh_setting("RandomMapPreferredIslandSize", preferred_island_size_slider.value)
			horizons.globals.fife.save_settings()
			self._on_random_map_parameter_changed()
		preferred_island_size_slider.capture(on_preferred_island_size_slider_change)
		preferred_island_size_slider.value = horizons.globals.fife.get_uh_setting("RandomMapPreferredIslandSize")

		island_size_deviation_slider = widget.findChild(name='island_size_deviation_slider')
		def on_island_size_deviation_slider_change():
			widget.findChild(name='island_size_deviation_lbl').text = _('Island size deviation:') + u' ' + \
				unicode(self.island_size_deviations[int(island_size_deviation_slider.value)])
			horizons.globals.fife.set_uh_setting("RandomMapIslandSizeDeviation", island_size_deviation_slider.value)
			horizons.globals.fife.save_settings()
			self._on_random_map_parameter_changed()
		island_size_deviation_slider.capture(on_island_size_deviation_slider_change)
		island_size_deviation_slider.value = horizons.globals.fife.get_uh_setting("RandomMapIslandSizeDeviation")

		on_map_size_slider_change()
		on_water_percent_slider_change()
		on_max_island_size_slider_change()
		on_preferred_island_size_slider_change()
		on_island_size_deviation_slider_change()

	def _get_random_map_parameters(self):
		seed_string = self._widget.findChild(name='seed_string_field').text
		map_size = self.map_sizes[int(self._widget.findChild(name='map_size_slider').value)]
		water_percent = self.water_percents[int(self._widget.findChild(name='water_percent_slider').value)]
		max_island_size = self.island_sizes[int(self._widget.findChild(name='max_island_size_slider').value)]
		preferred_island_size = self.island_sizes[int(self._widget.findChild(name='preferred_island_size_slider').value)]
		island_size_deviation = self.island_size_deviations[int(self._widget.findChild(name='island_size_deviation_slider').value)]
		return (seed_string, map_size, water_percent, max_island_size, preferred_island_size, island_size_deviation)

	def _setup_game_settings_selection(self):
		widget = self._widget_loader['game_settings']
		if widget.parent is not None:
			widget.parent.removeChild(widget)
		settings_box = self._widget.findChild(name='game_settings_box')
		settings_box.addChild(widget)

		# make click on labels change the respective checkboxes
		for setting in u'free_trader', u'pirates', u'disasters':
			def toggle(setting):
				box = self._widget.findChild(name=setting)
				box.marked = not box.marked
			self._widget.findChild(name=u'lbl_'+setting).capture(Callback(toggle, setting))

		resource_density_slider = widget.findChild(name='resource_density_slider')
		def on_resource_density_slider_change():
			widget.findChild(name='resource_density_lbl').text = _('Resource density:') + u' ' + \
				unicode(self.resource_densities[int(resource_density_slider.value)]) + u'x'
			horizons.globals.fife.set_uh_setting("MapResourceDensity", resource_density_slider.value)
			horizons.globals.fife.save_settings()
		resource_density_slider.capture(on_resource_density_slider_change)
		resource_density_slider.value = horizons.globals.fife.get_uh_setting("MapResourceDensity")

		on_resource_density_slider_change()

	def _open_random_map_archive(self):
		popup = self._widget_loader['random_map_archive']
		# ok should be triggered on enter, therefore we need to focus the button
		# pychan will only allow it after the widgets is shown
		#ExtScheduler().add_new_object(lambda : popup.findChild(name=OkButton.DEFAULT_NAME).requestFocus(), self, run_in=0)
		popup.mapEvents({OkButton.DEFAULT_NAME : popup.hide})
		popup.show()

	def _get_natural_resource_multiplier(self):
		return self.resource_densities[int(self._widget_loader['game_settings'].findChild(name='resource_density_slider').value)]

	def _get_selected_map(self):
		"""Returns map file, that is selected in the maplist widget"""
		return self._files[ self.active_right_side.collectData('maplist') ]

	def _show_invalid_scenario_file_popup(self, exception):
		"""Shows a popup complaining about invalid scenario file.
		@param exception: Something that str() will convert to an error message"""
		print "Error: ", unicode(str(exception))
		self.show_error_popup(_("Invalid scenario file"),
		                      description=_("The selected file is not a valid scenario file."),
		                      details=_("Error message:") + u' ' + unicode(str(exception)),
		                      advice=_("Please report this to the author."))

	def _update_free_map_infos(self):
		number_of_players = SavegameManager.get_recommended_number_of_players( self._get_selected_map() )
		#xgettext:python-format
		self._widget.findChild(name="recommended_number_of_players_lbl").text = \
			_("Recommended number of players: {number}").format(number=number_of_players)
		self.map_preview.update_map(self._get_selected_map())

	def _update_scenario_infos(self):
		"""Fill in infos of selected scenario to label"""
		lang_list = self._widget.findChild(name="uni_langlist")
		cur_selected_language = lang_list.selected_item
		lang_list.items = self._get_available_languages()
		if cur_selected_language in lang_list.items:
			lang_list.selected = lang_list.items.index(cur_selected_language)
		else:
			lang_list.selected = 0

		cur_locale = LANGUAGENAMES.get_by_value(lang_list.selected_item)
		translated_scenario = self._find_map_filename(cur_locale)
		if os.path.exists(translated_scenario):
			self._update_scenario_translation_infos(translated_scenario)
		else:
			try:
				default_locale, default_encoding = locale.getdefaultlocale()
			except ValueError: # OS X sometimes returns 'UTF-8' as locale, which is a ValueError
				default_locale = 'en'

			possibilities = [ # try to find a file for the system locale before falling back to en
				default_locale,
				default_locale.split('_')[0],
				'en',
			]
			for lang in possibilities:
				if LANGUAGENAMES[lang] in lang_list.items:
					lang_list.selected = lang_list.items.index(LANGUAGENAMES[lang])
					break
			else: # (for-else: else only runs if no break occured) select first one
				lang_list.selected = 0

		try:
			difficulty, author, desc = \
				ScenarioEventHandler.get_metadata_from_file( self._get_selected_map() )
		except InvalidScenarioFileFormat as e:
			self._show_invalid_scenario_file_popup(e)
			return

		#xgettext:python-format
		difficulty_text = _("Difficulty: {difficulty}").format(difficulty=difficulty)
		self._widget.findChild(name="uni_map_difficulty").text = difficulty_text
		#xgettext:python-format
		author_text = _("Author: {author}").format(author=author)
		self._widget.findChild(name="uni_map_author").text = author_text
		#xgettext:python-format
		desc_text = _("Description: {desc}").format(desc=desc)
		self._widget.findChild(name="uni_map_desc").text = desc_text

	def _update_campaign_infos(self):
		"""Fill in infos of selected campaign to label"""
		campaign_info = SavegameManager.get_campaign_info(filename=self._get_selected_map())
		if not campaign_info:
			self._show_invalid_scenario_file_popup("Unknown error")
			return
		#xgettext:python-format
		difficulty_text = _("Difficulty: {difficulty}").format(difficulty=campaign_info.get('difficulty', ''))
		self._widget.findChild(name="map_difficulty").text = difficulty_text
		#xgettext:python-format
		author_text = _("Author: {author}").format(author=campaign_info.get('author', ''))
		self._widget.findChild(name="map_author").text = author_text
		#xgettext:python-format
		desc_text = _("Description: {desc}").format(desc=campaign_info.get('description', ''))
		self._widget.findChild(name="map_desc").text = desc_text

	def _update_scenario_translation_infos(self, new_map_name):
		"""Fill in translation infos of selected scenario to translation label.
		This function also sets scenario map name using locale.
		(e.g. tutorial -> tutorial_en.yaml)"""
		translation_status_label = self._widget.findChild(name="translation_status")
		yamldata = YamlCache.get_file(new_map_name, game_data=True)
		translation_status = yamldata.get('translation_status')
		if translation_status:
			translation_status_label.text = translation_status
			translation_status_label.show()
		else:
			translation_status_label.hide()
		self._files[ self.active_right_side.collectData('maplist') ] = new_map_name

	def _find_map_filename(self, cur_locale, mapfile=None):
		"""Finds the given map's filename with its locale."""
		mapfile = mapfile or self._get_selected_map()
		if mapfile.endswith('.yaml'):
			yamldata = YamlCache.get_file(mapfile, game_data=True)
			split_locale = yamldata['locale']
			mapfile = mapfile.split('_' + split_locale)[0]
		return mapfile + '_' + cur_locale + '.' + SavegameManager.scenario_extension

	def _get_available_languages(self, mapfile=None):
		return sorted(
			[ LANGUAGENAMES[lang] for lang in find_available_languages()
							  if os.path.exists(self._find_map_filename(lang, mapfile)) ])

	def _save_player_name(self):
		if hasattr(self, '_playerdata'):
			playername = self._playerdata.get_player_name()
			horizons.globals.fife.set_uh_setting("Nickname", playername)

	def _on_random_map_parameter_changed(self):
		"""Called to update the map preview"""
		def on_click(event, drag):
			seed_string_field = self._widget.findChild(name='seed_string_field')
			seed_string_field.text = generate_random_seed(seed_string_field.text)
			self._on_random_map_parameter_changed()
		# the user might have changed the menu since the update and we would
		# crash if we don't find the fields with the parameters
		if True: # TODO self.active
		#if self.current is self.widgets['singleplayermenu']:
			self.map_preview.update_random_map( self._get_random_map_parameters(), on_click )

	def _get_random_map_file(self):
		"""Used to start game"""
		return self._generate_random_map( self._get_random_map_parameters() )

	@classmethod
	def _generate_random_map(cls, parameters):
		return generate_random_map( *parameters )


class MapPreview(object):
	"""Semiprivate class dealing with the map preview icon"""
	def __init__(self, get_widget):
		"""
		@param get_widget: returns the current widget (self.current)
		"""
		self.minimap = None
		self.calc_proc = None # handle to background calculation process
		self.get_widget = get_widget
		self._last_random_map_params = None

	def update_map(self, map_file):
		"""Direct map preview update.
		Only use for existing maps, it's too slow for random maps"""
		if self.minimap is not None:
			self.minimap.end()
		world = self._load_raw_world(map_file)
		self.minimap = Minimap(self._get_map_preview_icon(),
		                       session=None,
		                       view=None,
		                       world=world,
		                       targetrenderer=horizons.globals.fife.targetrenderer,
		                       imagemanager=horizons.globals.fife.imagemanager,
		                       cam_border=False,
		                       use_rotation=False,
		                       tooltip=None,
		                       on_click=None,
		                       preview=True)
		self.minimap.draw()

	def update_random_map(self, map_params, on_click):
		"""Called when a random map parameter has changed.
		@param map_params: _get_random_map() output
		@param on_click: handler for clicks"""
		if self._last_random_map_params == map_params:
			return # we already display this, happens on spurious slider events such as hover
		self._last_random_map_params = map_params

		def check_calc_process():
			# checks up on calc process (see below)
			if self.calc_proc is not None:
				state = self.calc_proc.poll()
				if state is None: # not finished
					ExtScheduler().add_new_object(check_calc_process, self, 0.1)
				elif state != 0:
					self._set_map_preview_status(_("An unknown error occured while generating the map preview"))
				else: # done

					data = open(self.calc_proc.output_filename, "r").read()
					os.unlink(self.calc_proc.output_filename)
					self.calc_proc = None

					icon = self._get_map_preview_icon()
					if icon is None:
						return # dialog already gone

					tooltip = _("Click to generate a different random map")

					if self.minimap is not None:
						self.minimap.end()
					self.minimap = Minimap(icon,
					                       session=None,
					                       view=None,
					                       world=None,
					                       targetrenderer=horizons.globals.fife.targetrenderer,
					                       imagemanager=horizons.globals.fife.imagemanager,
					                       cam_border=False,
					                       use_rotation=False,
					                       tooltip=tooltip,
					                       on_click=on_click,
					                       preview=True)
					self.minimap.draw_data( data )
					icon.show()
					self._set_map_preview_status(u"")

		if self.calc_proc is not None:
			self.calc_proc.kill() # process exists, therefore up is scheduled already
		else:
			ExtScheduler().add_new_object(check_calc_process, self, 0.5)

		# launch process in background to calculate minimap data
		minimap_icon = self._get_map_preview_icon()

		params = json.dumps(((minimap_icon.width, minimap_icon.height), map_params))

		args = (sys.executable, sys.argv[0], "--generate-minimap", params)
		handle, outfilename = tempfile.mkstemp()
		os.close(handle)
		self.calc_proc = subprocess.Popen(args=args,
								                      stdout=open(outfilename, "w"))
		self.calc_proc.output_filename = outfilename # attach extra info
		self._set_map_preview_status(_("Generating preview..."))


	@classmethod
	def generate_minimap(cls, size, parameters):
		"""Called as subprocess, calculates minimap data and passes it via string via stdout"""
		# called as standalone basically, so init everything we need
		from horizons.main import _create_main_db
		from horizons.entities import Entities
		from horizons.ext.dummy import Dummy
		db = _create_main_db()
		Entities.load_grounds(db, load_now=False) # create all references
		map_file = SingleplayerMenu._generate_random_map( parameters )
		world = cls._load_raw_world(map_file)
		location = Rect.init_from_topleft_and_size_tuples( (0, 0), size)
		minimap = Minimap(location,
		                  session=None,
		                  view=None,
		                  world=world,
		                  targetrenderer=Dummy(),
		                  imagemanager=Dummy(),
		                  cam_border=False,
		                  use_rotation=False,
		                  preview=True)
		# communicate via stdout
		print minimap.dump_data()

	@classmethod
	def _load_raw_world(cls, map_file):
		WorldObject.reset()
		world = World(session=None)
		world.inited = True
		world.load_raw_map(SavegameAccessor(map_file, True), preview=True)
		return world

	def _get_map_preview_icon(self):
		"""Returns pychan icon for map preview"""
		return self.get_widget().findChild(name="map_preview_minimap")

	def _set_map_preview_status(self, text):
		"""Sets small status label next to map preview"""
		wdg = self.get_widget().findChild(name="map_preview_status_label")
		if wdg: # might show next dialog already
			wdg.text = text
