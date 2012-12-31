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
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton, CancelButton


class Window(object):

	def __init__(self, windows=None):
		# Reference to the window manager. Use it to show new windows or close
		# this window.
		self._windows = windows

		self._modal_background = None

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

	def _show_modal_background(self):
		"""
		Loads transparent background that de facto prohibits access to other
		gui elements by eating all input events.
		"""
		height = horizons.globals.fife.engine_settings.getScreenHeight()
		width = horizons.globals.fife.engine_settings.getScreenWidth()
		image = horizons.globals.fife.imagemanager.loadBlank(width, height)
		image = fife.GuiImage(image)
		self._modal_background = pychan.Icon(image=image)
		self._modal_background.position = (0, 0)
		self._modal_background.show()

	def _hide_modal_background(self):
		self._modal_background.hide()


class Dialog(Window):
	# Whether to block user interaction while displaying the dialog
	modal = False

	# Name of widget that should get the focus once the dialog is shown
	focus = None

	def __init__(self, windows):
		super(Dialog, self).__init__(windows)

		self._gui = None
		self._hidden = False
		self._return_events = {}

	def prepare(self, **kwargs):
		"""Setup the dialog gui.

		The widget has to be stored in `self._gui`. If you want to abort the dialog
		here return False.
		"""
		raise NotImplementedError

	def act(self, retval):
		"""Do something after dialog is closed.

		If you want to show the dialog again, you need to do that explicitly, e.g. with:

			self._windows.show(self)
		"""
		return retval

	def show(self, **kwargs):
		# if the dialog is already running but has been hidden, just show the widget
		if self._hidden:
			self._hidden = False
			if self.modal:
				self._show_modal_background()
			self._gui.show()
			self._gui.requestFocus()
			return

		# if `prepare` returned False, we stop the dialog
		if self.prepare(**kwargs) == False:
			self._windows.close()
			return

		self._gui.capture(self._on_keypress, event_name="keyPressed")
		self._gui.show()

		if self.modal:
			self._show_modal_background()

		retval = Dialog.execute(self._gui, self.return_events, self.focus)

		self._windows.close()
		return self.act(retval)

	def hide(self):
		if self.modal:
			self._hide_modal_background()
		self._gui.hide()
		self._hidden = True

	def close(self):
		self.hide()

	def on_escape(self):
		# escape is handled in `_on_keypress`
		pass

	def _on_keypress(self, event):
		"""Intercept ESC and ENTER keys and execute the appropriate actions."""

		# Convention says use cancel action
		if event.getKey().getValue() == fife.Key.ESCAPE:
			retval = self.return_events.get(CancelButton.DEFAULT_NAME)
			if retval is not None:
				self.abort(retval)
		# Convention says use ok action
		elif event.getKey().getValue() == fife.Key.ENTER:
			retval = self.return_events.get(OkButton.DEFAULT_NAME)
			if retval is not None:
				self.abort(retval)

	def abort(self, retval=False):
		"""Break out of mainloop.

		Program flow continues after the `self._gui.execute` call in `show`.
		"""
		horizons.globals.fife.pychanmanager.breakFromMainLoop(retval)

	@staticmethod
	def execute(widget, bind, focus=None):
		"""Execute the dialog synchronously.
		
		Note: We implement this again as we want to retain focus for child widget sometimes.

		@param widget: widget to execute
		@param bind: Dictionary with buttons and return values
		"""
		# FIXME This is a workaround for lack of native implementation of focus handling within execute() in FIFE. 
		#       Ref. FIFE ticket #750.

		for name, retval in bind.items():
			def _quitThisDialog(retval=retval):
				horizons.globals.fife.pychanmanager.breakFromMainLoop(retval)
			widget.findChild(name=name).capture(_quitThisDialog, group_name="__execute__")

		widget.show()

		if focus and widget.findChild(name=focus):
			widget.findChild(name=focus).requestFocus() # child widget takes focus
		else:
			widget.is_focusable = True
			widget.requestFocus()

		return horizons.globals.fife.pychanmanager.mainLoop()


class WindowManager(object):

	def __init__(self, mainmenu):
		self._mainmenu = mainmenu
		self._windows = []

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
			# TODO temporary, try to stay compatible with rest of the code
			top = self._windows[-1]
			self._mainmenu.current = top
			if hasattr(top, 'on_escape'):
				self._mainmenu.on_escape = top.on_escape

			self._windows[-1].show()

	def hide(self):
		"""Attempt to hide the current window.

		A window that does not permit other windows on top of it will be closed,
		any other will be hidden.
		"""
		if not self._windows:
			return

		self._windows[-1].hide()

	def toggle(self, window, **kwargs):
		"""Hide window if is currently visible (and on top), show it otherwise."""
		if self._windows and self._windows[-1] == window:
			self.close()
		else:
			self.show(window, **kwargs)

	def show_dialog(self, dlg, bind, event_map=None, modal=False, focus=None):
		"""Shows any pychan dialog.

		@param dlg: dialog that is to be shown
		@param bind: events that make the dialog return + return values {'ok': True, 'cancel': False}
		@param event_map: dictionary with callbacks for buttons. See pychan docu: pychan.widget.mapEvents()
		@param modal: Whether to block user interaction while displaying the popup
		@param focus: Which child widget should take focus
		"""

		def prepare(self, **kwargs):
			self._gui = dlg
			if event_map:
				self._gui.mapEvents(event_map)

		TempDialog = type('TempDialog', (Dialog, ), {
			'modal': modal,
			'return_events': bind,
			'focus': focus,
			'prepare': prepare,
		})

		return self.show(TempDialog(self))

	def show_popup(self, windowtitle, message, show_cancel_button=False, size=0, modal=True):
		"""Displays a popup with the specified text

		@param windowtitle: the title of the popup
		@param message: the text displayed in the popup
		@param show_cancel_button: boolean, show cancel button or not
		@param size: 0, 1 or 2. Larger means bigger.
		@param modal: Whether to block user interaction while displaying the popup
		@return: True on ok, False on cancel (if no cancel button, always True)
		"""
		if size == 0:
			wdg_name = "popup_230"
		elif size == 1:
			wdg_name = "popup_290"
		elif size == 2:
			wdg_name = "popup_350"
		else:
			assert False, "size should be 0 <= size <= 2, but is " + str(size)

		popup = load_uh_widget(wdg_name + '.xml')

		headline = popup.findChild(name='headline')
		headline.text = _(windowtitle)
		message_lbl = popup.findChild(name='popup_message')
		message_lbl.text = _(message)
		popup.adaptLayout() # recalculate widths

		if show_cancel_button:
			bind = {OkButton.DEFAULT_NAME: True, CancelButton.DEFAULT_NAME: False}
		else:
			bind = {OkButton.DEFAULT_NAME: True}
			cancel_button = popup.findChild(name=CancelButton.DEFAULT_NAME)
			cancel_button.parent.removeChild(cancel_button)

		return self.show_dialog(popup, bind, modal=modal)

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
			                 msg)
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
