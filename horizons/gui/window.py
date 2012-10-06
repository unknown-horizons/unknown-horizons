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
from horizons.gui.widgets.imagebutton import OkButton, CancelButton


class Window(object):
	stackable = True

	def __init__(self, widget_loader, gui=None, manager=None):
		self._widget_loader = widget_loader
		self._widget = None
		self._gui = gui
		self.windows = manager

	def show(self, **kwargs):
		raise NotImplementedError

	def hide(self):
		raise NotImplementedError

	def close(self):
		# for now this is a special case for dialogs
		pass

	def abort(self):
		# for now this is a special case for dialogs
		pass

	def _focus(self, widget):
		"""Needed to capture key events to detect escape.
		
		Call this after your widget is visible.
		"""
		widget.is_focusable = True
		widget.requestFocus()

	def _capture_escape(self, widget):
		"""Set up key capture for the widget.

		Call this when setting up your widget.
		"""
		widget.capture(self._on_keypress, event_name="keyPressed")

	def _on_keypress(self, event):
		if event.getKey().getValue() == fife.Key.ESCAPE:
			self.on_escape()

	def on_escape(self):
		"""By default the window will close when escape is pressed.

		Override this in your subclass if you want to modify the behaviour.
		"""
		self.windows.close()


class Dialog(Window):
	modal = True
	widget_name = None

	def __init__(self, *args, **kwargs):
		super(Dialog, self).__init__(*args, **kwargs)
		self.active = False
		self._hidden = False
		self._widget = None

	def prepare(self, *args, **kwargs):
		"""Preparation of the widget before the dialog is shown.

		Return False here if you don't want to abort showing the dialog.
		"""
		# pre needs to accept args and kwargs due to the way Callback works
		pass

	def post(self, return_value):
		return return_value

	def show(self, *args, **kwargs):
		assert not self.active
		self.active = True

		if self._hidden:
			self._widget.show()
			self._widget.requestFocus()
			self._hidden = False
			return

		if self.widget_name:
			self._widget = self._widget_loader[self.widget_name]

		# need to check explicitly for False, because None might just be a normal
		# return in prepare
		if self.prepare(**kwargs) == False:
			return

		assert self._widget, 'Pre did not load a widget'

		if self.modal:
			self._show_modal_background()

		self._widget.capture(self._on_keypress, event_name="keyPressed")
		self._widget.show()
		ret = self._widget.execute(self.return_events)
		if self.modal:
			self._hide_modal_background()

		self.windows.close()
		return self.post(ret)

	def abort(self):
		horizons.globals.fife.pychanmanager.breakFromMainLoop(False)

	def close(self):
		if self.active:
			self.active = False
			self.hide()

	def hide(self):
		if self.active:
			self.active = False
			self._hidden = True

		if self._widget:
			self._widget.hide()

	def _show_modal_background(self):
		"""Loads transparent background that de facto prohibits
		access to other gui elements by eating all input events.
		"""
		# FIXME this is called multiple times without hide in between when
		# showing the credits
		if getattr(self, '_modal_widget', None):
			return

		height = horizons.globals.fife.engine_settings.getScreenHeight()
		width = horizons.globals.fife.engine_settings.getScreenWidth()
		image = horizons.globals.fife.imagemanager.loadBlank(width, height)
		image = fife.GuiImage(image)
		self._modal_widget = pychan.Icon(image=image)
		self._modal_widget.position = (0, 0)
		self._modal_widget.show()

	def _hide_modal_background(self):
		try:
			self._modal_widget.hide()
			del self._modal_widget
		except AttributeError:
			pass

	def _on_keypress(self, event):
		from horizons.engine import pychan_util
		if event.getKey().getValue() == fife.Key.ESCAPE: # convention says use cancel action
			btn = self._widget.findChild(name=CancelButton.DEFAULT_NAME)
			callback = pychan_util.get_button_event(btn) if btn else None
			if callback:
				pychan.tools.applyOnlySuitable(callback, event=event, widget=btn)
			else:
				# escape should hide the dialog default
				horizons.globals.fife.pychanmanager.breakFromMainLoop(False)
		elif event.getKey().getValue() == fife.Key.ENTER: # convention says use ok action
			btn = self._widget.findChild(name=OkButton.DEFAULT_NAME)
			callback = pychan_util.get_button_event(btn) if btn else None
			if callback:
				pychan.tools.applyOnlySuitable(callback, event=event, widget=btn)
			# can't guess a default action here


class WindowManager(object):

	def __init__(self, widget_loader):
		self._windows = []
		self._widgets = widget_loader

	def show(self, widget, **kwargs):
		"""Show a new window on top.
		
		Hide the current one and show the new one.
		"""
		# TODO for popups, we sometimes want the old widget to stay visible

		self.hide()
		self._windows.append(widget)
		return widget.show(**kwargs)

	def replace(self, widget, **kwargs):
		"""Replace the top window with this widget.

		So far, this seems to be needed by the credits dialog.
		"""
		self.close()
		return self.show(widget, **kwargs)

	def close(self):
		"""Close the top window.
		
		If there is another window left, show it.
		"""
		widget = self._windows.pop()
		widget.close()
		if self._windows:
			self._windows[-1].show()

	def hide(self):
		"""Attempt to hide the current window.
		
		A window that does not permit other windows on top of it will be closed,
		any other will be hidden.
		"""
		if not self._windows:
			return

		if not self._windows[-1].stackable:
			self.close()
		else:
			self._windows[-1].hide()

	def toggle(self, widget):
		# FIXME we ignore this for now, because the pause menu ingame needs to be
		# stackable... I think
		"""
		if widget.stackable:
			# This means that the widget might still be somewhere in our stack.
			# We can only toggle windows that are closed immediately when losing
			# focus.
			raise Exception('This should not be possible')
		"""

		if self._windows and self._windows[-1] == widget:
			self._windows[-1].abort()
		else:
			self.show(widget)

	def close_all(self):
		while self._windows:
			self.close()

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
			return self.show_popup( _("Error: {error_message}").format(error_message=windowtitle),
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
		class TempDialog(Dialog):
			return_events = bind
			def prepare(self, *args, **kwargs):
				self._widget = dlg
				self.modal = modal
				if event_map:
					self._widget.mapEvents(event_map)

		return self.show(TempDialog(self._widgets, manager=self))
