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

import re

from horizons.command.misc import Chat
from horizons.command.uioptions import RenameObject
from horizons.component.namedcomponent import SettlementNameComponent, NamedComponent
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.gui.window import Window 


class ChangeNameDialog(Window):
	widget_name = 'change_name'

	def show(self, instance=None):
		self.instance = instance

		events = {
			OkButton.DEFAULT_NAME: self._change_name,
			CancelButton.DEFAULT_NAME: self.windows.close
		}

		self.widget = self._widget_loader[self.widget_name]

		oldname = self.widget.findChild(name='old_name')
		oldname.text = self.instance.get_component(SettlementNameComponent).name
		self.newname = self.widget.findChild(name='new_name')
		self.newname.capture(self._change_name)
		self.widget.mapEvents(events)

		self.widget.show()
		self._capture_escape(self.newname)
		self.newname.requestFocus()

	def hide(self):
		self.widget.hide()

	def _change_name(self):
		"""Applies the new name and hides the dialog.

		If the new name has length 0 or only contains blanks, the old name is kept.
		"""
		new_name = self.widget.collectData('new_name')
		self.newname.text = u''

		if new_name and not new_name.isspace():
			# different namedcomponent classes share the name
			RenameObject(self.instance.get_component_by_name(NamedComponent.NAME), new_name).execute(self._gui.session)

		self.windows.close()


class SaveMapDialog(Window):
	widget_name = 'save_map'

	def show(self):
		self.widget = self._widget_loader[self.widget_name]

		events = {
			OkButton.DEFAULT_NAME: self.save_map,
			CancelButton.DEFAULT_NAME: self.windows.close
		}

		name = self.widget.findChild(name='map_name')
		name.text = u''
		name.capture(self.save_map)

		self.widget.mapEvents(events)
		self.widget.show()

		self._capture_escape(name)
		name.requestFocus()

	def save_map(self):
		"""Saves the map and hides the dialog."""
		name = self.widget.collectData('map_name')
		if re.match('^[a-zA-Z0-9_-]+$', name):
			self._gui.session.save_map(name)
			self.windows.close()
		else:
			#xgettext:python-format
			message = _('Valid map names are in the following form: {expression}').format(expression='[a-zA-Z0-9_-]+')
			#xgettext:python-format
			advice = _('Try a name that only contains letters and numbers.')
			self.windows.show_error_popup(_('Error'), message, advice)

	def hide(self):
		self.widget.hide()


class ChatDialog(Window):
	widget_name = 'chat'

	def show(self):
		self.widget = self._widget_loader[self.widget_name]

		events = {
			OkButton.DEFAULT_NAME: self._do_chat,
			CancelButton.DEFAULT_NAME: self.windows.close
		}

		message = self.widget.findChild(name='msg')
		self._capture_escape(message)  # textfield eats control events
		message.capture(self._do_chat)

		self.widget.mapEvents(events)
		self.widget.show()

		message.requestFocus()

	def hide(self):
		self.widget.hide()

	def _do_chat(self):
		"""Actually initiates chatting and hides the dialog"""
		msg = self.widget.findChild(name='msg').text
		Chat(msg).execute(self._gui.session)
		self.widget.findChild(name='msg').text = u''

		self.windows.close()


class LogbookProxy(Window):
	# FIXME Wrapper around the real logbook to adapt it to the window system
	# REMOVE THIS ASAP

	stackable = False
	no_page = object()
	
	def __init__(self, *args, **kwargs):
		super(LogbookProxy, self).__init__(*args, **kwargs)
		self.active_page = self.no_page

	def show(self, page=None):
		# Hide the window when the page that should be shown is already visible
		if self.active_page == page:
			self.active_page = self.no_page
			self.windows.close()
			return

		self.active_page = page

		if self.active_page is None:
			# Show captainslog
			self._gui.logbook._hide_statswidgets()
			self._gui.logbook.show()
			self._gui.logbook.update_view(0)
		else:
			self._gui.logbook.show()
			self._gui.logbook.show_statswidget(widget=page)

	def hide(self):
		pass

	def abort(self, page=None):
		if self.active_page == page:
			self.active_page = self.no_page
			self._gui.logbook.hide()
			return

		self.windows.show(self, page=page)
