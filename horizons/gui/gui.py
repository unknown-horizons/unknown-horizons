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
import logging
import random

from fife.extensions import pychan

import horizons.globals
import horizons.main
from horizons.gui.keylisteners import MainListener
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.widgets.pickbeltwidget import CreditsPickbeltWidget
from horizons.util.startgameoptions import StartGameOptions
from horizons.messaging import GuiAction
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.util import load_uh_widget
from horizons.gui.modules.editorstartmenu import EditorStartMenu

from horizons.gui.modules import (SingleplayerMenu, MultiplayerMenu, HelpDialog,
                                  SelectSavegameDialog, LoadingScreen)
from horizons.gui.widgets.fpsdisplay import FPSDisplay
from horizons.gui.windows import WindowManager


class Gui(object):
	"""This class handles all the out of game menu, like the main and pause menu, etc.
	"""
	log = logging.getLogger("gui")

	def __init__(self):
		self.mainlistener = MainListener(self)
		self.current = None # currently active window
		self.session = None

		self.windows = WindowManager()
		# temporary aliases for compatibility with rest of the code
		self.show_dialog = self.windows.show_dialog
		self.show_popup = self.windows.show_popup
		self.show_error_popup = self.windows.show_error_popup

		self.__pause_displayed = False

		self._background = pychan.Icon(image=self._get_random_background(),
		                               position_technique='center:center')
		self._background.show()

		self.subscribe()

		self.singleplayermenu = SingleplayerMenu(self)
		self.multiplayermenu = MultiplayerMenu(self)
		self.help_dialog = HelpDialog(self)
		self.selectsavegame_dialog = SelectSavegameDialog(self)
		self.show_select_savegame = self.selectsavegame_dialog.show_select_savegame
		self.loadingscreen = LoadingScreen()

		self.mainmenu = load_uh_widget('mainmenu.xml', 'menu')
		self.mainmenu.mapEvents({
			'single_button': self.singleplayermenu.show,
			'single_label' : self.singleplayermenu.show,
			'multi_button': self.multiplayermenu.show,
			'multi_label' : self.multiplayermenu.show,
			'settings_button': self.show_settings,
			'settings_label' : self.show_settings,
			'help_button': self.on_help,
			'help_label' : self.on_help,
			'quit_button': self.show_quit,
			'quit_label' : self.show_quit,
			'editor_button': self.show_editor_start_menu,
			'editor_label' : self.show_editor_start_menu,
			'credits_button': self.show_credits,
			'credits_label' : self.show_credits,
			'load_button': self.load_game,
			'load_label' : self.load_game,
			'changeBackground' : self.randomize_background
		})

		self.fps_display = FPSDisplay()

	def subscribe(self):
		"""Subscribe to the necessary messages."""
		GuiAction.subscribe(self._on_gui_action)

	def unsubscribe(self):
		GuiAction.unsubscribe(self._on_gui_action)

# basic menu widgets
	def show_main(self):
		"""Shows the main menu """
		if not self._background.isVisible():
			self._background.show()

		self.hide()
		self.on_escape = self.show_quit
		self.current = self.mainmenu
		self.current.show()

	def load_game(self):
		saved_game = self.show_select_savegame(mode='load')
		if saved_game is None:
			return False # user aborted dialog

		self.show_loading_screen()
		options = StartGameOptions(saved_game)
		horizons.main.start_singleplayer(options)
		return True

# what happens on button clicks

	def save_game(self):
		"""Wrapper for saving for separating gui messages from save logic
		"""
		success = self.session.save()
		if not success:
			# There was a problem during the 'save game' procedure.
			self.show_popup(_('Error'), _('Failed to save.'))

	def show_settings(self):
		"""Displays settings gui derived from the FIFE settings module."""
		horizons.globals.fife.show_settings()

	def on_help(self):
		self.help_dialog.toggle()

	def show_quit(self):
		"""Shows the quit dialog. Closes the game unless the dialog is cancelled."""
		message = _("Are you sure you want to quit Unknown Horizons?")
		if self.show_popup(_("Quit Game"), message, show_cancel_button=True):
			horizons.main.quit()

	def quit_session(self, force=False):
		"""Quits the current session. Usually returns to main menu afterwards.
		@param force: whether to ask for confirmation"""
		message = _("Are you sure you want to abort the running session?")

		if force or self.show_popup(_("Quit Session"), message, show_cancel_button=True):
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

	def show_credits(self):
		"""Shows the credits dialog. """
		widget = CreditsPickbeltWidget().get_widget()
		self.show_dialog(widget, {OkButton.DEFAULT_NAME: True})

# display

	def on_escape(self):
		pass

	def show(self):
		self.log.debug("Gui: showing current: %s", self.current)
		if self.current is not None:
			self.current.show()

	def hide(self):
		self.log.debug("Gui: hiding current: %s", self.current)
		if self.current is not None:
			self.current.hide()
			self.windows.hide_modal_background()

	def hide_all(self):
		self.hide()
		self._background.hide()

	def is_visible(self):
		return self.current is not None and self.current.isVisible()

	def show_loading_screen(self):
		self.hide()
		self.current = self.loadingscreen
		self.current.show()

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

	def show_editor_start_menu(self, from_main_menu=True):
		editor_start_menu = EditorStartMenu(self, from_main_menu)
		self.hide()
		self.current = editor_start_menu
		self.current.show()
		return True
