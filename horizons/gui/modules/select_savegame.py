# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from fife import fife

from horizons.engine import Fife
from horizons.extscheduler import ExtScheduler
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import CancelButton, DeleteButton, OkButton
from horizons.gui.windows import Dialog
from horizons.i18n import gettext as _, ngettext as N_
from horizons.savegamemanager import SavegameManager
from horizons.util.python.callback import Callback
from horizons.util.savegameupgrader import SavegameUpgrader


class SelectSavegameDialog(Dialog):

	def __init__(self, mode, windows):
		super(SelectSavegameDialog, self).__init__(windows)

		assert mode in ('load', 'save', 'editor-save')
		self._mode = mode

		self._gui = load_uh_widget('select_savegame.xml')

		if self._mode == 'save':
			helptext = _('Save game')
		elif self._mode == 'load':
			helptext = _('Load game')
		elif self._mode == 'editor-save':
			helptext = _('Save map')
		self._gui.findChild(name='headline').text = helptext
		self._gui.findChild(name=OkButton.DEFAULT_NAME).helptext = helptext

		w = self._gui.findChild(name="gamename_box")
		if (Fife.getVersion() >= (0, 4, 0)):
			w.parent.hideChild(w)
		else:
			if w not in w.parent.hidden_children:
				w.parent.hideChild(w)

		w = self._gui.findChild(name="gamepassword_box")
		if (Fife.getVersion() >= (0, 4, 0)):
			w.parent.hideChild(w)
		else:
			if w not in w.parent.hidden_children:
				w.parent.hideChild(w)

		w = self._gui.findChild(name='enter_filename')
		if self._mode in ('save', 'editor-save'): # only show enter_filename on save
			w.parent.showChild(w)
		else:
			if (Fife.getVersion() >= (0, 4, 0)):
				w.parent.hideChild(w)
			else:
				if w not in w.parent.hidden_children:
					w.parent.hideChild(w)

		self.last_click_event = None

	def prepare(self):
		if self._mode == 'load':
			self._map_files, self._map_file_display = SavegameManager.get_saves()
			if not self._map_files:
				self._windows.open_popup(_("No saved games"), _("There are no saved games to load."))
				return False
		elif self._mode == 'save':
			self._map_files, self._map_file_display = SavegameManager.get_regular_saves()
		elif self._mode == 'editor-save':
			self._map_files, self._map_file_display = SavegameManager.get_maps()

		self._gui.distributeInitialData({'savegamelist': self._map_file_display})
		if self._mode == 'load':
			self._gui.distributeData({'savegamelist': 0})

		self._cb = self._create_show_savegame_details(self._gui, self._map_files, 'savegamelist')
		if self._mode in ('save', 'editor-save'):
			def selected_changed():
				"""Fills in the name of the savegame in the textbox when selected in the list"""
				if self._gui.collectData('savegamelist') == -1: # set blank if nothing is selected
					self._gui.findChild(name="savegamefile").text = u""
				else:
					savegamefile = self._map_file_display[self._gui.collectData('savegamelist')]
					self._gui.distributeData({'savegamefile': savegamefile})

			self._cb = Callback.ChainedCallbacks(self._cb, selected_changed)

		self._cb()  # Refresh data on start
		self._gui.mapEvents({'savegamelist/action': self._cb})
		self._gui.findChild(name="savegamelist").capture(self._cb, event_name="keyPressed")
		self._gui.findChild(name="savegamelist").capture(self.check_double_click, event_name="mousePressed")

		self.return_events = {
			OkButton.DEFAULT_NAME    : True,
			CancelButton.DEFAULT_NAME: False,
			DeleteButton.DEFAULT_NAME: 'delete'
		}
		if self._mode in ('save', 'editor-save'):
			self.return_events['savegamefile'] = True

	def check_double_click(self, event):
		"""Apply OK button if there was a left double click"""
		if event.getButton() != fife.MouseEvent.LEFT:
			return
		if self.last_click_event == (event.getX(), event.getY()) and self.clicked:
			self.clicked = False
			ExtScheduler().rem_call(self, self.reset_click_status)
			self.trigger_close(OkButton.DEFAULT_NAME)
		else:
			self.clicked = True
			ExtScheduler().add_new_object(self.reset_click_status, self, run_in=0.3, loops=0)
			self.last_click_event = (event.getX(), event.getY())

	def reset_click_status(self):
		"""Callback function to reset the click status by Scheduler"""
		self.clicked = False

	def act(self, retval):
		if not retval:  # cancelled
			return

		if retval == 'delete':
			# delete button was pressed. Apply delete and reshow dialog, delegating the return value
			delete_retval = self._delete_savegame(self._map_files)
			if delete_retval:
				self._gui.distributeData({'savegamelist' : -1})
				self._cb()
			return self._windows.open(self)

		selected_savegame = None
		if self._mode in ('save', 'editor-save'):  # return from textfield
			selected_savegame = self._gui.collectData('savegamefile')
			if selected_savegame == "":
				self._windows.open_error_popup(windowtitle=_("No filename given"),
				                               description=_("Please enter a valid filename."))
				return self._windows.open(self)
			elif selected_savegame in self._map_file_display: # savegamename already exists
				if self._mode == 'save':
					message = _("A savegame with the name {name} already exists.")
				elif self._mode == 'editor-save':
					message = _("A map with the name {name} already exists.")
				message = message.format(name=selected_savegame)
				message += u"\n" + _('Overwrite it?')
				# keep the pop-up non-modal because otherwise it is double-modal (#1876)
				if not self._windows.open_popup(_("Confirmation for overwriting"), message, show_cancel_button=True):
					return self._windows.open(self)

		elif self._mode == 'load':  # return selected item from list
			selected_savegame = self._gui.collectData('savegamelist')
			assert selected_savegame != -1, "No savegame selected in savegamelist"
			selected_savegame = self._map_files[selected_savegame]

		return selected_savegame

	def _create_show_savegame_details(self, gui, map_files, savegamelist):
		"""Creates a function that displays details of a savegame in gui"""

		def tmp_show_details():
			"""Fetches details of selected savegame and displays it"""
			gui.findChild(name="screenshot").image = None
			map_file = None
			map_file_index = gui.collectData(savegamelist)

			savegame_details_box = gui.findChild(name="savegame_details")
			savegame_details_parent = savegame_details_box.parent
			if map_file_index == -1:
				if (Fife.getVersion() >= (0, 4, 0)):
					savegame_details_parent.hideChild(savegame_details_box)
				else:
					if savegame_details_box not in savegame_details_parent.hidden_children:
						savegame_details_parent.hideChild(savegame_details_box)
				return
			else:
				savegame_details_parent.showChild(savegame_details_box)
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
				details_label.text += _("Saved at {time}").format(time=savetime.decode('utf-8'))
			details_label.text += u'\n'
			counter = savegame_info['savecounter']
			# N_ takes care of plural forms for different languages
			details_label.text += N_("Saved {amount} time",
			                         "Saved {amount} times",
			                         counter).format(amount=counter)
			details_label.text += u'\n'

			from horizons.constants import VERSION
			try:
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
		self._gui has to contain the widget "savegamelist"
		@param map_files: list of files that corresponds to the entries of 'savegamelist'
		@return: True if something was deleted, else False
		"""
		selected_item = self._gui.collectData("savegamelist")
		if selected_item == -1 or selected_item >= len(map_files):
			self._windows.open_popup(_("No file selected"), _("You need to select a savegame to delete."))
			return False
		selected_file = map_files[selected_item]
		message = _("Do you really want to delete the savegame '{name}'?").format(
		             name=SavegameManager.get_savegamename_from_filename(selected_file))
		if self._windows.open_popup(_("Confirm deletion"), message, show_cancel_button=True):
			try:
				os.unlink(selected_file)
				return True
			except:
				self._windows.open_popup(_("Error!"), _("Failed to delete savefile!"))
				return False
		else: # player cancelled deletion
			return False
