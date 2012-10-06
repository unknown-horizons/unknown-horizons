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
from fife import fife
from fife.extensions import pychan
from horizons.gui.quotes import GAMEPLAY_TIPS, FUN_QUOTES

import horizons.globals
import horizons.main

from horizons.gui.keylisteners import MainListener
from horizons.messaging import GuiAction
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.util import LazyWidgetsDict
from horizons.gui.window import WindowManager

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

		self.__pause_displayed = False
		self._background_image = self._get_random_background()

		self._windows = WindowManager(self.widgets)

		from horizons.gui.mainmenu import CallForSupport, Credits, SaveLoad, Help, SingleplayerMenu, MultiplayerMenu
		self._call_for_support = CallForSupport(self.widgets, manager=self._windows)
		self._credits = Credits(self.widgets, manager=self._windows)
		self._saveload = SaveLoad(self.widgets, gui=self, manager=self._windows)
		self._help = Help(self.widgets, gui=self, manager=self._windows)
		self._singleplayer = SingleplayerMenu(self.widgets, gui=self, manager=self._windows)
		self._multiplayer = MultiplayerMenu(self.widgets, gui=self, manager=self._windows)

		GuiAction.subscribe( self._on_gui_action )

# basic menu widgets

	def show_main(self):
		"""Shows the main menu """
		self._switch_current_widget('mainmenu', center=True, show=True, event_map={
			'startSingle'      : lambda: self._windows.show(self._singleplayer), # first is the icon in menu
			'start'            : lambda: self._windows.show(self._singleplayer), # second is the label in menu
			'startMulti'       : lambda: self._windows.show(self._multiplayer),
			'start_multi'      : lambda: self._windows.show(self._multiplayer),
			'settingsLink'     : self.show_settings,
			'settings'         : self.show_settings,
			'helpLink'         : self.on_help,
			'help'             : self.on_help,
			'closeButton'      : self.show_quit,
			'quit'             : self.show_quit,
			'dead_link'        : lambda: self._windows.show(self._call_for_support), # call for help; SoC information
			'chimebell'        : lambda: self._windows.show(self._call_for_support),
			'creditsLink'      : lambda: self._windows.show(self._credits),
			'credits'          : lambda: self._windows.show(self._credits),
			'loadgameButton'   : horizons.main.load_game,
			'loadgame'         : horizons.main.load_game,
			'changeBackground' : self.get_random_background_by_button
		})

		self.on_escape = self.show_quit

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
			self.widgets.reload('ingamemenu')
			def do_load():
				did_load = horizons.main.load_game()
				if did_load:
					self.__pause_displayed = False
			def do_quit():
				did_quit = self.quit_session()
				if did_quit:
					self.__pause_displayed = False
			events = { # needed twice, save only once here
				'e_load' : do_load,
				'e_save' : self.save_game,
				'e_sett' : self.show_settings,
				'e_help' : self.on_help,
				'e_start': self.toggle_pause,
				'e_quit' : do_quit,
			}
			self._switch_current_widget('ingamemenu', center=True, show=False, event_map={
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

			self.show_modal_background()
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
			self._windows.show_popup(_('Error'), _('Failed to save.'))

	def show_settings(self):
		"""Displays settings gui derived from the FIFE settings module."""
		horizons.globals.fife.show_settings()

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
		self.log.debug("Gui: hiding current: %s", self.current)
		if self.current is not None:
			self.current.hide()
			self.hide_modal_background()

	def is_visible(self):
		return self.current is not None and self.current.isVisible()

	def show_modal_background(self):
		""" Loads transparent background that de facto prohibits
		access to other gui elements by eating all input events.
		Used for modal popups and our in-game menu.
		"""
		height = horizons.globals.fife.engine_settings.getScreenHeight()
		width = horizons.globals.fife.engine_settings.getScreenWidth()
		image = horizons.globals.fife.imagemanager.loadBlank(width, height)
		image = fife.GuiImage(image)
		self.additional_widget = pychan.Icon(image=image)
		self.additional_widget.position = (0, 0)
		self.additional_widget.show()

	def hide_modal_background(self):
		try:
			self.additional_widget.hide()
			del self.additional_widget
		except AttributeError:
			pass # only used for some widgets, e.g. pause

	def show_loading_screen(self):
		self._switch_current_widget('loadingscreen', center=True, show=True)
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

	def _switch_current_widget(self, new_widget, center=False, event_map=None, show=False, hide_old=False):
		"""Switches self.current to a new widget.
		@param new_widget: str, widget name
		@param center: bool, whether to center the new widget
		@param event_map: pychan event map to apply to new widget
		@param show: bool, if True old window gets hidden and new one shown
		@param hide_old: bool, if True old window gets hidden. Implied by show
		@return: instance of old widget"""
		old = self.current
		if (show or hide_old) and old is not None:
			self.log.debug("Gui: hiding %s", old)
			self.hide()
		self.log.debug("Gui: setting current to %s", new_widget)
		self.current = self.widgets[new_widget]
		bg = self.current.findChild(name='background')
		if bg:
			# Set background image
			bg.image = self._background_image
		if center:
			self.current.position_technique = "automatic" # == "center:center"
		if event_map:
			self.current.mapEvents(event_map)
		if show:
			self.current.show()

		return old

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
