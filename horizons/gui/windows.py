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

from fife import fife
from fife.extensions import pychan

import horizons.globals
from horizons.engine import pychan_util
from horizons.extscheduler import ExtScheduler
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton, CancelButton


class WindowManager(object):

	def __init__(self):
		self._modal_background = None

	def show_modal_background(self):
		""" Loads transparent background that de facto prohibits
		access to other gui elements by eating all input events.
		Used for modal popups and our in-game menu.
		"""
		height = horizons.globals.fife.engine_settings.getScreenHeight()
		width = horizons.globals.fife.engine_settings.getScreenWidth()
		image = horizons.globals.fife.imagemanager.loadBlank(width, height)
		image = fife.GuiImage(image)
		self._modal_background = pychan.Icon(image=image)
		self._modal_background.position = (0, 0)
		self._modal_background.show()

	def hide_modal_background(self):
		if self._modal_background:
			self._modal_background.hide()

	def show_dialog(self, dlg, bind, event_map=None, modal=False, focus=None):
		"""Shows any pychan dialog.
		@param dlg: dialog that is to be shown
		@param bind: events that make the dialog return + return values{ 'ok': callback, 'cancel': callback }
		@param event_map: dictionary with callbacks for buttons. See pychan docu: pychan.widget.mapEvents()
		@param modal: Whether to block user interaction while displaying the dialog
		@param focus: Which child widget should take focus
		"""
		self.current_dialog = dlg
		if event_map is not None:
			dlg.mapEvents(event_map)
		if modal:
			self.show_modal_background()

		def execute(widget, bind):
			""" Execute the dialog synchronously. ## We implement this again as we want to 
						retain focus for child widget sometimes.
				@param widget: widget to execute
				@param bind: Dictionary with buttons and return values
			"""
			# FIXME:This is a workaround for lack of native implementation of focus handling within execute() in FIFE. 
			#		Ref. FIFE ticket #750.
			for name,returnValue in bind.items():
				def _quitThisDialog(returnValue = returnValue ):
					horizons.globals.fife.pychanmanager.breakFromMainLoop( returnValue )
					widget.hide()
				widget.findChild(name=name).capture( _quitThisDialog , group_name = "__execute__" )
			widget.show()
			if focus and widget.findChild(name=focus):
				widget.findChild(name=focus).requestFocus() # child widget takes focus
			else:
				widget.is_focusable = True
				widget.requestFocus()
			return horizons.globals.fife.pychanmanager.mainLoop()

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
		ret = execute(dlg, bind)
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
		popup = self._build_popup(windowtitle, message, show_cancel_button, size=size)
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
		popup = load_uh_widget(wdg_name + '.xml')

		if not show_cancel_button:
			cancel_button = popup.findChild(name=CancelButton.DEFAULT_NAME)
			cancel_button.parent.removeChild(cancel_button)

		popup.headline = popup.findChild(name='headline')
		popup.headline.text = _(windowtitle)
		popup.message = popup.findChild(name='popup_message')
		popup.message.text = _(message)
		popup.adaptLayout() # recalculate widths
		return popup
