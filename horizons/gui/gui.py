# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from fife import fife
import os
import os.path
import time
from fife.extensions import pychan
import logging

import horizons.main

from horizons.savegamemanager import SavegameManager
from horizons.gui.keylisteners import MainListener
from horizons.util import Callback
from horizons.util.gui import adjust_widget_black_background, LazyWidgetsDict
from horizons.ambientsound import AmbientSound
from horizons.i18n.utils import N_

from horizons.gui.modules import SingleplayerMenu, MultiplayerMenu

class Gui(SingleplayerMenu, MultiplayerMenu):
	"""This class handles all the out of game menu, like the main and pause menu, etc.

	"""
	log = logging.getLogger("gui")

	# styles to apply to a widget
	styles = {
	  'mainmenu': 'menu',
	  'requirerestart': 'book',
	  'gamemenu': 'menu',
	  'help': 'book',
	  'singleplayermenu': 'book',
	  'multiplayermenu' : 'book',
	  'multiplayer_creategame' : 'book',
	  'multiplayer_gamelobby' : 'book',
	  'playerdataselection' : 'book',
	  'select_savegame': 'book',
	  'ingame_pause': 'book',
#	  'credits': 'book',
	  }

	def __init__(self):
		self.mainlistener = MainListener(self)
		self.current = None # currently active window
		self.widgets = LazyWidgetsDict(self.styles) # access widgets with their filenames without '.xml'
		self.session = None
		self.current_dialog = None

# basic menu widgets

	def show_main(self):
		"""Shows the main menu """
		self._switch_current_widget('mainmenu', center=True, show=True, event_map = {
			'startSingle'    : self.show_single,
			'startMulti'     : self.show_multi,
			'settingsLink'   : self.show_settings,
			'helpLink'       : self.on_help,
			'closeButton'    : self.show_quit,
			'dead_link'      : self.on_chime, # call for help; SoC information
			'creditsLink'    : self.show_credits,
			'loadgameButton' : horizons.main.load_game
		})

		self.on_escape = self.show_quit

		adjust_widget_black_background(self.widgets['mainmenu'])

	def show_pause(self):
		"""
		Show Pause menu
		"""
		self._switch_current_widget('gamemenu', center=True, show=True, event_map={
			'startGame'      : self.return_to_game,
			'savegameButton' : self.save_game,
			'settingsLink'   : self.show_settings,
			'helpLink'       : self.on_help,
			'closeButton'    : self.quit_session,
			'dead_link'      : self.on_chime,
			'creditsLink'    : self.show_credits,
			'loadgameButton' : horizons.main.load_game
		})

		adjust_widget_black_background(self.widgets['gamemenu'])

		self.session.speed_pause()
		self.on_escape = self.return_to_game

# what happens on button clicks

	def return_to_game(self):
		"""Return to the horizons."""
		self.hide() # Hide old gui
		self.current = None
		self.session.speed_unpause()
		self.on_escape = self.show_pause

	def save_game(self):
		"""Wrapper for saving for separating gui messages from save logic
		"""
		success = self.session.save()
		if not success:
			self.show_popup(_('Error'), _('Failed to save.'))

	def show_settings(self):
		horizons.main.fife._setting.onOptionsPress()

	_help_is_displayed = False
	def on_help(self):
		"""Called on help action
		Toggles help screen via static variable help_is_displayed"""
		help_dlg = self.widgets['help']
		if not self._help_is_displayed:
			self._help_is_displayed = True
			# make game pause if there is a game and we're not in the main menu
			if self.session is not None and self.current != self.widgets['gamemenu']:
				self.session.speed_pause()
			self.show_dialog(help_dlg, {'okButton' : True}, onPressEscape = True)
			self.on_help() # toggle state
		else:
			self._help_is_displayed = False
			if self.session is not None and self.current != self.widgets['gamemenu']:
				self.session.speed_unpause()
			help_dlg.hide()

	def show_quit(self):
		"""Shows the quit dialog """
		message = _("Are you sure you want to quit Unknown Horizons?")
		if self.show_popup(_("Quit Game"),message,show_cancel_button = True):
			horizons.main.quit()

	def quit_session(self, force=False):
		"""Quits the current session.
		@param force: whether to ask for confirmation"""
		message = _("Are you sure you want to abort the running session?")
		if force or \
		   self.show_popup(_("Quit Session"),message,show_cancel_button = True):
			self.current.hide()
			self.current = None
			if self.session is not None:
				self.session.end()
				self.session = None

			self.show_main()

	def on_chime(self):
		"""
		Called chime action. Displaying call for help on artists and game design,
		introduces information for SoC applicants (if valid).
		"""
		AmbientSound.play_special("message")
		self.show_dialog(self.widgets['call_for_support'], {'okButton' : True}, onPressEscape = True)

	def show_credits(self, number=0):
		"""Shows the credits dialog. """
		for box in self.widgets['credits'+str(number)].findChildren(name='box'):
			box.margins = (30,0) # to get some indentation
			if number == 2: # #TODO fix this hardcoded translators page ref
				box.padding = 1 # further decrease if more entries
				box.parent.padding = 3 # see above
		label = [self.widgets['credits'+str(number)].findChild(name=section+"_lbl") \
		              for section in ('team','patchers','translators','special_thanks')]
		for i in xrange (0,4):
			if label[i]: # add callbacks to each pickbelt that is displayed
				label[i].capture(Callback(self.show_credits, i),
				                 event_name="mouseClicked")

		if self.current_dialog is not None:
			self.current_dialog.hide()
		self.show_dialog(self.widgets['credits'+str(number)], {'okButton' : True}, onPressEscape = True)

	def show_select_savegame(self, mode):
		"""Shows menu to select a savegame.
		@param mode: 'save' or 'load'
		@return: Path to savegamefile or None"""
		assert mode in ('save', 'load')
		map_files, map_file_display = None, None
		if mode == 'load':
			map_files, map_file_display = SavegameManager.get_saves()
			if len(map_files) == 0:
				self.show_popup(_("No saved games"), _("There are no saved games to load"))
				return
		else: # don't show autosave and quicksave on save
			map_files, map_file_display = SavegameManager.get_regular_saves()

		# Prepare widget
		old_current = self._switch_current_widget('select_savegame')
		self.current.findChild(name='headline').text = _('Save game') if mode == 'save' else _('Load game')

		""" this doesn't work (yet), see http://fife.trac.cvsdude.com/engine/ticket/375
		if mode == 'save': # only show enter_filename on save
			self.current.findChild(name='enter_filename').show()
		else:
			self.current.findChild(name='enter_filename').hide()
		"""

		def tmp_selected_changed():
			"""Fills in the name of the savegame in the textbox when selected in the list"""
			if self.current.collectData('savegamelist') != -1: # check if we actually collect valid data
				self.current.distributeData({'savegamefile' : \
				                             map_file_display[self.current.collectData('savegamelist')]})

		self.current.distributeInitialData({'savegamelist' : map_file_display})
		cb = Callback.ChainedCallbacks(Gui._create_show_savegame_details(self.current, map_files, 'savegamelist'), \
		                               tmp_selected_changed)
		self.current.findChild(name="savegamelist").mapEvents({
		    'savegamelist/action'              : cb,
		    'savegamelist/mouseWheelMovedUp'   : cb,
		    'savegamelist/mouseWheelMovedDown' : cb
		})
		self.current.findChild(name="savegamelist").capture(cb, event_name="keyPressed")

		retval = self.show_dialog(self.current, {
		                                          'okButton'     : True,
		                                          'cancelButton' : False,
		                                          'deleteButton' : 'delete',
		                                          'savegamefile' : True
		                                        },
		                                        onPressEscape = False)
		if not retval: # cancelled
			self.current = old_current
			return

		if retval == 'delete':
			# delete button was pressed. Apply delete and reshow dialog, delegating the return value
			self._delete_savegame(map_files)
			self.current = old_current
			return self.show_select_savegame(mode=mode)

		selected_savegame = None
		if mode == 'save': # return from textfield
			selected_savegame = self.current.collectData('savegamefile')
			if selected_savegame in map_file_display: # savegamename already exists
				message = _("A savegame with the name \"%s\" already exists. \nShould i overwrite it?") % selected_savegame
				if not self.show_popup(_("Confirmation for overwriting"),message,show_cancel_button = True):
					self.current = old_current
					return self.show_select_savegame(mode=mode) # reshow dialog
		else: # return selected item from list
			selected_savegame = self.current.collectData('savegamelist')
			selected_savegame = None if selected_savegame == -1 else map_files[selected_savegame]
			if selected_savegame is None:
				# ok button has been pressed, but no savegame was selected
				self.show_popup(_("Select a savegame"), _("Please select a savegame or click on cancel."));
				return self.show_select_savegame(mode=mode) # reshow dialog
		self.current = old_current # reuse old widget
		return selected_savegame

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

	def show_dialog(self, dlg, actions, onPressEscape = None, event_map = None):
		"""Shows any pychan dialog.
		@param dlg: dialog that is to be shown
		@param actions: actions that are executed by the dialog { 'ok': callback, 'cancel': callback }
		@param onPressEscape: callback that is to be called if the escape button is pressed
		@param event_map: dictionary with callbacks for buttons. See pychan docu: pychan.widget.mapEvents()
		"""
		self.current_dialog = dlg
		if event_map is not None:
			dlg.mapEvents(event_map)
		if onPressEscape is not None:
			def _escape(event):
				if event.getKey().getValue() == fife.Key.ESCAPE:
					pychan.internal.get_manager().breakFromMainLoop(onPressEscape)
					dlg.hide()
			dlg.capture(_escape, event_name="keyPressed")
		ret = dlg.execute(actions)
		return ret

	def show_popup(self, windowtitle, message, show_cancel_button = False):
		"""Displays a popup with the specified text
		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, show cancel button or not
		@return: True on ok, False on cancel (if no cancel button, always True)
		"""
		popup = self.build_popup(windowtitle, message, show_cancel_button)
		if show_cancel_button:
			return self.show_dialog(popup, {'okButton' : True, 'cancelButton' : False}, onPressEscape = False)
		else:
			return self.show_dialog(popup, {'okButton' : True}, onPressEscape = True)

	def show_error_popup(self, windowtitle, description, advice=None, details=None):
		"""Displays a popup containing an error message.
		@param windowtitle: title of popup, will be auto-prefixed with "Error: "
		@param description: string to tell the user what happened
		@param advice: how the user might be able to fix the problem
		@param details: technical details, relevant for debugging but not for the user

		Guide for writing good error messages:
		http://www.useit.com/alertbox/20010624.html
		"""
		msg = u""
		msg += description + u"\n"
		if advice:
			msg += advice + u"\n"
		if details:
			msg += _(u"Details:") + u" " + details
		self.show_popup( _(u"Error:") + u" " + windowtitle, msg, show_cancel_button=False)

	def build_popup(self, windowtitle, message, show_cancel_button = False):
		""" Creates a pychan popup widget with the specified properties.
		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, include cancel button or not
		@return: Container(name='popup_window') with buttons 'okButton' and optionally 'cancelButton'
		"""
		if show_cancel_button:
			popup = self.widgets['popup_with_cancel']
		else:
			popup = self.widgets['popup']
		headline = popup.findChild(name='headline')
		# just to be safe, the gettext-function is used twice,
		# once on the original, once on the unicode string.
		headline.text = _(_(windowtitle))
		popup.findChild(name='popup_message').text = _(_(message))
		popup.adaptLayout() # recalculate widths
		return popup

	def show_loading_screen(self):
		self._switch_current_widget('loadingscreen', center=True, show=True)

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
			old.hide()
		self.log.debug("Gui: setting current to %s", new_widget)
		self.current = self.widgets[new_widget]
		if center:
			self.current.position_technique="automatic" # "center:center"
		if event_map:
			self.current.mapEvents(event_map)
		if show:
			self.current.show()
		return old

	@staticmethod
	def _create_show_savegame_details(gui, map_files, savegamelist):
		"""Creates a function that displays details of a savegame in gui"""
		def tmp_show_details():
			"""Fetches details of selected savegame and displays it"""
			box = gui.findChild(name="savegamedetails_box")
			old_label = box.findChild(name="savegamedetails_lbl")
			if old_label is not None:
				box.removeChild(old_label)
			map_file = None
			try:
				map_file = map_files[gui.collectData(savegamelist)]
			except IndexError:
				# this was a click in the savegame list, but not on an element
				# it happens when the savegame list is empty
				return
			savegame_info = SavegameManager.get_metadata(map_file)
			details_label = pychan.widgets.Label(min_size=(140, 0), max_size=(140, 290), wrap_text=True)
			details_label.name = "savegamedetails_lbl"
			details_label.text = u""
			if savegame_info['timestamp'] == -1:
				details_label.text += _("Unknown savedate\n")
			else:
				details_label.text += _("Saved at %s\n") % \
										time.strftime(_("%H:%M, %A, %B %d"), time.localtime(savegame_info['timestamp']))
			counter = savegame_info['savecounter']
			# N_ takes care of plural forms for different languages
			details_label.text += N_("Saved %(counter)d time\n", \
			                         "Saved %(counter)d times\n", \
			                         counter) % {'counter':counter}
			details_label.stylize('book_t')

			from horizons.constants import VERSION
			try:
				if savegame_info['savegamerev'] == VERSION.SAVEGAMEREVISION:
					details_label.text += _("Savegame ver. %d") % ( savegame_info['savegamerev'] )
				else:
					details_label.text += _("WARNING: Incompatible ver. %(ver)d!\nNeed ver. %(need)d!") \
					             % {'ver' : savegame_info['savegamerev'], 'need' : VERSION.SAVEGAMEREVISION}
			except KeyError:
				details_label.text += _("INCOMPATIBLE VERSION\n")


			box.addChild( details_label )

			"""
			if savegame_info['screenshot']:
				fd, filename = tempfile.mkstemp()
				os.fdopen(fd, "w").write(savegame_info['screenshot'])
				box.addChild( pychan.widgets.Icon(image=filename) )
			"""

			gui.adaptLayout()
		return tmp_show_details

	def _delete_savegame(self, map_files):
		"""Deletes the selected savegame if the user confirms
		self.current has to contain the widget "savegamelist"
		@param map_files: list of files that corresponds to the entries of 'savegamelist'
		@return: True if something was deleted, else False
		"""
		selected_item = self.current.collectData("savegamelist")
		if selected_item == -1 or selected_item >= len(map_files):
			self.show_popup(_("No file selected"), _("You need to select a savegame to delete"))
			return False
		selected_file = map_files[selected_item]
		message = _('Do you really want to delete the savegame "%s"?') % \
		             SavegameManager.get_savegamename_from_filename(selected_file)
		if self.show_popup(_("Confirm deletion"), message, show_cancel_button = True):
			try:
				os.unlink(selected_file)
				return True
			except:
				self.show_popup(_("Error!"), _("Failed to delete savefile!"))
				return False
		else: # player cancelled deletion
			return False
