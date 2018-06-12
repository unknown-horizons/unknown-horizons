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

import glob
import logging
from collections import deque

from fife.extensions.pychan.widgets import Container, Icon

import horizons.globals
import horizons.main
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.keylisteners import MainListener
from horizons.gui.modules import (
	HelpDialog, LoadingScreen, MultiplayerMenu, SelectSavegameDialog, SettingsDialog, SingleplayerMenu)
from horizons.gui.modules.editorstartmenu import EditorStartMenu
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.fpsdisplay import FPSDisplay
from horizons.gui.widgets.pickbeltwidget import CreditsPickbeltWidget
from horizons.gui.windows import Window, WindowManager
from horizons.i18n import gettext as T
from horizons.messaging import GuiAction, GuiCancelAction, GuiHover
from horizons.util.startgameoptions import StartGameOptions


class MainMenu(Window):
	# normal and hover
	CHANGE_BACKGROUND_LABEL_BACKGROUND_COLOR = [(0, 0, 0, 70), (0, 0, 0, 175)]

	def __init__(self, gui, windows):
		super().__init__(windows)

		self._gui = load_uh_widget('mainmenu.xml', 'menu')
		self._gui.mapEvents({
			'single_button': lambda: self._windows.open(gui.singleplayermenu),
			'single_label': lambda: self._windows.open(gui.singleplayermenu),
			'multi_button': lambda: self._windows.open(gui.multiplayermenu),
			'multi_label': lambda: self._windows.open(gui.multiplayermenu),
			'settings_button': lambda: self._windows.open(gui.settings_dialog),
			'settings_label': lambda: self._windows.open(gui.settings_dialog),
			'help_button': gui.on_help,
			'help_label': gui.on_help,
			'quit_button': self.on_escape,
			'quit_label': self.on_escape,
			'editor_button': gui.show_editor_start_menu,
			'editor_label': gui.show_editor_start_menu,
			'credits_button': gui.show_credits,
			'credits_label': gui.show_credits,
			'load_button': gui.load_game,
			'load_label': gui.load_game,
			'changeBackground': gui._background.rotate_image,
			'changeBackground/mouseEntered': self.mouse_entered_changebackground,
			'changeBackground/mouseExited': self.mouse_exited_changebackground,
		})

		# non-default background color for this Label
		w = self._gui.findChildByName('changeBackground')
		w.background_color = self.CHANGE_BACKGROUND_LABEL_BACKGROUND_COLOR[0]

	def show(self):
		self._gui.show()

	def hide(self):
		self._gui.hide()

	def on_escape(self):
		"""Shows the quit dialog. Closes the game unless the dialog is cancelled."""
		message = T("Are you sure you want to quit Unknown Horizons?")
		if self._windows.open_popup(T("Quit Game"), message, show_cancel_button=True):
			horizons.main.quit()

	def mouse_entered_changebackground(self):
		w = self._gui.findChildByName('changeBackground')
		w.background_color = self.CHANGE_BACKGROUND_LABEL_BACKGROUND_COLOR[1]

	def mouse_exited_changebackground(self):
		w = self._gui.findChildByName('changeBackground')
		w.background_color = self.CHANGE_BACKGROUND_LABEL_BACKGROUND_COLOR[0]


class Background:
	"""
	Display a centered background image on top of a black screen.
	"""
	def __init__(self):
		available_images = glob.glob('content/gui/images/background/mainmenu/bg_*.png')
		self.bg_images = deque(available_images)

		latest_bg = horizons.globals.fife.get_uh_setting("LatestBackground")
		try:
			# If we know the current background from an earlier session,
			# show all other available ones before picking that one again.
			self.bg_images.remove(latest_bg)
			self.bg_images.append(latest_bg)
		except ValueError:
			pass

		(res_width, res_height) = horizons.globals.fife.get_fife_setting('ScreenResolution').split('x')
		self._black_box = Container()
		self._black_box.size = int(res_width), int(res_height)
		self._black_box.base_color = (0, 0, 0, 255)

		self._image = Icon(position_technique='center:center')
		self.rotate_image()

	def rotate_image(self):
		"""Select next background image to use in the game menu.

		Triggered by the "Change background" main menu button.
		"""
		self.bg_images.rotate(1)
		self._image.image = self.bg_images[0]
		# Save current background choice to settings.
		# This keeps the background image consistent between sessions.
		horizons.globals.fife.set_uh_setting("LatestBackground", self.bg_images[0])
		horizons.globals.fife.save_settings()

	def show(self):
		self._black_box.show()
		self._image.show()

	def hide(self):
		self._image.hide()
		self._black_box.hide()

	@property
	def visible(self):
		return self._image.isVisible()


class Gui:
	"""This class handles all the out of game menu, like the main and pause menu, etc.
	"""
	log = logging.getLogger("gui")

	def __init__(self):
		self.mainlistener = MainListener(self)

		self.windows = WindowManager()
		# temporary aliases for compatibility with rest of the code
		self.open_popup = self.windows.open_popup
		self.open_error_popup = self.windows.open_error_popup

		self._background = Background()
		self._background.show()

		# Initialize menu dialogs and widgets that are accessed from `gui`.
		self.singleplayermenu = SingleplayerMenu(self.windows)
		self.multiplayermenu = MultiplayerMenu(self, self.windows)
		self.help_dialog = HelpDialog(self.windows)
		self.loadingscreen = LoadingScreen()
		self.settings_dialog = SettingsDialog(self.windows)
		self.mainmenu = MainMenu(self, self.windows)
		self.fps_display = FPSDisplay()

	def show_main(self):
		"""Shows the main menu"""
		GuiAction.subscribe(self._on_gui_click_action)
		GuiHover.subscribe(self._on_gui_hover_action)
		GuiCancelAction.subscribe(self._on_gui_cancel_action)

		if not self._background.visible:
			self._background.show()

		self.windows.open(self.mainmenu)

	def show_select_savegame(self, mode):
		window = SelectSavegameDialog(mode, self.windows)
		return self.windows.open(window)

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
		self.windows.open(window)

	def on_escape(self):
		self.windows.on_escape()

	def on_return(self):
		self.windows.on_return()

	def close_all(self):
		GuiAction.discard(self._on_gui_click_action)
		GuiHover.discard(self._on_gui_hover_action)
		GuiCancelAction.discard(self._on_gui_cancel_action)
		self.windows.close_all()
		self._background.hide()

	def show_loading_screen(self):
		if not self._background.visible:
			self._background.show()
		self.windows.open(self.loadingscreen)

	def _on_gui_click_action(self, msg):
		"""Make a sound when a button is clicked"""
		AmbientSoundComponent.play_special('click', gain=10)

	def _on_gui_cancel_action(self, msg):
		"""Make a sound when a cancelButton is clicked"""
		AmbientSoundComponent.play_special('success', gain=10)

	def _on_gui_hover_action(self, msg):
		"""Make a sound when the mouse hovers over a button"""
		AmbientSoundComponent.play_special('refresh', position=None, gain=1)

	def show_editor_start_menu(self):
		editor_start_menu = EditorStartMenu(self.windows)
		self.windows.open(editor_start_menu)
