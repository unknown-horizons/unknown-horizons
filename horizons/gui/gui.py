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

import glob
import random
import logging

import horizons.globals
import horizons.main

from horizons.gui.keylisteners import MainListener
from horizons.messaging import GuiAction
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.mainmenu import (CallForSupport, Credits, SaveLoad, Help, SingleplayerMenu,
								   MultiplayerMenu, Settings, MainMenu, LoadingScreen)
from horizons.gui.pausemenu import PauseMenu
from horizons.gui.util import LazyWidgetsDict
from horizons.gui.window import WindowManager


class Gui(object):
	"""This class handles all the out of game menu, like the main and pause menu, etc.
	"""
	log = logging.getLogger("gui")

	# styles to apply to a widget
	styles = {
	  'mainmenu': 'menu',
	  'requirerestart': 'book',
	  'ingamemenu': 'headline',
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
	  'ingame_pause': 'book',
	  'game_settings' : 'book',
#	  'credits': 'book',
	  }

	def __init__(self):
		self.mainlistener = MainListener(self)
		self.current = None # currently active window
		self.widgets = LazyWidgetsDict(self.styles) # access widgets with their filenames without '.xml'
		self.session = None

		self._background_image = self._get_random_background()

		self._windows = WindowManager(self.widgets)

		self._call_for_support = CallForSupport(self.widgets, manager=self._windows)
		self._credits = Credits(self.widgets, manager=self._windows)
		self._saveload = SaveLoad(self.widgets, gui=self, manager=self._windows)
		self._help = Help(self.widgets, gui=self, manager=self._windows)
		self._singleplayer = SingleplayerMenu(self.widgets, gui=self, manager=self._windows)
		self._multiplayer = MultiplayerMenu(self.widgets, gui=self, manager=self._windows)
		self._settings = Settings(None, manager=self._windows)
		self._mainmenu = MainMenu(self.widgets, gui=self, manager=self._windows)
		self._loadingscreen = LoadingScreen(self.widgets, manager=self._windows)

		self._ingame_windows = WindowManager(self.widgets)
		self._pausemenu = PauseMenu(self.widgets, gui=self, manager=self._ingame_windows)

		GuiAction.subscribe( self._on_gui_action )

# basic menu widgets

	def show_main(self):
		self._windows.show(self._mainmenu)

	def toggle_pause(self):
		"""Shows in-game pause menu if the game is currently not paused.
		Else unpauses and hides the menu. Multiple layers of the 'paused' concept exist;
		if two widgets are opened which would both pause the game, we do not want to
		unpause after only one of them is closed. Uses PauseCommand and UnPauseCommand.
		"""
		self._ingame_windows.toggle(self._pausemenu)

# what happens on button clicks

	def save_game(self):
		"""Wrapper for saving for separating gui messages from save logic
		"""
		success = self.session.save()
		if not success:
			# There was a problem during the 'save game' procedure.
			self._windows.show_popup(_('Error'), _('Failed to save.'))

	def on_help(self):
		"""Called on help action.
		Toggles help screen via static variable *help_is_displayed*.
		Can be called both from main menu and in-game interface.
		"""
		self._windows.toggle(self._help)

	def show_quit(self):
		"""Shows the quit dialog. Closes the game unless the dialog is cancelled."""
		message = _("Are you sure you want to quit Unknown Horizons?")
		if self._windows.show_popup(_("Quit Game"), message, show_cancel_button=True):
			horizons.main.quit()

	def quit_session(self, force=False):
		"""Quits the current session. Usually returns to main menu afterwards.
		@param force: whether to ask for confirmation"""
		message = _("Are you sure you want to abort the running session?")

		if force or self._windows.show_popup(_("Quit Session"), message, show_cancel_button=True):
			if self.current is not None:
				# this can be None if not called from gui (e.g. scenario finished)
				self.hide()
				self.current = None
			if self.session is not None:
				self.session.end()
				self.session = None

			self.show_main()
			return True
		else:
			return False

	def show_select_savegame(self, mode, sanity_checker=None, sanity_criteria=None):
		return self._windows.show(self._saveload, mode=mode, sanity_checker=sanity_checker,
								  sanity_criteria=sanity_criteria)

# display

	# TODO remove both functions later
	def show_popup(self, *args, **kwargs):
		return self._windows.show_popup(*args, **kwargs)

	def show_error_popup(self, *args, **kwargs):
		return self._windows.show_error_popup(*args, **kwargs)

	def on_escape(self):
		pass

	def show(self):
		self.log.debug("Gui: showing current: %s", self.current)
		if self.current is not None:
			self.current.show()

	def hide(self):
		self._windows.close_all()

	def is_visible(self):
		return self.current is not None and self.current.isVisible()

	def show_loading_screen(self):
		self._windows.show(self._loadingscreen)

# helper

	def get_random_background_by_button(self):
		"""Randomly select a background image to use. This function is triggered by
		change background button from main menu."""
		#we need to redraw screen to apply changes.
		self.hide()
		self._background_image = self._get_random_background()
		self.show_main()

	def _get_random_background(self):
		"""Randomly select a background image to use through out the game menu."""
		available_images = glob.glob('content/gui/images/background/mainmenu/bg_*.png')
		#get latest background
		latest_background = horizons.globals.fife.get_uh_setting("LatestBackground")
		#if there is a latest background then remove it from available list
		if latest_background is not None:
			available_images.remove(latest_background)
		background_choice = random.choice(available_images)
		#save current background choice
		horizons.globals.fife.set_uh_setting("LatestBackground", background_choice)
		horizons.globals.fife.save_settings()
		return background_choice

	def _on_gui_action(self, msg):
		AmbientSoundComponent.play_special('click')
