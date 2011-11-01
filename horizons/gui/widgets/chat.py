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

from fife.extensions import pychan

import horizons.main
from horizons.entities import Entities

from horizons.util import livingProperty, LivingObject, PychanChildFinder, Rect, Point
from horizons.util.python import Callback
from horizons.gui.mousetools import BuildingTool, SelectionTool
from horizons.gui.tabs import TabWidget, BuildTab
from horizons.gui.widgets.messagewidget import MessageWidget
from horizons.util.gui import LazyWidgetsDict
from horizons.constants import RES
from horizons.command.uioptions import RenameObject
from horizons.command.misc import Chat

class Chat(LivingObject):
	"""			"""
	SHOW_NEW_MESSAGE_TEXT = 4 # seconds
	MAX_MESSAGES = 5
		
	def __init__(self, session, x, y):
		super(LivingObject, self).__init__()
		self.session = session
		self.x_pos, self.y_pos = x, y
		#self.active_messages = [] # for displayed messages
		#self.archive = [] # messages, that aren't displayed any more
		self.widget = load_uh_widget('chat.xml')
		self.widget.position = (
			 50,
			 5) #horizons.main.fife.engine_settings.getScreenHeight()/2 - self.widget.size[1]/2)
		self.text_widget = load_uh_widget('hud_messages_text.xml')
		self.text_widget.position = (self.widget.x + self.widget.width, self.widget.y)
		self.widget.show()
		self.current_tick = 0
		self.position = 0 # number of current message
		ExtScheduler().add_new_object(self.tick, self, loops=-1)
		
		
	def show_chat_dialog(self):
		"""Show a dialog where the user can enter a chat message"""
		events = {
			'okButton': self._do_chat,
			'cancelButton': self._hide_chat_dialog
		}
		self.main_gui.on_escape = self._hide_chat_dialog

		self.widgets['chat'].mapEvents(events)
		self.widgets['chat'].findChild(name='msg').capture( self._do_chat )
		self.widgets['chat'].show()
		self.widgets['chat'].findChild(name="msg").requestFocus()

	def _hide_chat_dialog(self):
		"""Escapes the chat dialog"""
		self.main_gui.on_escape = self.main_gui.show_pause
		self.widgets['chat'].hide()

	def _do_chat(self):
		"""Actually initiates chatting and hides the dialog"""
		msg = self.widgets['chat'].findChild(name='msg').text
		Chat(msg).execute(self.session)
		self.widgets['chat'].findChild(name='msg').text = u''
		self._hide_chat_dialog()
