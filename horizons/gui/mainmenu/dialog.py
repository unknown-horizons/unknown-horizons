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

from fife import fife
from fife.extensions import pychan

import horizons.globals
from horizons.gui.widgets.imagebutton import OkButton, CancelButton


CLOSE_DIALOG = object()


class Dialog(object):
	modal = True
	widget_name = None
	stackable = True

	def __init__(self, widget_loader, gui=None, manager=None):
		self._widget_loader = widget_loader
		self._widget = None
		self.dialogs = manager
		# TODO this needs to go probably
		self._gui = gui
		self.active = False
		self._hidden = False

	def prepare(self, *args, **kwargs):
		"""Preparation of the widget before the dialog is shown.

		Return False here if you don't want to abort showing the dialog.
		"""
		# pre needs to accept args and kwargs due to the way Callback works
		pass

	def post(self, return_value):
		return return_value

	def show(self, *args, **kwargs):
		print 'Dialog show', self, 'hidden' if self._hidden else ''
		assert not self.active
		self.active = True

		if self._hidden:
			print 'Dialog show unhide', self
			self._widget.show()
			self._hidden = False
			return

		print 'Dialog show new', self
		if self.widget_name:
			self._widget = self._widget_loader[self.widget_name]

		# need to check explicitly for False, because None might just be a normal
		# return in prepare
		if self.prepare(**kwargs) == False:
			return

		assert self._widget, 'Pre did not load a widget'

		if self.modal:
			self._show_modal_background()

		def _on_keypress(event, dlg=self._widget): # rebind to make sure this dlg is used
			print 'keypress', dlg
			from horizons.engine import pychan_util
			if event.getKey().getValue() == fife.Key.ESCAPE: # convention says use cancel action
				btn = dlg.findChild(name=CancelButton.DEFAULT_NAME)
				callback = pychan_util.get_button_event(btn) if btn else None
				if callback:
					pychan.tools.applyOnlySuitable(callback, event=event, widget=btn)
				else:
					# escape should hide the dialog default
					horizons.globals.fife.pychanmanager.breakFromMainLoop(CLOSE_DIALOG)
			elif event.getKey().getValue() == fife.Key.ENTER: # convention says use ok action
				btn = dlg.findChild(name=OkButton.DEFAULT_NAME)
				callback = pychan_util.get_button_event(btn) if btn else None
				if callback:
					pychan.tools.applyOnlySuitable(callback, event=event, widget=btn)
				# can't guess a default action here

		self._widget.capture(_on_keypress, event_name="keyPressed")
		self._widget.show()
		print 'Dialog show execute start', self
		ret = self._widget.execute(self.return_events)
		print 'Dialog show execute end', self
		if self.modal:
			self._hide_modal_background()

		self.dialogs.close()
		return self.post(ret)

	def abort(self):
		print 'Dialog abort', self
		horizons.globals.fife.pychanmanager.breakFromMainLoop(CLOSE_DIALOG)

	def close(self):
		print 'Dialog close', self
		if self.active:
			self.active = False
			self.hide()

	def hide(self):
		print 'Dialog hide', self
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
