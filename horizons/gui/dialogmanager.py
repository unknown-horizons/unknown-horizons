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

import traceback

from horizons.extscheduler import ExtScheduler
from horizons.gui.widgets.imagebutton import OkButton, CancelButton


class DialogManager(object):

	def __init__(self, widgets):
		self._dialogs = []
		self._widgets = widgets

	def show(self, widget, **kwargs):
		"""Show a new dialog on top.
		
		Hide the current one and show the new one.
		"""
		# TODO for popups, we sometimes want the old widget to stay visible
		print 'DialogManager show', widget

		self.hide()
		self._dialogs.append(widget)
		return widget.show(**kwargs)

	def replace(self, widget, **kwargs):
		"""Replace the top dialog with this widget.

		So far, this seems to be needed by the credits dialog.
		"""
		print 'DialogManager replace', widget
		self.close()
		return self.show(widget, **kwargs)

	def close(self):
		"""Close the top dialog.
		
		If there is another dialog left, show it.
		"""
		widget = self._dialogs.pop()
		print 'DialogManager close', widget
		widget.close()
		if self._dialogs:
			self._dialogs[-1].show()

	def hide(self):
		"""Attempt to hide the current dialog.
		
		A dialog that does not permit other dialogs on top of it will be closed,
		any other will be hidden.
		"""
		print 'DialogManager hide'
		if not self._dialogs:
			return

		if not self._dialogs[-1].stackable:
			print 'DialogManager close top'
			self.close()
		else:
			print 'DialogManager hide top'
			self._dialogs[-1].hide()

	def toggle(self, widget):
		print 'DialogManager toggle', widget
		if widget.stackable:
			# This means that the widget might still be somewhere in our stack.
			# We can only toggle dialogs that are closed immediately when losing
			# focus.
			raise Exception('This should not be possible')

		if self._dialogs and self._dialogs[-1] == widget:
			print 'DialogManager toggle abort non stackable'
			self._dialogs[-1].abort()
		else:
			print 'DialogManager toggle show'
			self.show(widget)

	# TODO we can probably move the popup building into a separate class next to Dialog

	def show_popup(self, windowtitle, message, show_cancel_button=False, size=0, modal=True):
		"""Displays a popup with the specified text
		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, show cancel button or not
		@param size: 0, 1 or 2. Larger means bigger.
		@param modal: Whether to block user interaction while displaying the popup
		@return: True on ok, False on cancel (if no cancel button, always True)
		"""
		popup = self._build_popup(windowtitle, message, show_cancel_button, size=size)
		# ok should be triggered on enter, therefore we need to focus the button
		# pychan will only allow it after the widgets is shown
		def focus_ok_button():
			popup.findChild(name=OkButton.DEFAULT_NAME).requestFocus()
		ExtScheduler().add_new_object(focus_ok_button, self, run_in=0)
		if show_cancel_button:
			return self._show_dialog(popup, {OkButton.DEFAULT_NAME : True,
			                                CancelButton.DEFAULT_NAME : False},
			                         modal=modal)
		else:
			return self._show_dialog(popup, {OkButton.DEFAULT_NAME : True},
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
			return self._show_popup( _("Error: {error_message}").format(error_message=windowtitle),
			                        msg, show_cancel_button=False)
		except SystemExit: # user really wants us to die
			raise
		except:
			# could be another game error, try to be persistent in showing the error message
			# else the game would be gone without the user being able to read the message.
			if _first:
				traceback.print_exc()
				print 'Exception while showing error, retrying once more'
				return self._show_error_popup(windowtitle, description, advice, details, _first=False)
			else:
				raise # it persists, we have to die.

	def _build_popup(self, windowtitle, message, show_cancel_button=False, size=0):
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
		self._widgets.reload(wdg_name)
		popup = self._widgets[wdg_name]

		if not show_cancel_button:
			cancel_button = popup.findChild(name=CancelButton.DEFAULT_NAME)
			cancel_button.parent.removeChild(cancel_button)

		headline = popup.findChild(name='headline')
		headline.text = _(windowtitle)
		popup.findChild(name='popup_message').text = _(message)
		popup.adaptLayout() # recalculate widths
		return popup

	def _show_dialog(self, dlg, bind, event_map=None, modal=False):
		# TODO ugly, see todo above about moving the popup code to dialog
		from horizons.gui.mainmenu import Dialog
		class TempDialog(Dialog):
			return_events = bind
			def prepare(self, *args, **kwargs):
				self._widget = dlg
				self.modal = modal
				if event_map:
					self._widget.mapEvents(event_map)

		return self.show(TempDialog(self._widgets, manager=self))
