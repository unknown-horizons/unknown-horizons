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
		self.widget.show()
		self.current_tick = None
		self.position = 0
		game.main.ext_scheduler.add_new_object(self.tick, self, loops=-1)

	def add(self, x, y, id):
		"""Adds a message to the MessageWidget.
		@param x, y: int coordinates where the action took place.
		@param id: message id, needed to retrieve the message from the database.
		"""
		self.active_messages.insert(0, Message(x,y,id, self.current_tick))
		self.draw_wigdet()

	def draw_wigdet(self):
		"""Updates the widget."""
		widg = self.widget
		for i in range(1,5):
			if self.position + i-1 < len(self.active_messages):
				w = self.widget.findChild(name=str(i))
				w.image = self.active_messages[self.position + i-1].image
				w2 = self.widget.findChild(name='button_'+str(i))
				w2.capture(game.main.fife.pychan.tools.callbackWithArguments(game.main.session.view.center, self.active_messages[self.position + i-1].x,self.active_messages[self.position + i-1].y))
			else:
				w = self.widget.findChild(name=str(i))
				w.image = 'content/gui/images/background/oa_ingame_buttonbg_48.png'
				w2 = self.widget.findChild(name='button_'+str(i))
				w2.capture(lambda : None)

	def forward(self):
		"""Sets the widget to the next icon."""
		pass

	def back(self):
		"""Sets the widget to the previous icon."""
		pass

	def tick(self):
		"""Check wether a message is old enough to be put into the archives"""
		print 'tick'
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
	@param x,y: int position on the map where the action took place.
	@param id: message id, needed to retrieve the message from the database.
	@param created: tickid when the message was created.
	"""
	def __init__(self, x, y, id, created):
		self.x, self.y = x, y
		self.id = id
		self.read = False
		self.created = created
		self.display = int(game.main.db('SELECT visible_for from message WHERE rowid=?', id).rows[0][0])
		self.image = str(game.main.db('SELECT icon from message_icon WHERE color=? AND icon_id=?', 1, id).rows[0][0])
		self.message = str(game.main.db('SELECT text from message WHERE rowid=?', id).rows[0][0])