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
import traceback

from fife import fife
from fife.extensions import pychan

import horizons.globals
import horizons.main

from horizons.i18n.quotes import GAMEPLAY_TIPS, FUN_QUOTES
from horizons.gui.keylisteners import MainListener
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.util.python.callback import Callback
from horizons.util.startgameoptions import StartGameOptions
from horizons.extscheduler import ExtScheduler
from horizons.messaging import GuiAction
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.util import LazyWidgetsDict
from horizons.gui.modules.editorstartmenu import EditorStartMenu

from horizons.gui.modules import (SingleplayerMenu, MultiplayerMenu, HelpDialog,
                                  SelectSavegameDialog)
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
	  'editor_pause_menu': 'headline',
	  }

	def __init__(self):
		self.mainlistener = MainListener(self)
		self.current = None # currently active window
		self.widgets = LazyWidgetsDict(self.styles) # access widgets with their filenames without '.xml'
		self.session = None
		self.current_dialog = None

		self.dialog_executed = False

		self.__pause_displayed = False
		self._background_image = self._get_random_background()
		self.subscribe()

		self.singleplayermenu = SingleplayerMenu(self)
		self.multiplayermenu = MultiplayerMenu(self)
		self.help_dialog = HelpDialog(self)
		self.selectsavegame_dialog = SelectSavegameDialog(self)
		self.show_select_savegame = self.selectsavegame_dialog.show_select_savegame

	def subscribe(self):
		"""Subscribe to the necessary messages."""
		GuiAction.subscribe(self._on_gui_action)

	def unsubscribe(self):
		GuiAction.unsubscribe(self._on_gui_action)

# basic menu widgets
	def show_main(self):
		"""Shows the main menu """
		self._switch_current_widget('mainmenu', center=True, show=True, event_map={
			'startSingle'      : self.show_single, # first is the icon in menu
			'start'            : self.show_single, # second is the label in menu
			'startMulti'       : self.show_multi,
			'start_multi'      : self.show_multi,
			'settingsLink'     : self.show_settings,
			'settings'         : self.show_settings,
			'helpLink'         : self.on_help,
			'help'             : self.on_help,
			'editor_link'      : self.show_editor_start_menu,
			'editor'           : self.show_editor_start_menu,
			'closeButton'      : self.show_quit,
			'quit'             : self.show_quit,
			'creditsLink'      : self.show_credits,
			'credits'          : self.show_credits,
			'loadgameButton'   : self.load_game,
			'loadgame'         : self.load_game,
			'changeBackground' : self.get_random_background_by_button,
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
			self._switch_current_widget(menu_name, center=True, show=False, event_map={
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

	def show_credits(self, number=0):
		"""Shows the credits dialog. """
		if self.current_dialog is not None:
			self.current_dialog.hide()

		credits_page = self.widgets['credits{number}'.format(number=number)]
		for box in credits_page.findChildren(name='box'):
			box.margins = (30, 0) # to get some indentation
			if number in [0, 2]: # #TODO fix these hardcoded page references
				box.padding = 1
				box.parent.padding = 3 # further decrease if more entries
		labels = [credits_page.findChild(name=section+"_lbl")
		          for section in ('team', 'patchers', 'translators',
		                          'packagers', 'special_thanks')]
		for i in xrange(5): # add callbacks to each pickbelt
			labels[i].capture(Callback(self.show_credits, i), event_name="mouseClicked")

		self.show_dialog(credits_page, {OkButton.DEFAULT_NAME : True})

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
			self.hide_modal_background()

	def is_visible(self):
		return self.current is not None and self.current.isVisible()

	def show_dialog(self, dlg, bind, event_map=None, modal=False):
		"""Shows any pychan dialog.
		@param dlg: dialog that is to be shown
		@param bind: events that make the dialog return + return values{ 'ok': callback, 'cancel': callback }
		@param event_map: dictionary with callbacks for buttons. See pychan docu: pychan.widget.mapEvents()
		@param modal: Whether to block user interaction while displaying the dialog
		"""
		self.current_dialog = dlg
		if event_map is not None:
			dlg.mapEvents(event_map)
		if modal:
			self.show_modal_background()

		# handle escape and enter keypresses
		def _on_keypress(event, dlg=dlg): # rebind to make sure this dlg is used
			from horizons.engine import pychan_util
			if event.getKey().getValue() == fife.Key.ESCAPE: # convention says use cancel action
				btn = dlg.findChild(name=CancelButton.DEFAULT_NAME)
				callback = pychan_util.get_button_event(btn) if btn else None
				if callback:
					pychan.tools.applyOnlySuitable(callback, event=event, widget=btn)
				else:
					# escape should hide the dialog default
					horizons.globals.fife.pychanmanager.breakFromMainLoop(returnValue=False)
					dlg.hide()
			elif event.getKey().getValue() == fife.Key.ENTER: # convention says use ok action
				btn = dlg.findChild(name=OkButton.DEFAULT_NAME)
				callback = pychan_util.get_button_event(btn) if btn else None
				if callback:
					pychan.tools.applyOnlySuitable(callback, event=event, widget=btn)
				# can't guess a default action here

		dlg.capture(_on_keypress, event_name="keyPressed")

		# show that a dialog is being executed, this can sometimes require changes in program logic elsewhere
		self.dialog_executed = True
		ret = dlg.execute(bind)
		self.dialog_executed = False
		if modal:
			self.hide_modal_background()
		return ret

	def show_popup(self, windowtitle, message, show_cancel_button=False, size=0, modal=True):
		"""Displays a popup with the specified text
		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, show cancel button or not
		@param size: 0, 1 or 2. Larger means bigger.
		@param modal: Whether to block user interaction while displaying the popup
		@return: True on ok, False on cancel (if no cancel button, always True)
		"""
		popup = self.build_popup(windowtitle, message, show_cancel_button, size=size)
		# ok should be triggered on enter, therefore we need to focus the button
		# pychan will only allow it after the widgets is shown
		def focus_ok_button():
			popup.findChild(name=OkButton.DEFAULT_NAME).requestFocus()
		ExtScheduler().add_new_object(focus_ok_button, self, run_in=0)
		if show_cancel_button:
			return self.show_dialog(popup, {OkButton.DEFAULT_NAME : True,
			                                CancelButton.DEFAULT_NAME : False},
			                        modal=modal)
		else:
			return self.show_dialog(popup, {OkButton.DEFAULT_NAME : True},
			                        modal=modal)

	def show_error_popup(self, windowtitle, description, advice=None, details=None, _first=True):
		"""Displays a popup containing an error message.
		@param windowtitle: title of popup, will be auto-prefixed with "Error: "
		@param description: string to tell the user what happened
		@param advice: how the user might be able to fix the problem
		@param details: technical details, relevant for debugging but not for the user
		@param _first: Don't touch this.

		Guide for writing good error messages:
		http://www.useit.com/alertbox/20010624.html
		"""
		msg = u""
		msg += description + u"\n"
		if advice:
			msg += advice + u"\n"
		if details:
			msg += _("Details: {error_details}").format(error_details=details)
		try:
			self.show_popup( _("Error: {error_message}").format(error_message=windowtitle),
			                 msg, show_cancel_button=False)
		except SystemExit: # user really wants us to die
			raise
		except:
			# could be another game error, try to be persistent in showing the error message
			# else the game would be gone without the user being able to read the message.
			if _first:
				traceback.print_exc()
				print 'Exception while showing error, retrying once more'
				return self.show_error_popup(windowtitle, description, advice, details, _first=False)
			else:
				raise # it persists, we have to die.

	def build_popup(self, windowtitle, message, show_cancel_button=False, size=0):
		""" Creates a pychan popup widget with the specified properties.
		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, include cancel button or not
		@param size: 0, 1 or 2
		@return: Container(name='popup_window') with buttons 'okButton' and optionally 'cancelButton'
		"""
		if size == 0:
			wdg_name = "popup_230"
		elif size == 1:
			wdg_name = "popup_290"
		elif size == 2:
			wdg_name = "popup_350"
		else:
			assert False, "size should be 0 <= size <= 2, but is "+str(size)

		# NOTE: reusing popup dialogs can sometimes lead to exit(0) being called.
		#       it is yet unknown why this happens, so let's be safe for now and reload the widgets.
		self.widgets.reload(wdg_name)
		popup = self.widgets[wdg_name]

		if not show_cancel_button:
			cancel_button = popup.findChild(name=CancelButton.DEFAULT_NAME)
			cancel_button.parent.removeChild(cancel_button)

		popup.headline = popup.findChild(name='headline')
		popup.headline.text = _(windowtitle)
		popup.message = popup.findChild(name='popup_message')
		popup.message.text = _(message)
		popup.adaptLayout() # recalculate widths
		return popup

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
		if isinstance(new_widget, str):
			self.current = self.widgets[new_widget]
		else:
			self.current = new_widget
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

	def show_editor_start_menu(self, from_main_menu=True):
		editor_start_menu = EditorStartMenu(self, from_main_menu)
		self._switch_current_widget(editor_start_menu, hide_old=True)
		return True

	def show_single(self):
		self.singleplayermenu.show_single()

	def show_multi(self):
		self.multiplayermenu.show_multi()
