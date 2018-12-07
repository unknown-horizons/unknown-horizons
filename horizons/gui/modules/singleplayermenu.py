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


import json
import locale
import logging
import os
import re
import subprocess
import sys
import tempfile
from typing import List, Optional, Tuple

import horizons.globals
import horizons.main
from horizons.constants import LANGUAGENAMES, PATHS, VERSION
from horizons.extscheduler import ExtScheduler
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.minimap import Minimap, iter_minimap_points_colors
from horizons.gui.windows import Window
from horizons.i18n import gettext as T
from horizons.savegamemanager import SavegameManager
from horizons.scenario import InvalidScenarioFileFormat, ScenarioEventHandler
from horizons.util.python.callback import Callback
from horizons.util.random_map import generate_random_map, generate_random_seed
from horizons.util.shapes import Rect
from horizons.util.startgameoptions import StartGameOptions
from horizons.world import load_raw_world  # FIXME placing this import at the end results in a cycle

from .aidataselection import AIDataSelection
from .playerdataselection import PlayerDataSelection


class SingleplayerMenu(Window):

	def __init__(self, windows):
		super().__init__(windows)

		self._mode = None

		self._gui = load_uh_widget('singleplayermenu.xml')
		self._gui.mapEvents({
			'cancel': self._windows.close,
			'okay': self.act,
			'scenario': Callback(self._select_mode, 'scenario'),
			'random': Callback(self._select_mode, 'random'),
			'free_maps': Callback(self._select_mode, 'free_maps')
		})

		self._playerdata = PlayerDataSelection()
		self._aidata = AIDataSelection()
		self._gui.findChild(name="playerdataselectioncontainer").addChild(self._playerdata.get_widget())
		self._gui.findChild(name="aidataselectioncontainer").addChild(self._aidata.get_widget())

	def hide(self):
		# Save the player-data on hide so that other menus gets updated data
		self._playerdata.save_settings()
		self._gui.hide()

	def show(self):
		self._playerdata.update_data()
		self._gui.findChild(name='scenario').marked = True
		self._select_mode('scenario')

	def on_return(self):
		self.act()

	def _select_mode(self, mode):
		self._gui.hide()

		modes = {
			'random': RandomMapWidget,
			'free_maps': FreeMapsWidget,
			'scenario': ScenarioMapWidget,
		}

		# remove old widget
		if self._mode:
			self._mode.end()
			self._gui.findChild(name="right_side_box").removeChild(self._mode.get_widget())

		self._mode = modes[mode](self._windows, self, self._aidata)
		self._mode.show()

		self._gui.findChild(name="right_side_box").addChild(self._mode.get_widget())
		self._gui.show()

	def act(self):
		"""Start the game. Called when OK button is pressed."""
		player_color = self._playerdata.get_player_color()
		player_name = self._playerdata.get_player_name()

		if not player_name:
			self._windows.open_popup(T("Invalid player name"), T("You entered an invalid playername."))
			return

		horizons.globals.fife.set_uh_setting("Nickname", player_name)

		self._windows.close()
		self._mode.act(player_name, player_color)


class GameSettingsWidget:
	"""Toggle trader/pirates/disasters and change resource density."""

	def __init__(self):
		self._gui = load_uh_widget('game_settings.xml')

	def get_widget(self):
		return self._gui

	def show(self):
		# make click on labels change the respective checkboxes
		checkboxes = [('free_trader', 'MapSettingsFreeTraderEnabled'),
		              ('pirates', 'MapSettingsPirateEnabled'),
		              ('disasters', 'MapSettingsDisastersEnabled')]

		for (setting, setting_save_name) in checkboxes:

			def on_box_toggle(setting, setting_save_name):
				"""Called whenever the checkbox is toggled"""
				box = self._gui.findChild(name=setting)
				horizons.globals.fife.set_uh_setting(setting_save_name, box.marked)
				horizons.globals.fife.save_settings()

			def toggle(setting, setting_save_name):
				"""Called by the label to toggle the checkbox"""
				box = self._gui.findChild(name=setting)
				box.marked = not box.marked

			self._gui.findChild(name=setting).capture(Callback(on_box_toggle, setting, setting_save_name))
			self._gui.findChild(name=setting).marked = horizons.globals.fife.get_uh_setting(setting_save_name)
			self._gui.findChild(name='lbl_' + setting).capture(Callback(toggle, setting, setting_save_name))

		resource_density_slider = self._gui.findChild(name='resource_density_slider')

		def on_resource_density_slider_change():
			self._gui.findChild(name='resource_density_lbl').text = T('Resource density:') + ' ' + \
				str(resource_density_slider.value) + 'x'
			horizons.globals.fife.set_uh_setting("MapResourceDensity", resource_density_slider.value)
			horizons.globals.fife.save_settings()

		resource_density_slider.capture(on_resource_density_slider_change)
		resource_density_slider.value = horizons.globals.fife.get_uh_setting("MapResourceDensity")

		on_resource_density_slider_change()

	@property
	def natural_resource_multiplier(self):
		return self._gui.findChild(name='resource_density_slider').value

	@property
	def free_trader(self):
		return self._gui.findChild(name='free_trader').marked

	@property
	def pirates(self):
		return self._gui.findChild(name='pirates').marked

	@property
	def disasters(self):
		return self._gui.findChild(name='disasters').marked


class RandomMapWidget:
	"""Create a random map, influence map generation with multiple sliders."""

	def __init__(self, windows, singleplayer_menu, aidata):
		self._windows = windows
		self._singleplayer_menu = singleplayer_menu
		self._aidata = aidata

		self._gui = load_uh_widget('sp_random.xml')
		self._map_parameters = {}  # stores the current values from the sliders
		self._game_settings = GameSettingsWidget()

		# Map preview
		self._last_map_parameters = None
		self._preview_process = None
		self._preview_output = None
		self._map_preview = None

	def end(self):
		if self._preview_process:
			self._preview_process.kill()
			self._preview_process = None
		ExtScheduler().rem_all_classinst_calls(self)

	def get_widget(self):
		return self._gui

	def act(self, player_name, player_color):
		self.end()

		map_file = generate_random_map(*self._get_map_parameters())

		options = StartGameOptions.create_start_map(map_file)
		options.set_human_data(player_name, player_color)
		options.ai_players = self._aidata.get_ai_players()
		options.trader_enabled = self._game_settings.free_trader
		options.pirate_enabled = self._game_settings.pirates
		options.disasters_enabled = self._game_settings.disasters
		options.natural_resource_multiplier = self._game_settings.natural_resource_multiplier
		horizons.main.start_singleplayer(options)

	def show(self):
		seed_string_field = self._gui.findChild(name='seed_string_field')
		seed_string_field.capture(self._on_random_parameter_changed)
		seed_string_field.text = generate_random_seed(seed_string_field.text)

		parameters = (
			('map_size', T('Map size:'), 'RandomMapSize'),
			('water_percent', T('Water:'), 'RandomMapWaterPercent'),
			('max_island_size', T('Max island size:'), 'RandomMapMaxIslandSize'),
			('preferred_island_size', T('Preferred island size:'), 'RandomMapPreferredIslandSize'),
			('island_size_deviation', T('Island size deviation:'), 'RandomMapIslandSizeDeviation'),
		)

		for param, __, setting_name in parameters:
			self._map_parameters[param] = int(horizons.globals.fife.get_uh_setting(setting_name))

		def make_on_change(param, text, setting_name):
			# When a slider is changed, update the value displayed in the label, save the value
			# in the settings and store the value in self._map_parameters
			def on_change():
				slider = self._gui.findChild(name=param + '_slider')
				self._gui.findChild(name=param + '_lbl').text = text + ' ' + str(int(slider.value))
				horizons.globals.fife.set_uh_setting(setting_name, slider.value)
				horizons.globals.fife.save_settings()
				self._map_parameters[param] = int(slider.value)
				self._on_random_parameter_changed()
			return on_change

		for param, text, setting_name in parameters:
			slider = self._gui.findChild(name=param + '_slider')
			on_change = make_on_change(param, text, setting_name)
			slider.capture(on_change)
			slider.value = horizons.globals.fife.get_uh_setting(setting_name)
			on_change()

		self._gui.findChild(name='game_settings_box').addChild(self._game_settings.get_widget())
		self._game_settings.show()
		self._aidata.show()

	def _get_map_parameters(self):
		return (
			self._gui.findChild(name='seed_string_field').text,
			self._map_parameters['map_size'],
			self._map_parameters['water_percent'],
			self._map_parameters['max_island_size'],
			self._map_parameters['preferred_island_size'],
			self._map_parameters['island_size_deviation']
		)

	def _on_random_parameter_changed(self):
		self._update_map_preview()

	# Map preview

	def _on_preview_click(self, event, drag):
		seed_string_field = self._gui.findChild(name='seed_string_field')
		seed_string_field.text = generate_random_seed(seed_string_field.text)
		self._on_random_parameter_changed()

	def _update_map_preview(self):
		"""Start a new process to generate a map preview."""
		current_parameters = self._get_map_parameters()
		if self._last_map_parameters == current_parameters:
			# nothing changed, don't generate a new preview
			return

		self._last_map_parameters = current_parameters

		if self._preview_process:
			self._preview_process.kill() # process exists, therefore up is scheduled already

		# launch process in background to calculate minimap data
		minimap_icon = self._gui.findChild(name='map_preview_minimap')
		params = json.dumps(((minimap_icon.width, minimap_icon.height), current_parameters))

		args = [sys.executable, sys.argv[0], "--generate-minimap", params]
		# We're running UH in a new process, make sure fife is setup correctly
		if horizons.main.command_line_arguments.fife_path:
			args.extend(["--fife-path", horizons.main.command_line_arguments.fife_path])

		handle, self._preview_output = tempfile.mkstemp()
		os.close(handle)
		self._preview_process = subprocess.Popen(args=args, stdout=open(self._preview_output, "w"))
		self._set_map_preview_status("Generating preview…")

		ExtScheduler().add_new_object(self._poll_preview_process, self, 0.5)

	def _poll_preview_process(self):
		"""This will be called regularly to see if the process ended.

		If the process has not yet finished, schedule a new callback to this function.
		Otherwise use the data to update the minimap.
		"""
		if not self._preview_process:
			return

		self._preview_process.poll()

		if self._preview_process.returncode is None: # not finished
			ExtScheduler().add_new_object(self._poll_preview_process, self, 0.1)
			return
		elif self._preview_process.returncode != 0:
			self._preview_process = None
			self._set_map_preview_status("An unknown error occurred while generating the map preview")
			return

		with open(self._preview_output, 'r') as f:
			data = f.read()
			# Sometimes the subprocess outputs more then the minimap data, e.g. debug
			# information. Since we just read from its stdout, parse out the data that
			# is relevant to us.
			data = re.findall(r'^DATA (\[\[.*\]\]) ENDDATA$', data, re.MULTILINE)[0]
			data = json.loads(data)

		os.unlink(self._preview_output)
		self._preview_process = None

		if self._map_preview:
			self._map_preview.end()

		self._map_preview = Minimap(
			self._gui.findChild(name='map_preview_minimap'),
			session=None,
			view=None,
			world=None,
			targetrenderer=horizons.globals.fife.targetrenderer,
			imagemanager=horizons.globals.fife.imagemanager,
			cam_border=False,
			use_rotation=False,
			tooltip=T("Click to generate a different random map"),
			on_click=self._on_preview_click,
			preview=True)

		self._map_preview.draw_data(data)
		self._set_map_preview_status("")

	def _set_map_preview_status(self, text):
		self._gui.findChild(name="map_preview_status_label").text = text


class FreeMapsWidget:
	"""Start a game by selecting an existing map."""

	def __init__(self, windows, singleplayer_menu, aidata):
		self._windows = windows
		self._singleplayer_menu = singleplayer_menu
		self._aidata = aidata

		self._gui = load_uh_widget('sp_free_maps.xml')
		self._game_settings = GameSettingsWidget()

		self._map_preview = None

	def end(self):
		pass

	def get_widget(self):
		return self._gui

	def act(self, player_name, player_color):
		map_file = self._get_selected_map()

		options = StartGameOptions.create_start_map(map_file)
		options.set_human_data(player_name, player_color)
		options.ai_players = self._aidata.get_ai_players()
		options.trader_enabled = self._game_settings.free_trader
		options.pirate_enabled = self._game_settings.pirates
		options.disasters_enabled = self._game_settings.disasters
		options.natural_resource_multiplier = self._game_settings.natural_resource_multiplier
		horizons.main.start_singleplayer(options)

	def show(self):
		self._files, maps_display = SavegameManager.get_maps()

		self._gui.distributeInitialData({'maplist': maps_display})
		self._gui.mapEvents({
			'maplist/action': self._update_map_infos,
		})
		if maps_display: # select first entry
			self._gui.distributeData({'maplist': 0})
			self._update_map_infos()

		self._gui.findChild(name='game_settings_box').addChild(self._game_settings.get_widget())
		self._game_settings.show()
		self._aidata.show()

	def _update_map_infos(self):
		map_file = self._get_selected_map()

		number_of_players = SavegameManager.get_recommended_number_of_players(map_file)
		lbl = self._gui.findChild(name="recommended_number_of_players_lbl")
		lbl.text = T("Recommended number of players: {number}").format(number=number_of_players)

		self._update_map_preview(map_file)

	def _get_selected_map(self):
		selection_index = self._gui.collectData('maplist')
		assert selection_index != -1

		return self._files[self._gui.collectData('maplist')]

	def _update_map_preview(self, map_file):
		if self._map_preview:
			self._map_preview.end()

		world = load_raw_world(map_file)
		self._map_preview = Minimap(
			self._gui.findChild(name='map_preview_minimap'),
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

		self._map_preview.draw()


class ScenarioMapWidget:
	"""Start a scenario (with a specific language)."""

	def __init__(self, windows, singleplayer_menu, aidata):
		self._windows = windows
		self._singleplayer_menu = singleplayer_menu
		self._aidata = aidata
		self._scenarios = {}

		self._language_fallback_active = False

		self._gui = load_uh_widget('sp_scenario.xml')

	def end(self):
		pass

	def get_widget(self):
		return self._gui

	def act(self, player_name, player_color):
		map_file = self._get_selected_map()

		try:
			options = StartGameOptions.create_start_scenario(map_file)
			options.set_human_data(player_name, player_color)
			horizons.main.start_singleplayer(options)
		except InvalidScenarioFileFormat as e:
			self._show_invalid_scenario_file_popup(e)

	def show(self):
		self._aidata.hide()

		self._scenarios = SavegameManager.get_available_scenarios()

		# get the map files and their display names. display tutorials on top.
		self.maps_display = list(self._scenarios.keys())
		if not self.maps_display:
			return

		prefer_tutorial = lambda x: ('tutorial' not in x, x)
		self.maps_display.sort(key=prefer_tutorial)

		self._gui.distributeInitialData({'maplist': self.maps_display})
		self._gui.distributeData({'maplist': 0})
		self._gui.mapEvents({
			'maplist/action': self._on_map_change,
			'uni_langlist/action': self._update_infos,
		})
		self._on_map_change()

	def _show_invalid_scenario_file_popup(self, exception):
		"""Shows a popup complaining about invalid scenario file.

		@param exception: Something that str() will convert to an error message
		"""
		logging.getLogger('gui.windows').error("Error: %s", exception)
		self._windows.open_error_popup(
			T("Invalid scenario file"),
			description=T("The selected file is not a valid scenario file."),
			details=T("Error message:") + ' ' + str(str(exception)),
			advice=T("Please report this to the author."))

	def _on_map_change(self):
		# type: () -> None
		lang_list = self._gui.findChild(name="uni_langlist")
		selected_language = lang_list.selected_item

		if (selected_language is None
		    or self._language_fallback_active):
			# Either no language is selected (this happens initially), or the previous
			# map needed a fallback language: we want to choose a more appropriate
			# one for the new map.
			selected_language = LANGUAGENAMES[horizons.globals.fife.get_locale()]
			self._language_fallback_active = False

		self._update_infos(selected_language=selected_language)

	def _update_infos(self, selected_language=None):
		# type: (Optional[str]) -> None
		"""
		Check if selected language is available or pick a fallback language. Fill in infos
		of selected scenario.
		"""
		scenario_idx = self._gui.findChild(name="maplist").selected_item
		scenario = self._scenarios[scenario_idx]

		lang_list = self._gui.findChild(name="uni_langlist")
		selected_language = selected_language if selected_language is not None else lang_list.selected_item

		available_languages = self.get_available_languages(scenario)
		if selected_language not in available_languages:
			selected_language = LANGUAGENAMES[self.guess_suitable_default_locale(available_languages)]
			self._language_fallback_active = True
		else:
			self._language_fallback_active = False

		lang_list.items = available_languages
		lang_list.selected = available_languages.index(selected_language)

		selected_language_code = LANGUAGENAMES.get_by_value(selected_language)
		translated_scenario = self.find_map_filename(scenario, selected_language_code)
		if translated_scenario is None:
			return

		self._update_scenario_translation_infos(translated_scenario)

	@staticmethod
	def guess_suitable_default_locale(available_languages):
		# type: (List[str]) -> Optional[str]
		"""Attempts to guess a reasonable localized scenario to preselect in SP menu.

		If no filename was found so far for our scenario:
		 1. Try harder to find locale of user
		 2. Try to find a file for the system locale
		 3. Fall back to English
		"""
		try:
			default_locale, default_encoding = locale.getdefaultlocale()
		except ValueError: # OS X sometimes returns 'UTF-8' as locale, which is a ValueError
			default_locale = 'en'

		possibilities = [
			default_locale,
			default_locale.split('@')[0],
			default_locale.split('_')[0],
			'en',
		]
		for lang in possibilities:
			if LANGUAGENAMES[lang] in available_languages:
				return lang

	def _update_scenario_translation_infos(self, scenario):
		"""Fill in translation infos of selected scenario to translation label."""
		try:
			metadata = ScenarioEventHandler.get_metadata_from_file(scenario)
		except InvalidScenarioFileFormat as e:
			self._show_invalid_scenario_file_popup(e)
			return

		translation_status = metadata.get('translation_status', '')
		lbl = self._gui.findChild(name="translation_status")
		lbl.text = translation_status

		lbl = self._gui.findChild(name="uni_map_difficulty")
		lbl.text = T("Difficulty: {difficulty}").format(difficulty=metadata['difficulty'])

		lbl = self._gui.findChild(name="uni_map_author")
		lbl.text = T("Author: {author}").format(author=metadata['author'])

		lbl = self._gui.findChild(name="uni_map_desc")
		lbl.text = T("Description: {desc}").format(desc=metadata['description'])

	@staticmethod
	def find_map_filename(scenario, target_locale):
		# type: (List[Tuple[str, str]], str) -> Optional[str]
		"""Finds the given map's filename with its locale."""
		for language, mapfile in scenario:
			if language == target_locale and os.path.exists(mapfile):
				return mapfile

	@staticmethod
	def get_available_languages(scenario):
		# type: (List[Tuple[str, str]]) -> List[str]
		scenario_langs = {language for language, filename in scenario}
		return [LANGUAGENAMES[l] for l in sorted(scenario_langs)]

	def _get_selected_map(self):
		selection_index = self._gui.collectData('maplist')
		assert selection_index != -1
		scenario = self._scenarios[self.maps_display[selection_index]]
		language_index = self._gui.collectData('uni_langlist')
		return scenario[language_index][1]


def generate_random_minimap(size, parameters):
	"""Called as subprocess, calculates minimap data and passes it via string via stdout"""
	# called as standalone basically, so init everything we need
	from horizons.entities import Entities
	from horizons.main import _create_main_db

	if not VERSION.IS_DEV_VERSION:
		# Hack enable atlases.
		# Usually the minimap generator uses single tile files, but in release
		# mode these are not available. Therefor we have to hackenable atlases
		# for the minimap generation in this case. This forces the game to use
		# the correct imageloader
		# In normal dev mode + enabled atlases we ignore this and just continue
		# to use single tile files instead of atlases for the minimap generation.
		# These are always available in dev checkouts
		PATHS.DB_FILES = PATHS.DB_FILES + (PATHS.ATLAS_DB_PATH, )

	db = _create_main_db()
	horizons.globals.db = db
	horizons.globals.fife.init_animation_loader(not VERSION.IS_DEV_VERSION)
	Entities.load_grounds(db, load_now=False) # create all references

	map_file = generate_random_map(*parameters)
	world = load_raw_world(map_file)
	location = Rect.init_from_topleft_and_size_tuples((0, 0), size)

	# communicate via stdout. Sometimes the process seems to print more information, therefore
	# we add markers around our data so it's easier for the caller to get to the data.
	args = (location, world, Minimap.COLORS['island'], Minimap.COLORS['water'])
	data = [(x, y, r, g, b) for (x, y), (r, g, b) in iter_minimap_points_colors(*args)]
	print('DATA', json.dumps(data), 'ENDDATA')
