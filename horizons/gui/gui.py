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

import logging

import horizons.main
from horizons.gui.keylisteners import MainListener
from horizons.messaging import GuiAction
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.mainmenu import (CallForSupport, Credits, SaveLoad, Help, SingleplayerMenu,
                                   MultiplayerMenu, Settings, MainMenu, LoadingScreen, Background,
                                   EditorLoadMap)
from horizons.gui.util import LazyWidgetsDict
from horizons.gui.window import WindowManager
from horizons.util.startgameoptions import StartGameOptions


class Gui(object):
	"""This class handles all the out of game menu, like the main and pause menu, etc.
	"""
	log = logging.getLogger("gui")

	# styles to apply to a widget
	styles = {
	  'mainmenu': 'menu',
	  'requirerestart': 'book',
	  'help': 'book',
	  'singleplayermenu': 'book',
	  'sp_random': 'book',
	  'sp_scenario': 'book',
	  'sp_campaign': 'book',
	  'sp_free_maps': 'book',
	  'multiplayermenu' : 'book',
	  'multiplayer_creategame' : 'book',
	  'multiplayer_gamelobby' : 'book',
	  'playerdataselection' : 'book',
	  'aidataselection' : 'book',
	  'select_savegame': 'book',
	  'game_settings' : 'book',
#	  'credits': 'book',
	  'editor_select_map': 'book',
	  }

	def __init__(self):
		self.mainlistener = MainListener(self)
		self.widgets = LazyWidgetsDict(self.styles) # access widgets with their filenames without '.xml'
		self.session = None

		self._windows = WindowManager(self.widgets)

		self._call_for_support = CallForSupport(self.widgets, manager=self._windows)
		self._credits = Credits(self.widgets, manager=self._windows)
		self._saveload = SaveLoad(self.widgets, gui=self, manager=self._windows)
		self._editor_load_map = EditorLoadMap(self.widgets, gui=self, manager=self._windows)
		self._help = Help(self.widgets, gui=self, manager=self._windows)
		self._singleplayer = SingleplayerMenu(self.widgets, gui=self, manager=self._windows)
		self._multiplayer = MultiplayerMenu(self.widgets, gui=self, manager=self._windows)
		self._settings = Settings(None, manager=self._windows)
		self._mainmenu = MainMenu(self.widgets, gui=self, manager=self._windows)
		self._loadingscreen = LoadingScreen(self.widgets, manager=self._windows)
		self._background = Background(self.widgets)

		GuiAction.subscribe( self._on_gui_action )

	def load_game(self):
		saved_game = self.show_select_savegame(mode='load')
		if saved_game is None:
			return False # user aborted dialog

		self.show_loading_screen()
		options = StartGameOptions(saved_game)
		horizons.main.start_singleplayer(options)
		return True

	def on_help(self):
		"""Toggles help screen."""
		self._windows.toggle(self._help)

	# TODO remove this
	def show_select_savegame(self, mode, sanity_checker=None, sanity_criteria=None):
		return self._windows.show(self._saveload, mode=mode, sanity_checker=sanity_checker,
		                          sanity_criteria=sanity_criteria)

	# TODO perhaps remove both functions later
	def show_popup(self, *args, **kwargs):
		return self._windows.show_popup(*args, **kwargs)

	def show_error_popup(self, *args, **kwargs):
		return self._windows.show_error_popup(*args, **kwargs)

	def show(self):
		"""Display the mainmenu.

		This is called on startup or when we're coming back from a game.
		"""
		self._windows.show(self._background)
		self._windows.show(self._mainmenu)

	def hide(self):
		"""Completely hide the mainmenu.

		Called once we're ingame and the ingame gui is ready.
		"""
		self._windows.close_all()

	def show_loading_screen(self):
		"""Show loading screen.

		When a game is started from the command line, we need to add the background
		window manually, because the main gui was never shown.
		"""
		if self._background not in self._windows:
			self._windows.show(self._background)
		self._windows.show(self._loadingscreen)

	def _on_gui_action(self, msg):
		AmbientSoundComponent.play_special('click')
