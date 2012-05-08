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
import os
import os.path
import random
import traceback
import time
import tempfile
import logging
from fife import fife
from fife.extensions import pychan

import horizons.main

from horizons.savegamemanager import SavegameManager
from horizons.gui.keylisteners import MainListener
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.widgets import OkButton, CancelButton, DeleteButton
from horizons.util import Callback
from horizons.extscheduler import ExtScheduler
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.util import LazyWidgetsDict

from horizons.gui.modules import SingleplayerMenu, MultiplayerMenu
from horizons.command.game import PauseCommand, UnPauseCommand

class Gui(SingleplayerMenu, MultiplayerMenu):
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
		build_help_strings(self.widgets['help'])
		self.session = None
		self.current_dialog = None

		self.dialog_executed = False

		self.__pause_displayed = False
		self._background_image = self._get_random_background()

# basic menu widgets

	def show_main(self):
		"""Shows the main menu """
		self._switch_current_widget('mainmenu', center=True, show=True, event_map={
			'startSingle'      : self.show_single, # first is the icon in menu
			'start'            : self.show_single, # second is the lable in menu
			'startMulti'       : self.show_multi,
			'start_multi'      : self.show_multi,
			'settingsLink'     : self.show_settings,
			'settings'         : self.show_settings,
			'helpLink'         : self.on_help,
			'help'             : self.on_help,
			'closeButton'      : self.show_quit,
			'quit'             : self.show_quit,
			'dead_link'        : self.on_chime, # call for help; SoC information
			'chimebell'        : self.on_chime,
			'creditsLink'      : self.show_credits,
			'credits'          : self.show_credits,
			'loadgameButton'   : horizons.main.load_game,
			'loadgame'         : horizons.main.load_game,
			'changeBackground' : self.get_random_background_by_button
		})

		self.on_escape = self.show_quit

	def toggle_pause(self):
		"""
		Show Pause menu
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

			# load transparent background, that de facto prohibits access to other
			# gui elements by eating all events
			height = horizons.main.fife.engine_settings.getScreenHeight()
			width = horizons.main.fife.engine_settings.getScreenWidth()
			image = horizons.main.fife.imagemanager.loadBlank(width,  height)
			image = fife.GuiImage(image)
			self.current.additional_widget = pychan.Icon(image=image)
			self.current.additional_widget.position = (0, 0)
			self.current.additional_widget.show()
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
		horizons.main.fife.show_settings()

	_help_is_displayed = False
	def on_help(self):
		"""Called on help action
		Toggles help screen via static variable help_is_displayed"""
		help_dlg = self.widgets['help']
		if not self._help_is_displayed:
			self._help_is_displayed = True
			# make game pause if there is a game and we're not in the main menu
			if self.session is not None and self.current != self.widgets['ingamemenu']:
				PauseCommand().execute(self.session)
			if self.session is not None:
				self.session.ingame_gui.on_escape() # close dialogs that might be open
			self.show_dialog(help_dlg, {OkButton.DEFAULT_NAME : True})
			self.on_help() # toggle state
		else:
			self._help_is_displayed = False
			if self.session is not None and self.current != self.widgets['ingamemenu']:
				UnPauseCommand().execute(self.session)
			help_dlg.hide()

	def show_quit(self):
		"""Shows the quit dialog """
		message = _("Are you sure you want to quit Unknown Horizons?")
		if self.show_popup(_("Quit Game"), message, show_cancel_button=True):
			horizons.main.quit()

	def quit_session(self, force=False):
		"""Quits the current session.
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

	def on_chime(self):
		"""
		Called chime action. Displaying call for help on artists and game design,
		introduces information for SoC applicants (if valid).
		"""
		AmbientSoundComponent.play_special("message")
		self.show_dialog(self.widgets['call_for_support'], {OkButton.DEFAULT_NAME : True})

	def show_credits(self, number=0):
		"""Shows the credits dialog. """
		for box in self.widgets['credits'+str(number)].findChildren(name='box'):
			box.margins = (30, 0) # to get some indentation
			if number in [2, 0]: # #TODO fix this hardcoded translators page ref
				box.padding = 1 # further decrease if more entries
				box.parent.padding = 3 # see above
		label = [self.widgets['credits'+str(number)].findChild(name=section+"_lbl") \
		              for section in ('team','patchers','translators','packagers','special_thanks')]
		for i in xrange(5):
			if label[i]: # add callbacks to each pickbelt that is displayed
				label[i].capture(Callback(self.show_credits, i),
				                 event_name="mouseClicked")

		if self.current_dialog is not None:
			self.current_dialog.hide()
		self.show_dialog(self.widgets['credits'+str(number)], {OkButton.DEFAULT_NAME : True})

	def show_select_savegame(self, mode, sanity_checker=None, sanity_criteria=None):
		"""Shows menu to select a savegame.
		@param mode: 'save', 'load' or 'mp_load'
		@param sanity_checker: only allow manually entered names that pass this test
		@param sanity_criteria: explain which names are allowed to the user
		@return: Path to savegamefile or None"""
		assert mode in ('save', 'load', 'mp_load', 'mp_save')
		map_files, map_file_display = None, None
		mp = False
		args = mode, sanity_checker, sanity_criteria # for reshow
		if mode.startswith('mp'):
			mode = mode[3:]
			mp = True
			# below this line, mp_load == load, mp_save == save
		if mode == 'load':
			if not mp:
				map_files, map_file_display = SavegameManager.get_saves()
			else:
				map_files, map_file_display = SavegameManager.get_multiplayersaves()
			if len(map_files) == 0:
				self.show_popup(_("No saved games"), _("There are no saved games to load."))
				return
		else: # don't show autosave and quicksave on save
			if not mp:
				map_files, map_file_display = SavegameManager.get_regular_saves()
			else:
				map_files, map_file_display = SavegameManager.get_multiplayersaves()

		# Prepare widget
		old_current = self._switch_current_widget('select_savegame')
		self.current.findChild(name='headline').text = _('Save game') if mode == 'save' else _('Load game')
		self.current.findChild(name=OkButton.DEFAULT_NAME).helptext = _('Save game') if mode == 'save' else _('Load game')

		name_box = self.current.findChild(name="gamename_box")
		if mp and mode == 'load': # have gamename
			name_box.parent.showChild(name_box)
			gamename_textfield = self.current.findChild(name="gamename")
			def clear_gamename_textfield():
				gamename_textfield.text = u""
			gamename_textfield.capture(clear_gamename_textfield, 'mouseReleased', 'default')
		else:
			if name_box not in name_box.parent.hidden_children:
				name_box.parent.hideChild(name_box)

		self.current.show()

		if not hasattr(self, 'filename_hbox'):
			self.filename_hbox = self.current.findChild(name='enter_filename')
			self.filename_hbox_parent = self.filename_hbox._getParent()

		if mode == 'save': # only show enter_filename on save
			self.filename_hbox_parent.showChild(self.filename_hbox)
		elif self.filename_hbox not in self.filename_hbox_parent.hidden_children:
			self.filename_hbox_parent.hideChild(self.filename_hbox)

		def tmp_selected_changed():
			"""Fills in the name of the savegame in the textbox when selected in the list"""
			if mode == 'save': # set textbox only if we are in save mode
				if self.current.collectData('savegamelist') == -1: # set blank if nothing is selected
					self.current.findChild(name="savegamefile").text = u""
				else:
					self.current.distributeData({'savegamefile' : \
				                             map_file_display[self.current.collectData('savegamelist')]})

		self.current.distributeInitialData({'savegamelist' : map_file_display})
		self.current.distributeData({'savegamelist' : -1}) # Don't select anything by default
		cb = Callback.ChainedCallbacks(Gui._create_show_savegame_details(self.current, map_files, 'savegamelist'), \
		                               tmp_selected_changed)
		cb() # Refresh data on start
		self.current.findChild(name="savegamelist").mapEvents({
		    'savegamelist/action'              : cb
		})
		self.current.findChild(name="savegamelist").capture(cb, event_name="keyPressed")

		bind = {
			OkButton.DEFAULT_NAME     : True,
			CancelButton.DEFAULT_NAME : False,
			DeleteButton.DEFAULT_NAME : 'delete'
		}

		if mode == 'save':
			bind['savegamefile'] = True

		retval = self.show_dialog(self.current, bind)
		if not retval: # cancelled
			self.current = old_current
			return

		if retval == 'delete':
			# delete button was pressed. Apply delete and reshow dialog, delegating the return value
			delete_retval = self._delete_savegame(map_files)
			if delete_retval:
				self.current.distributeData({'savegamelist' : -1})
				cb()
			self.current = old_current
			return self.show_select_savegame(*args)

		selected_savegame = None
		if mode == 'save': # return from textfield
			selected_savegame = self.current.collectData('savegamefile')
			if selected_savegame == "":
				self.show_error_popup(windowtitle=_("No filename given"), description=_("Please enter a valid filename."))
				self.current = old_current
				return self.show_select_savegame(*args) # reshow dialog
			elif selected_savegame in map_file_display: # savegamename already exists
				#xgettext:python-format
				message = _("A savegame with the name '{name}' already exists.").format(
				             name=selected_savegame) + u"\n" + _('Overwrite it?')
				if not self.show_popup(_("Confirmation for overwriting"), message, show_cancel_button=True):
					self.current = old_current
					return self.show_select_savegame(*args) # reshow dialog
			elif sanity_checker and sanity_criteria:
				if not sanity_checker(selected_savegame):
					self.show_error_popup(windowtitle=_("Invalid filename given"), description=sanity_criteria)
					self.current = old_current
					return self.show_select_savegame(*args) # reshow dialog
		else: # return selected item from list
			selected_savegame = self.current.collectData('savegamelist')
			selected_savegame = None if selected_savegame == -1 else map_files[selected_savegame]
			if selected_savegame is None:
				# ok button has been pressed, but no savegame was selected
				self.show_popup(_("Select a savegame"), _("Please select a savegame or click on cancel."))
				self.current = old_current
				return self.show_select_savegame(*args) # reshow dialog

		if mp and mode == 'load': # also name
			gamename_textfield = self.current.findChild(name="gamename")
			ret = selected_savegame, self.current.collectData('gamename')
		else:
			ret = selected_savegame
		self.current = old_current # reuse old widget
		return ret

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
			try:
				self.current.additional_widget.hide()
				del self.current.additional_widget
			except AttributeError:
				pass # only used for some widgets, e.g. pause

	def is_visible(self):
		return self.current is not None and self.current.isVisible()


	def show_dialog(self, dlg, bind, event_map=None):
		"""Shows any pychan dialog.
		@param dlg: dialog that is to be shown
		@param bind: events that make the dialog return + return values{ 'ok': callback, 'cancel': callback }
		@param event_map: dictionary with callbacks for buttons. See pychan docu: pychan.widget.mapEvents()
		"""
		self.current_dialog = dlg
		if event_map is not None:
			dlg.mapEvents(event_map)

		# handle escape and enter keypresses
		def _on_keypress(event, dlg=dlg): # rebind to make sure this dlg is used
			from horizons.engine import pychan_util
			if event.getKey().getValue() == fife.Key.ESCAPE: # convention says use cancel action
				btn = dlg.findChild(name=CancelButton.DEFAULT_NAME)
				callback = pychan_util.get_button_event(btn) if btn else None
				if callback:
					callback()
				else:
					# escape should hide the dialog default
					pychan.internal.get_manager().breakFromMainLoop(returnValue=False)
					dlg.hide()
			elif event.getKey().getValue() == fife.Key.ENTER: # convention says use ok action
				btn = dlg.findChild(name=OkButton.DEFAULT_NAME)
				callback = pychan_util.get_button_event(btn) if btn else None
				if callback:
					callback()
				# can't guess a default action here

		dlg.capture(_on_keypress, event_name="keyPressed")

		# show that a dialog is being executed, this can sometimes require changes in program logic elsewhere
		self.dialog_executed = True
		ret = dlg.execute(bind)
		self.dialog_executed = False
		return ret

	def show_popup(self, windowtitle, message, show_cancel_button=False, size=0):
		"""Displays a popup with the specified text
		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, show cancel button or not
		@param size: 0, 1 or 2. Larger means bigger.
		@return: True on ok, False on cancel (if no cancel button, always True)
		"""
		popup = self.build_popup(windowtitle, message, show_cancel_button, size=size)
		# ok should be triggered on enter, therefore we need to focus the button
		# pychan will only allow it after the widgets is shown
		ExtScheduler().add_new_object(lambda : popup.findChild(name=OkButton.DEFAULT_NAME).requestFocus(), self, run_in=0)
		if show_cancel_button:
			return self.show_dialog(popup,{OkButton.DEFAULT_NAME : True,
			                               CancelButton.DEFAULT_NAME : False})
		else:
			return self.show_dialog(popup, {OkButton.DEFAULT_NAME : True})

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
			msg += _(u"Details:") + u" " + details
		try:
			self.show_popup( _(u"Error:") + u" " + windowtitle, msg, show_cancel_button=False)
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
			self.hide()
		self.log.debug("Gui: setting current to %s", new_widget)
		self.current = self.widgets[new_widget]
		# Set background image
		bg = self.current.findChild(name='background')
		if bg:
			bg.image = self._background_image

		if center:
			self.current.position_technique = "automatic" # "center:center"
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
			gui.findChild(name="screenshot").image = None
			box = gui.findChild(name="savegamedetails_box")
			old_label = box.findChild(name="savegamedetails_lbl")
			if old_label is not None:
				box.removeChild(old_label)
			map_file = None
			map_file_index = gui.collectData(savegamelist)
			if map_file_index == -1:
				return
			try:
				map_file = map_files[map_file_index]
			except IndexError:
				# this was a click in the savegame list, but not on an element
				# it happens when the savegame list is empty
				return
			savegame_info = SavegameManager.get_metadata(map_file)

			# screenshot (len can be 0 if save failed in a weird way)
			if 'screenshot' in savegame_info and \
			   savegame_info['screenshot'] is not None and \
			   len(savegame_info['screenshot']) > 0:
				# try to find a writeable location, that is accessible via relative paths
				# (required by fife)
				fd, filename = tempfile.mkstemp()
				try:
					path_rel = os.path.relpath(filename)
				except ValueError: # the relative path sometimes doesn't exist on win
					os.close(fd)
					os.unlink(filename)
					# try again in the current dir, it's often writable
					fd, filename = tempfile.mkstemp(dir=os.curdir)
					try:
						path_rel = os.path.relpath(filename)
					except ValueError:
						fd, filename = None, None

				if fd:
					with os.fdopen(fd, "w") as f:
						f.write(savegame_info['screenshot'])
					# fife only supports relative paths
					gui.findChild(name="screenshot").image = path_rel
					os.unlink(filename)

			# savegamedetails
			details_label = pychan.widgets.Label(min_size=(290, 0), max_size=(290, 290), wrap_text=True)
			details_label.name = "savegamedetails_lbl"
			details_label.text = u""
			if savegame_info['timestamp'] == -1:
				details_label.text += _("Unknown savedate")
			else:
				#xgettext:python-format
				details_label.text += _("Saved at {time}").format(
				                         time=time.strftime("%c",
				                         time.localtime(savegame_info['timestamp'])).decode('utf-8'))
			details_label.text += u'\n'
			counter = savegame_info['savecounter']
			# N_ takes care of plural forms for different languages
			#xgettext:python-format
			details_label.text += N_("Saved {amount} time",
			                         "Saved {amount} times",
			                         counter).format(amount=counter)
			details_label.text += u'\n'
			details_label.stylize('book_t')

			from horizons.constants import VERSION
			try:
				#xgettext:python-format
				details_label.text += _("Savegame version {version}").format(
				                         version=savegame_info['savegamerev'])
				if savegame_info['savegamerev'] != VERSION.SAVEGAMEREVISION:
					#xgettext:python-format
					details_label.text += u" " + _("(potentially incompatible)")
			except KeyError:
				# this should only happen for very old savegames, so having this unfriendly
				# error is ok (savegame is quite certainly fully unusable).
				details_label.text += _("Incompatible version")


			box.addChild( details_label )


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
			self.show_popup(_("No file selected"), _("You need to select a savegame to delete."))
			return False
		selected_file = map_files[selected_item]
		#xgettext:python-format
		message = _("Do you really want to delete the savegame '{name}'?").format(
		             name=SavegameManager.get_savegamename_from_filename(selected_file))
		if self.show_popup(_("Confirm deletion"), message, show_cancel_button=True):
			try:
				os.unlink(selected_file)
				return True
			except:
				self.show_popup(_("Error!"), _("Failed to delete savefile!"))
				return False
		else: # player cancelled deletion
			return False

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
		latest_background = horizons.main.fife.get_uh_setting("LatestBackground")
		#if there is a latest background then remove it from available list
		if latest_background is not None:
			available_images.remove(latest_background)
		background_choice = random.choice(available_images)
		#save current background choice
		horizons.main.fife.set_uh_setting("LatestBackground", background_choice)
		horizons.main.fife.save_settings()
		return background_choice

def build_help_strings(widgets):
	"""
	Loads the help strings from pychan object widgets (containing no key definitions)
	and adds 	the keys defined in the keyconfig configuration object in front of them.
	The layout is defined through HELPSTRING_LAYOUT and translated.
	"""
	#i18n this defines how each line in our help looks like. Default: '[C] = Chat'
	#xgettext:python-format
	HELPSTRING_LAYOUT = _('[{key}] = {text}')

	#HACK Ugliness starts; load actions defined through keys and map them to FIFE key strings
	actions = KeyConfig._Actions.__dict__
	reversed_keys = dict([[str(v),k] for k,v in fife.Key.__dict__.iteritems()])
	reversed_stringmap = dict([[str(v),k] for k,v in KeyConfig().keystring_mappings.iteritems()])
	reversed_keyvalmap = dict([[str(v), reversed_keys[str(k)]] for k,v in KeyConfig().keyval_mappings.iteritems()])
	actionmap = dict(reversed_stringmap, **reversed_keyvalmap)
	#HACK Ugliness ends here; These hacks can be removed once a config file exists which is nice to parse.

	labels = widgets.getNamedChildren()
	# filter misc labels that do not describe key functions
	labels = dict( [(name, lbl) for (name, lbl) in labels.items() if name.startswith('lbl_')] )

	# now prepend the actual keys to the function strings defined in xml
	for (name, lbl) in labels.items():
		try:
			keyname = '{key}'.format(key=actionmap[str(actions[name[4:]])])
		except KeyError:
			keyname = ' '
		lbl[0].text = HELPSTRING_LAYOUT.format(text=_(lbl[0].text), key=keyname.upper())

	author_label = widgets.findChild(name='fife_and_uh_team')
	author_label.helptext = u"www.unknown-[br]horizons.org[br]www.fifengine.net"
