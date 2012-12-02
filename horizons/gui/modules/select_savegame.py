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

import os
import os.path
import tempfile
import time

from horizons.gui.widgets.imagebutton import OkButton, CancelButton, DeleteButton
from horizons.savegamemanager import SavegameManager
from horizons.util.python.callback import Callback
from horizons.util.savegameupgrader import SavegameUpgrader


class SelectSavegameDialog(object):

	def __init__(self, mainmenu):
		self.mainmenu = mainmenu

	def show_select_savegame(self, mode, sanity_checker=None, sanity_criteria=None):
		"""Shows menu to select a savegame.
		@param mode: Valid options are 'save', 'load', 'mp_load', 'mp_save'
		@param sanity_checker: only allow manually entered names that pass this test
		@param sanity_criteria: explain which names are allowed to the user
		@return: Path to savegamefile or None"""
		assert mode in ('save', 'load', 'mp_load', 'mp_save')
		map_files, map_file_display = None, None
		args = mode, sanity_checker, sanity_criteria # for reshow
		mp = mode.startswith('mp_')
		if mp:
			mode = mode[3:]
		# below this line, mp_load == load, mp_save == save
		if mode == 'load':
			if not mp:
				map_files, map_file_display = SavegameManager.get_saves()
			else:
				map_files, map_file_display = SavegameManager.get_multiplayersaves()
			if not map_files:
				self.mainmenu.show_popup(_("No saved games"), _("There are no saved games to load."))
				return
		else: # don't show autosave and quicksave on save
			if not mp:
				map_files, map_file_display = SavegameManager.get_regular_saves()
			else:
				map_files, map_file_display = SavegameManager.get_multiplayersaves()

		# Prepare widget
		old_current = self.mainmenu._switch_current_widget('select_savegame')
		self.current = self.mainmenu.current
		if mode == 'save':
			helptext = _('Save game')
		elif mode == 'load':
			helptext = _('Load game')
		# else: not a valid mode, so we can as well crash on the following
		self.current.findChild(name='headline').text = helptext
		self.current.findChild(name=OkButton.DEFAULT_NAME).helptext = helptext

		name_box = self.current.findChild(name="gamename_box")
		password_box = self.current.findChild(name="gamepassword_box")
		if mp and mode == 'load': # have gamename
			name_box.parent.showChild(name_box)
			password_box.parent.showChild(password_box)
			gamename_textfield = self.current.findChild(name="gamename")
			gamepassword_textfield = self.current.findChild(name="gamepassword")
			gamepassword_textfield.text = u""
			def clear_gamedetails_textfields():
				gamename_textfield.text = u""
				gamepassword_textfield.text = u""
			gamename_textfield.capture(clear_gamedetails_textfields, 'mouseReleased', 'default')
		else:
			if name_box not in name_box.parent.hidden_children:
				name_box.parent.hideChild(name_box)
			if password_box not in name_box.parent.hidden_children:
				password_box.parent.hideChild(password_box)

		self.current.show()

		if not hasattr(self, 'filename_hbox'):
			self.filename_hbox = self.current.findChild(name='enter_filename')
			self.filename_hbox_parent = self.filename_hbox.parent

		if mode == 'save': # only show enter_filename on save
			self.filename_hbox_parent.showChild(self.filename_hbox)
		elif self.filename_hbox not in self.filename_hbox_parent.hidden_children:
			self.filename_hbox_parent.hideChild(self.filename_hbox)

		def tmp_selected_changed():
			"""Fills in the name of the savegame in the textbox when selected in the list"""
			if mode != 'save': # set textbox only if we are in save mode
				return
			if self.current.collectData('savegamelist') == -1: # set blank if nothing is selected
				self.current.findChild(name="savegamefile").text = u""
			else:
				savegamefile = map_file_display[self.current.collectData('savegamelist')]
				self.current.distributeData({'savegamefile': savegamefile})

		self.current.distributeInitialData({'savegamelist': map_file_display})
		# Select first item when loading, nothing when saving
		selected_item = -1 if mode == 'save' else 0
		self.current.distributeData({'savegamelist': selected_item})
		cb_details = self._create_show_savegame_details(self.current, map_files, 'savegamelist')
		cb = Callback.ChainedCallbacks(cb_details, tmp_selected_changed)
		cb() # Refresh data on start
		self.current.mapEvents({'savegamelist/action': cb})
		self.current.findChild(name="savegamelist").capture(cb, event_name="keyPressed")

		bind = {
			OkButton.DEFAULT_NAME     : True,
			CancelButton.DEFAULT_NAME : False,
			DeleteButton.DEFAULT_NAME : 'delete'
		}

		if mode == 'save':
			bind['savegamefile'] = True

		retval = self.mainmenu.show_dialog(self.current, bind)
		if not retval: # cancelled
			self.current = old_current
			return

		if retval == 'delete':
			# delete button was pressed. Apply delete and reshow dialog, delegating the return value
			delete_retval = self._delete_savegame(map_files)
			if delete_retval:
				self.current.distributeData({'savegamelist' : -1})
				cb()
			self.mainmenu.current = old_current
			return self.show_select_savegame(*args)

		selected_savegame = None
		if mode == 'save': # return from textfield
			selected_savegame = self.current.collectData('savegamefile')
			if selected_savegame == "":
				self.mainmenu.show_error_popup(windowtitle=_("No filename given"),
				                               description=_("Please enter a valid filename."))
				self.mainmenu.current = old_current
				return self.show_select_savegame(*args) # reshow dialog
			elif selected_savegame in map_file_display: # savegamename already exists
				#xgettext:python-format
				message = _("A savegame with the name '{name}' already exists.").format(
				             name=selected_savegame) + u"\n" + _('Overwrite it?')
				# keep the pop-up non-modal because otherwise it is double-modal (#1876)
				if not self.mainmenu.show_popup(_("Confirmation for overwriting"), message, show_cancel_button=True, modal=False):
					self.mainmenu.current = old_current
					return self.show_select_savegame(*args) # reshow dialog
			elif sanity_checker and sanity_criteria:
				if not sanity_checker(selected_savegame):
					self.mainmenu.show_error_popup(windowtitle=_("Invalid filename given"),
					                               description=sanity_criteria)
					self.mainmenu.current = old_current
					return self.show_select_savegame(*args) # reshow dialog
		else: # return selected item from list
			selected_savegame = self.current.collectData('savegamelist')
			assert selected_savegame != -1, "No savegame selected in savegamelist"
			selected_savegame = map_files[selected_savegame]

		if mp and mode == 'load': # also name
			gamename_textfield = self.current.findChild(name="gamename")
			ret = selected_savegame, self.current.collectData('gamename'), self.current.collectData('gamepassword')
		else:
			ret = selected_savegame
		self.mainmenu.current = old_current # reuse old widget
		return ret

	def _create_show_savegame_details(self, gui, map_files, savegamelist):
		"""Creates a function that displays details of a savegame in gui"""

		def tmp_show_details():
			"""Fetches details of selected savegame and displays it"""
			gui.findChild(name="screenshot").image = None
			map_file = None
			map_file_index = gui.collectData(savegamelist)
			if map_file_index == -1:
				gui.findChild(name="savegame_details").hide()
				return
			else:
				gui.findChild(name="savegame_details").show()
			try:
				map_file = map_files[map_file_index]
			except IndexError:
				# this was a click in the savegame list, but not on an element
				# it happens when the savegame list is empty
				return
			savegame_info = SavegameManager.get_metadata(map_file)

			if savegame_info.get('screenshot'):
				# try to find a writable location, that is accessible via relative paths
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
			details_label = gui.findChild(name="savegamedetails_lbl")
			details_label.text = u""
			if savegame_info['timestamp'] == -1:
				details_label.text += _("Unknown savedate")
			else:
				savetime = time.strftime("%c", time.localtime(savegame_info['timestamp']))
				#xgettext:python-format
				details_label.text += _("Saved at {time}").format(time=savetime.decode('utf-8'))
			details_label.text += u'\n'
			counter = savegame_info['savecounter']
			# N_ takes care of plural forms for different languages
			#xgettext:python-format
			details_label.text += N_("Saved {amount} time",
			                         "Saved {amount} times",
			                         counter).format(amount=counter)
			details_label.text += u'\n'
			details_label.stylize('book')

			from horizons.constants import VERSION
			try:
				#xgettext:python-format
				details_label.text += _("Savegame version {version}").format(
				                         version=savegame_info['savegamerev'])
				if savegame_info['savegamerev'] != VERSION.SAVEGAMEREVISION:
					if not SavegameUpgrader.can_upgrade(savegame_info['savegamerev']):
						details_label.text += u" " + _("(probably incompatible)")
			except KeyError:
				# this should only happen for very old savegames, so having this unfriendly
				# error is ok (savegame is quite certainly fully unusable).
				details_label.text += u" " + _("Incompatible version")

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
			self.mainmenu.show_popup(_("No file selected"), _("You need to select a savegame to delete."))
			return False
		selected_file = map_files[selected_item]
		#xgettext:python-format
		message = _("Do you really want to delete the savegame '{name}'?").format(
		             name=SavegameManager.get_savegamename_from_filename(selected_file))
		if self.mainmenu.show_popup(_("Confirm deletion"), message, show_cancel_button=True):
			try:
				os.unlink(selected_file)
				return True
			except:
				self.mainmenu.show_popup(_("Error!"), _("Failed to delete savefile!"))
				return False
		else: # player cancelled deletion
			return False
