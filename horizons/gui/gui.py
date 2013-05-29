# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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
import logging
import random

from fife.extensions.pychan.widgets import Icon

import horizons.globals
import horizons.main
from horizons.gui.keylisteners import MainListener
from horizons.gui.widgets.pickbeltwidget import CreditsPickbeltWidget
from horizons.util.startgameoptions import StartGameOptions
from horizons.messaging import GuiAction
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.util import load_uh_widget
from horizons.gui.modules.editorstartmenu import EditorStartMenu
from horizons.gui.modules import (SingleplayerMenu, MultiplayerMenu,
                                  SelectSavegameDialog, LoadingScreen, SettingsDialog)
from horizons.gui.widgets.fpsdisplay import FPSDisplay
from horizons.gui.windows import WindowManager, Window


class MainMenu(Window):

	def __init__(self, gui, windows):
		super(MainMenu, self).__init__(windows)

		self._gui = load_uh_widget('mainmenu.xml', 'menu')
		self._gui.mapEvents({
			'single_button': lambda: self._windows.show(gui.singleplayermenu),
			'single_label' : lambda: self._windows.show(gui.singleplayermenu),
			'multi_button': lambda: self._windows.show(gui.multiplayermenu),
			'multi_label' : lambda: self._windows.show(gui.multiplayermenu),
			'settings_button': lambda: self._windows.show(gui.settings_dialog),
			'settings_label' : lambda: self._windows.show(gui.settings_dialog),
			'help_button': gui.on_help,
			'help_label' : gui.on_help,
			'quit_button': self.on_escape,
			'quit_label' : self.on_escape,
			'editor_button': gui.show_editor_start_menu,
			'editor_label' : gui.show_editor_start_menu,
			'credits_button': gui.show_credits,
			'credits_label' : gui.show_credits,
			'load_button': gui.load_game,
			'load_label' : gui.load_game,
			'changeBackground' : gui.randomize_background
		})

	def show(self):
		self._gui.show()

	def hide(self):
		self._gui.hide()

	def on_escape(self):
		"""Shows the quit dialog. Closes the game unless the dialog is cancelled."""
		message = _("Are you sure you want to quit Unknown Horizons?")
		if self._windows.show_popup(_("Quit Game"), message, show_cancel_button=True):
			horizons.main.quit()


class Gui(object):
	"""This class handles all the out of game menu, like the main and pause menu, etc.
	"""
	log = logging.getLogger("gui")

	def __init__(self):
		self.mainlistener = MainListener(self)

		self.windows = WindowManager()
		# temporary aliases for compatibility with rest of the code
		self.show_popup = self.windows.show_popup
		self.show_error_popup = self.windows.show_error_popup

		self._background = Icon(image=self._get_random_background(),
		                        position_technique='center:center')
		self._background.show()

		self.singleplayermenu = SingleplayerMenu(self.windows)
		self.multiplayermenu = MultiplayerMenu(self, self.windows)
		self.help_dialog = None
		self.loadingscreen = LoadingScreen()
		self.settings_dialog = SettingsDialog(self.windows)
		self.mainmenu = MainMenu(self, self.windows)
		self.fps_display = FPSDisplay()

	def show_main(self):
		"""Shows the main menu """
		GuiAction.subscribe(self._on_gui_action)

		if not self._background.isVisible():
			self._background.show()

		self.windows.show(self.mainmenu)

	def show_select_savegame(self, mode):
		window = SelectSavegameDialog(mode, self.windows)
		return self.windows.show(window)

	def load_game(self):
		saved_game = self.show_select_savegame(mode='load')
		if saved_game is None:
			return False # user aborted dialog

		options = StartGameOptions(saved_game)
		horizons.main.start_singleplayer(options)
		return True

	def on_help(self):
		self.windows.toggle(self.help_dialog)

	def show_credits(self):
		"""Shows the credits dialog. """
		window = CreditsPickbeltWidget(self.windows)
		self.windows.show(window)

	def on_escape(self):
		self.windows.on_escape()

	def on_return(self):
		self.windows.on_return()

	def close_all(self):
		GuiAction.discard(self._on_gui_action)
		self.windows.close_all()
		self._background.hide()

	def show_loading_screen(self):
		if not self._background.isVisible():
			self._background.show()
		self.windows.show(self.loadingscreen)

	def randomize_background(self):
		"""Randomly select a background image to use. This function is triggered by
		change background button from main menu."""
		self._background.image = self._get_random_background()

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

	def show_editor_start_menu(self):
		editor_start_menu = EditorStartMenu(self.windows)
		self.windows.show(editor_start_menu)
