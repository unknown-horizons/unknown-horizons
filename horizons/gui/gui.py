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
from horizons.i18n.quotes import GAMEPLAY_TIPS, FUN_QUOTES
from horizons.gui.keylisteners import MainListener
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.widgets.pickbeltwidget import CreditsPickbeltWidget
from horizons.util.startgameoptions import StartGameOptions
from horizons.messaging import GuiAction
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.util import LazyWidgetsDict
from horizons.gui.modules.editorstartmenu import EditorStartMenu

from horizons.gui.modules import (SingleplayerMenu, MultiplayerMenu, HelpDialog,
                                  SelectSavegameDialog)
from horizons.gui.widgets.fpsdisplay import FPSDisplay
from horizons.gui.windows import WindowManager
from horizons.command.game import PauseCommand, UnPauseCommand

class Gui(object):
	"""This class handles all the out of game menu, like the main and pause menu, etc.
	"""
	log = logging.getLogger("gui")

	# styles to apply to a widget
	styles = {
	  'mainmenu': 'menu',
	  'requirerestart': 'book',
	  'ingamemenu': 'headline',
	  'singleplayermenu': 'book',
	  'sp_random': 'book',
	  'sp_scenario': 'book',
	  'sp_free_maps': 'book',
	  'multiplayermenu' : 'book',
	  'multiplayer_creategame' : 'book',
	  'multiplayer_gamelobby' : 'book',
	  'set_password' : 'book',
	  'playerdataselection' : 'book',
	  'aidataselection' : 'book',
	  'select_savegame': 'book',
	  'game_settings' : 'book',
	  'editor_pause_menu': 'headline',
	  }

	def __init__(self):
		self.mainlistener = MainListener(self)
		self.current = None # currently active window
		self.widgets = LazyWidgetsDict(self.styles) # access widgets with their filenames without '.xml'
		self.session = None

		self.windows = WindowManager(self.widgets)
		# temporary aliases for compatibility with rest of the code
		self.show_dialog = self.windows.show_dialog
		self.show_popup = self.windows.show_popup
		self.show_error_popup = self.windows.show_error_popup

		self.__pause_displayed = False

		self._background = pychan.Icon(image=self._get_random_background(),
		                               position_technique='automatic')
		self._background.show()

		self.subscribe()

		self.singleplayermenu = SingleplayerMenu(self)
		self.multiplayermenu = MultiplayerMenu(self)
		self.help_dialog = HelpDialog(self)
		self.selectsavegame_dialog = SelectSavegameDialog(self)
		self.show_select_savegame = self.selectsavegame_dialog.show_select_savegame

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

		self._switch_current_widget('mainmenu', show=True, event_map={
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

		self.on_escape = self.show_quit

	def load_game(self):
		saved_game = self.show_select_savegame(mode='load')
		if saved_game is None:
			return False # user aborted dialog

		self.show_loading_screen()
		options = StartGameOptions(saved_game)
		horizons.main.start_singleplayer(options)
		return True

	def toggle_pause(self):
		"""Shows in-game pause menu if the game is currently not paused.
		Else unpauses and hides the menu. Multiple layers of the 'paused' concept exist;
		if two widgets are opened which would both pause the game, we do not want to
		unpause after only one of them is closed. Uses PauseCommand and UnPauseCommand.
		"""
		# TODO: logically, this now belongs to the ingame_gui (it used to be different)
		#       this manifests itself by the need for the __pause_displayed hack below
		#       in the long run, this should be moved, therefore eliminating the hack, and
		#       ensuring correct setup/teardown.
		if self.__pause_displayed:
			self.__pause_displayed = False
			self.hide()
			self.current = None
			UnPauseCommand(suggestion=True).execute(self.session)
			self.on_escape = self.toggle_pause

		else:
			self.__pause_displayed = True
			# reload the menu because caching creates spacing problems
			# see http://trac.unknown-horizons.org/t/ticket/1047
			in_editor_mode = self.session.in_editor_mode()
			menu_name = 'editor_pause_menu' if in_editor_mode else 'ingamemenu'
			self.widgets.reload(menu_name)
			def do_load():
				did_load = self.load_game()
				if did_load:
					self.__pause_displayed = False
			def do_load_map():
				self.show_editor_start_menu(False)
			def do_quit():
				did_quit = self.quit_session()
				if did_quit:
					self.__pause_displayed = False
			events = { # needed twice, save only once here
				'e_load' : do_load_map if in_editor_mode else do_load,
				'e_save' : self.session.ingame_gui.show_save_map_dialog if in_editor_mode else self.save_game,
				'e_sett' : self.show_settings,
				'e_help' : self.on_help,
				'e_start': self.toggle_pause,
				'e_quit' : do_quit,
			}
			self._switch_current_widget(menu_name, show=False, event_map={
				  # icons
				'loadgameButton' : events['e_load'],
				'savegameButton' : events['e_save'],
				'settingsLink'   : events['e_sett'],
				'helpLink'       : events['e_help'],
				'startGame'      : events['e_start'],
				'closeButton'    : events['e_quit'],
				# labels
				'loadgame' : events['e_load'],
				'savegame' : events['e_save'],
				'settings' : events['e_sett'],
				'help'     : events['e_help'],
				'start'    : events['e_start'],
				'quit'     : events['e_quit'],
			})

			self.windows.show_modal_background()
			self.current.show()

			PauseCommand(suggestion=True).execute(self.session)
			self.on_escape = self.toggle_pause

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
		self._switch_current_widget('loadingscreen', show=True)
		# Add 'Quote of the Load' to loading screen:
		qotl_type_label = self.current.findChild(name='qotl_type_label')
		qotl_label = self.current.findChild(name='qotl_label')
		quote_type = int(horizons.globals.fife.get_uh_setting("QuotesType"))
		if quote_type == 2:
			quote_type = random.randint(0, 1) # choose a random type

		if quote_type == 0:
			name = GAMEPLAY_TIPS["name"]
			items = GAMEPLAY_TIPS["items"]
		elif quote_type == 1:
			name = FUN_QUOTES["name"]
			items = FUN_QUOTES["items"]

		qotl_type_label.text = unicode(name)
		qotl_label.text = unicode(random.choice(items)) # choose a random quote / gameplay tip

# helper

	def _switch_current_widget(self, new_widget, event_map=None, show=False, hide_old=False):
		"""Switches self.current to a new widget.
		@param new_widget: str (widget name) or loaded pychan widget
		@param event_map: pychan event map to apply to new widget
		@param show: bool, if True old window gets hidden and new one shown
		@param hide_old: bool, if True old window gets hidden. Implied by show
		@return: instance of old widget"""
		old = self.current
		if (show or hide_old) and old is not None:
			self.log.debug("Gui: hiding %s", old)
			self.hide()
		self.log.debug("Gui: setting current to %s", new_widget)
		if isinstance(new_widget, str):
			self.current = self.widgets[new_widget]
		else:
			self.current = new_widget
		if event_map:
			self.current.mapEvents(event_map)
		self.current.position_technique = "automatic" # == "center:center"
		if show:
			self.current.show()

		return old

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
		self._switch_current_widget(editor_start_menu, hide_old=True)
		return True
