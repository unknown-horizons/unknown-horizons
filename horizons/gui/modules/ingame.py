# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

from horizons.command.misc import Chat
from horizons.command.uioptions import RenameObject
from horizons.component.namedcomponent import NamedComponent
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.util.python.callback import Callback


class ChatDialog(object):
	"""Allow player to send messages to other players."""

	def __init__(self, main_gui, session, widget):
		self._main_gui = main_gui
		self._session = session
		self._widget = widget

		events = {
			OkButton.DEFAULT_NAME: self._do_chat,
			CancelButton.DEFAULT_NAME: self.hide
		}
		self._widget.mapEvents(events)

		def forward_escape(event):
			# the textfield will eat everything, even control events
			if event.getKey().getValue() == fife.Key.ESCAPE:
				self._main_gui.on_escape()

		self._widget.findChild(name="msg").capture(forward_escape, "keyPressed")
		self._widget.findChild(name="msg").capture(self._do_chat)

	def show(self):
		self._main_gui.on_escape = self.hide
		self._widget.show()
		self._widget.findChild(name="msg").requestFocus()

	def hide(self):
		self._main_gui.on_escape = self._main_gui.toggle_pause
		self._widget.hide()

	def _do_chat(self):
		"""Actually initiates chatting and hides the dialog"""
		msg = self._widget.findChild(name="msg").text
		Chat(msg).execute(self._session)
		self._widget.findChild(name="msg").text = u''
		self.hide()


class ChangeNameDialog(object):
	"""Shows a dialog where the user can change the name of a NamedComponent."""

	def __init__(self, main_gui, session, widget):
		self._main_gui = main_gui
		self._session = session
		self._widget = widget

		self._widget.mapEvents({CancelButton.DEFAULT_NAME: self.hide})

		def forward_escape(event):
			# the textfield will eat everything, even control events
			if event.getKey().getValue() == fife.Key.ESCAPE:
				self._main_gui.on_escape()

		self._widget.findChild(name="new_name").capture(forward_escape, "keyPressed")

	def show(self, instance):
		self._main_gui.on_escape = self.hide

		cb = Callback(self._do_change_name, instance)
		self._widget.mapEvents({OkButton.DEFAULT_NAME: cb})
		self._widget.findChild(name="new_name").capture(cb)

		oldname = self._widget.findChild(name='old_name')
		oldname.text = instance.get_component(NamedComponent).name

		self._widget.show()
		self._widget.findChild(name="new_name").requestFocus()

	def hide(self):
		self._main_gui.on_escape = self._main_gui.toggle_pause
		self._widget.hide()

	def _do_change_name(self, instance):
		new_name = self._widget.collectData('new_name')
		self._widget.findChild(name='new_name').text = u''

		if not new_name or not new_name.isspace():
			# different namedcomponent classes share the name
			RenameObject(instance.get_component_by_name(NamedComponent.NAME), new_name).execute(self._session)

		self.hide()
