# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import game.main
import fife
from string import Template

class MessageWidget(object):
	"""Class that organises the messages in the top right of the screen.
	It uses Message Class instances to store messages and manages the
	archive.
	@param x,y: int position where the widget ist placed on the screen."""
	def __init__(self, x, y):
		self.x, self.y = x, y
		self.active_messages = []
		self.archive = []
		self.widget = game.main.fife.pychan.loadXML('content/gui/hud_messages.xml')
		self.widget.position = (x,y)
		self.text_widget = game.main.fife.pychan.loadXML('content/gui/hud_messages_text.xml')
		self.text_widget.position = (x,y+self.widget.height)
		self.widget.show()
		self.current_tick = None
		self.position = 0
		game.main.ext_scheduler.add_new_object(self.tick, self, loops=-1)

	def add(self, x, y, id, message_dict=None):
		"""Adds a message to the MessageWidget.
		@param x, y: int coordinates where the action took place.
		@param id: message id, needed to retrieve the message from the database.
		@param message_dict: template dict with the neccassary values. ( e.g.: {'player': 'Arthus'}
		"""
		self.active_messages.insert(0, Message(x,y,id, self.current_tick, message_dict))
		self.draw_wigdet()

	def draw_wigdet(self):
		"""Updates the widget."""
		widg = self.widget
		for i in range(1,5):
			if self.position + i-1 < len(self.active_messages):
				w = self.widget.findChild(name=str(i))
				w.up_image = self.active_messages[self.position + i-1].image
				w.hover_image = self.active_messages[self.position + i-1].image
				w.capture(game.main.fife.pychan.tools.callbackWithArguments(game.main.session.view.center, self.active_messages[self.position + i-1].x,self.active_messages[self.position + i-1].y))
				print 'set showtext to', self.position + i-1
				w.setEnterCallback(self.show_text)
				w.setExitCallback(self.hide_text)
			else:
				w = self.widget.findChild(name=str(i))
				w.up_image = 'content/gui/images/background/oa_ingame_buttonbg_48.png'
				w.hover_image = 'content/gui/images/background/oa_ingame_buttonbg_48.png'
				w.capture(lambda : None)
				w.setEnterCallback(lambda button: None)
				w.setExitCallback(lambda button: None)

	def forward(self):
		"""Sets the widget to the next icon."""
		pass

	def back(self):
		"""Sets the widget to the previous icon."""
		pass

	def show_text(self, button):
		"""Shows the text for the button."""
		label = self.text_widget.findChild(name='text')
		label.text = self.active_messages[self.position+int(button.name)-1].message
		label.resizeToContent()
		self.text_widget.size = (self.text_widget.getMaxChildrenWidth(), self.text_widget.height)
		self.text_widget.position = (self.widget.x + self.widget.width/2-self.text_widget.width/2, self.text_widget.y)
		self.text_widget.show()

	def hide_text(self, button):
		"""Hides the text."""
		self.text_widget.hide()

	def tick(self):
		"""Check wether a message is old enough to be put into the archives"""
		changed = False
		for item in self.active_messages:
			item.display -= 1
			if item.display == 0:
				self.archive.append(item)
				self.active_messages.remove(item)
				changed = True
		if changed:
			self.draw_wigdet()

	def __del__(self):
		game.main.ext_scheduler.rem_all_classinst_calls(self)
		self.active_messages = []
		self.archive = []

class Message(object):
	"""Represents a message that is to be displayed in the MessageWidget.
	The message is used as a string.Template, meaning it can contain placeholders
	like the following: $player, ${gold}. The second version is recommendet, as the word
	can then be followed by other characters without a whitespace (e.g. "${player}'s home").
	The dict needed to fill these placeholders needs to be provided when creating the Message.

	@param x,y: int position on the map where the action took place.
	@param id: message id, needed to retrieve the message from the database.
	@param created: tickid when the message was created.
	@param message_dict: template dict with the neccassary values for the message. ( e.g.: {'player': 'Arthus'}
	"""
	def __init__(self, x, y, id, created, message_dict=None):
		self.x, self.y = x, y
		self.id = id
		self.read = False
		self.created = created
		self.display = int(game.main.db('SELECT visible_for from message WHERE rowid=?', id).rows[0][0])
		self.image = str(game.main.db('SELECT icon from message_icon WHERE color=? AND icon_id=?', 1, id).rows[0][0])
		self.message = Template(str(game.main.db('SELECT text from message WHERE rowid=?', id).rows[0][0])).safe_substitute(message_dict if message_dict is not None else {})
