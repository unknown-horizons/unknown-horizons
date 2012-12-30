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
from horizons.extscheduler import ExtScheduler
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton, CancelButton


class Window(object):

	def __init__(self, windows=None):
		# Reference to the window manager. Use it to show new windows or close
		# this window.
		self._windows = windows

	def show(self, **kwargs):
		"""Show the window.

		After this call, the window should be visible. If you decide to not show
		the window here (e.g. an error occured), you'll need to call
		`self._windows.close()` to remove the window from the manager.
		"""
		raise NotImplementedError

	def hide(self):
		"""Hide the window.

		After this call, the window should not be visible anymore. However, it remains
		in the stack of open windows and will be visible once it becomes the topmost
		window again.

		You should *never* call this directly in your code, other than in `close()`
		when you overwrote it in your subclass.
		"""
		raise NotImplementedError

	def close(self):
		"""Closes the window.

		You should *never* call this directly in your code. Use `self._windows.close()`
		to ask the WindowManager to remove the window instead.
		"""
		self.hide()

	def on_escape(self):
		"""Define what happens when ESC is pressed.

		By default, the window will be closed.
		"""
		self._windows.close()


class WindowManager(object):

	def __init__(self, mainmenu):
		self._mainmenu = mainmenu
		self._windows = []
		self._modal_background = None

	def show(self, window, **kwargs):
		"""Show a new window on top.

		Hide the current one and show the new one.
		Keyword arguments will be passed through to the window's `show` method.
		"""
		self.hide()

		# TODO temporary, try to stay compatible with rest of the code
		self._mainmenu.current = window
		if hasattr(window, 'on_escape'):
			self._mainmenu.on_escape = window.on_escape

		self._windows.append(window)
		return window.show(**kwargs)

	def close(self):
		"""Close the top window.

		If there is another window left, show it.
		"""
		window = self._windows.pop()
		window.close()
		if self._windows:
			self._windows[-1].show()

	def hide(self):
		"""Attempt to hide the current window.

		A window that does not permit other windows on top of it will be closed,
		any other will be hidden.
		"""
		if not self._windows:
			return

		self._windows[-1].hide()

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
