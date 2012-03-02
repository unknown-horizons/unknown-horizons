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

import textwrap
import itertools

from fife.extensions import pychan

import horizons.main

from horizons.extscheduler import ExtScheduler
from horizons.util import LivingObject, Callback, Point
from horizons.scheduler import Scheduler
from horizons.util.gui import load_uh_widget
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.i18n.voice import get_speech_file

class MessageWidget(LivingObject):
	"""Class that organizes the messages. Displayed on left screen edge.
	It uses Message instances to store messages and manages the archive.
	"""

	BG_IMAGE_MIDDLE = 'content/gui/images/background/widgets/message_bg_middle.png'
	IMG_HEIGHT = 24 # distance of above segments in px.
	LINE_HEIGHT = 17
	ICON_TEMPLATE = 'messagewidget_icon.xml'
	MSG_TEMPLATE = 'messagewidget_message.xml'
	CHARS_PER_LINE = 34 # character count after which we start new line. no wrap
	SHOW_NEW_MESSAGE_TEXT = 7 # seconds
	MAX_MESSAGES = 5

	_DUPLICATE_TIME_THRESHOLD = 10 # sec
	_DUPLICATE_SPACE_THRESHOLD = 8 # distance

	OVERVIEW_WIDGET = 'messagewidget_overview.xml'

	def __init__(self, session):
		super(MessageWidget, self).__init__()
		self.session = session
		self.active_messages = [] # for displayed messages
		self.archive = [] # messages, that aren't displayed any more
		self.chat = [] # chat messages sent by players
		self.msgcount = itertools.count() # sort to preserve order after loading

		self.widget = load_uh_widget(self.ICON_TEMPLATE)
		self.widget.position = (
			 5,
			 horizons.main.fife.engine_settings.getScreenHeight()/2 - self.widget.size[1]/2)

		self.text_widget = load_uh_widget(self.MSG_TEMPLATE)
		self.text_widget.position = (self.widget.x + self.widget.width, self.widget.y)

		self.widget.show()
		self.item = 0 # number of current message
		ExtScheduler().add_new_object(self.tick, self, loops=-1)
		# buttons to toggle through messages

		self._last_message = {} # used to detect fast subsequent messages in add()
		self.draw_widget()

	def add(self, x, y, string_id, message_dict=None, creation_tick=None, sound_file=True, check_duplicate=False):
		"""Adds a message to the MessageWidget.
		@param x, y: int coordinates where the action took place. Clicks on the message will then focus that spot.
		@param id: message id string, needed to retrieve the message text from the content database.
		@param message_dict: dict with strings to replace in the message, e.g. {'player': 'Arthus'}
		@param sound_file: if True: play default message speech for string_id
		                   if False: do not play sound
		                   if sound file path: play this sound file
		@param check_duplicate: check for pseudo-duplicates (similar messages recently nearby)
		"""
		if check_duplicate:
			if string_id in self._last_message:
				when, where = self._last_message[string_id]
				if when > Scheduler().cur_tick - Scheduler().get_ticks(self.__class__._DUPLICATE_TIME_THRESHOLD) and \
				   where.distance( (x, y) ) < self.__class__._DUPLICATE_SPACE_THRESHOLD:
					# there has been a message nearby recently, abort
					return
			self._last_message[string_id] = (Scheduler().cur_tick, Point(x, y))

		sound = {
							True: get_speech_file(string_id),
							False: None
							}.get(sound_file, sound_file)
		self._add_message(Message(x, y, string_id, created=self.msgcount.next(), message_dict=message_dict), sound)

	def add_custom(self, x, y, messagetext, visible_for=40, icon_id=1):
		""" See docstring for add().
		Uses no predefined message template from content database like add() does.
		Instead, directly provides text and icon to be shown (messagetext, icon_id)
		@param visible_for: how many seconds the message will stay visible in the widget
		"""
		self._add_message(Message(x, y, None, display=visible_for, created=self.msgcount.next(), message=messagetext, icon_id=icon_id))

	def add_chat(self, player, messagetext, icon_id=1):
		""" See docstring for add().
		"""
		message_dict = {'player': player, 'message': messagetext}
		self.add(x=None, y=None, string_id='CHAT', message_dict=message_dict)
		self.chat.append(self.active_messages[0])

	def _add_message(self, message, sound=None):
		"""Internal function for adding messages. Do not call directly.
		@param message: Message instance
		@param sound: path to soundfile"""
		self.active_messages.insert(0, message)
		if len(self.active_messages) > self.MAX_MESSAGES:
			self.active_messages.remove(self.active_messages[self.MAX_MESSAGES])

		if sound:
			horizons.main.fife.play_sound('speech', sound)
		else:
			# play default msg sound
			AmbientSoundComponent.play_special('message')

		if message.x is not None and message.y is not None:
			self.session.ingame_gui.minimap.highlight( (message.x, message.y) )

		self.draw_widget()
		self.show_text(0)
		ExtScheduler().add_new_object(self.hide_text, self, self.SHOW_NEW_MESSAGE_TEXT)

	def draw_widget(self):
		"""
		Updates whole messagewidget (all messages): draw icons.
		Inactive messages need their icon hovered to display their text again
		"""
		button_space = self.widget.findChild(name="button_space")
		button_space.removeAllChildren() # Remove old buttons
		for index, message in enumerate(self.active_messages):
			if (self.item + index) < len(self.active_messages):
				button = pychan.widgets.ImageButton()
				button.name = str(index)
				button.up_image = message.up_image
				button.hover_image = message.hover_image
				button.down_image = message.down_image
				button.is_focusable = False
				# show text on hover
				events = {
					button.name + "/mouseEntered": Callback(self.show_text, index),
					button.name + "/mouseExited": self.hide_text
				}
				if message.x is not None and message.y is not None:
					# move camera to source of event on click, if there is a source
					callback = Callback.ChainedCallbacks(
					  Callback(self.session.view.center, message.x, message.y),
					  Callback(self.session.ingame_gui.minimap.highlight, (message.x, message.y) )
					)
					events[button.name] = callback

				button.mapEvents(events)
				button_space.addChild(button)
		button_space.resizeToContent()
		self.widget.size = button_space.size

	def show_text(self, index):
		"""Shows the text for a button.
		@param index: index of button"""
		assert isinstance(index, int)
		ExtScheduler().rem_call(self, self.hide_text) # stop hiding if a new text has been shown
		label = self.text_widget.findChild(name='text')
		text = unicode(self.active_messages[self.item+index].message)
		text = text.replace(r'\n', self.CHARS_PER_LINE*' ')
		text = text.replace(r'[br]', self.CHARS_PER_LINE*' ')
		text = textwrap.fill(text, self.CHARS_PER_LINE)

		self.bg_middle = self.text_widget.findChild(name='msg_bg_middle')
		self.bg_middle.removeAllChildren()

		line_count = len(text.splitlines()) - 1
		for i in xrange(line_count * self.LINE_HEIGHT // self.IMG_HEIGHT):
			middle_icon = pychan.Icon(image=self.BG_IMAGE_MIDDLE)
			self.bg_middle.addChild(middle_icon)

		message_container = self.text_widget.findChild(name='message')
		message_container.size = (300, 21 + self.IMG_HEIGHT * line_count + 21)

		self.bg_middle.adaptLayout()
		label.text = text
		label.adaptLayout()
		self.text_widget.show()

	def hide_text(self):
		"""Hides the text."""
		self.text_widget.hide()

	def tick(self):
		"""Check whether a message is old enough to be put into the archives"""
		changed = False
		for item in self.active_messages:
			item.display -= 1
			if item.display == 0:
				# item not displayed any more -- put it in archive
				self.archive.append(item)
				self.active_messages.remove(item)
				self.hide_text()
				changed = True
		if changed:
			self.draw_widget()

	def end(self):
		self.hide_text()
		self.widget.findChild(name="button_space").removeAllChildren() # Remove old buttons
		ExtScheduler().rem_all_classinst_calls(self)
		self.active_messages = []
		self.archive = []
		super(MessageWidget, self).end()

	def save(self, db):
		for message in self.active_messages:
			if message.id is not None and message.id != 'CHAT': # only save default messages (for now)
				db("INSERT INTO message_widget_active (id, x, y, read, created, display, message) VALUES (?, ?, ?, ?, ?, ?, ?)", message.id, message.x, message.y, int(message.read), message.created, message.display, message.message)
		for message in self.archive:
			if message.id is not None and message.id != 'CHAT':
				db("INSERT INTO message_widget_archive (id, x, y, read, created, display, message) VALUES (?, ?, ?, ?, ?, ?, ?)", message.id, message.x, message.y, int(message.read), message.created, message.display, message.message)
		for message in self.chat:
			# handle 'CHAT' special case: display is 0 (do not show old chat on load)
			db("INSERT INTO message_widget_archive (id, x, y, read, created, display, message) VALUES (?, ?, ?, ?, ?, ?, ?)", message.id, message.x, message.y, int(message.read), message.created, 0, message.message)

	def load(self, db):
		messages = db("SELECT id, x, y, read, created, display, message FROM message_widget_active ORDER BY created ASC")
		for (msg_id, x, y, read, created, display, message) in messages:
			msg = Message(x, y, msg_id, created, bool(read), bool(display), message)
			self.active_messages.append(msg)
		messages = db("SELECT id, x, y, read, created, display, message FROM message_widget_archive ORDER BY created ASC")
		for (msg_id, x, y, read, created, display, message) in messages:
			msg = Message(x, y, msg_id, created, bool(read), bool(display), message)
			if msg_id == 'CHAT':
				self.chat.append(msg)
			else:
				self.archive.append(msg)
		count = max([-1] + [m.created for m in self.active_messages + self.archive + self.chat]) + 1
		self.msgcount = itertools.count(count) # start keyword only works with 2.7+
		self.draw_widget()


class Message(object):
	"""Represents a message that is to be displayed in the MessageWidget.
	The message is used as a string template, meaning it can contain placeholders
	like the following: {player}, {gold}. The dict needed to fill in these place-
	holders needs to be provided when creating Messages. (parameter message_dict)

	@param x, y: int position on the map where the action took place.
	@param id: message id string, needed to retrieve the message from the database.
	@param created: tickid when the message was created. Keeps message order after load.
	@param message_dict: dict with strings to replace in the message, e.g. {'player': 'Arthus'}
	"""
	def __init__(self, x, y, id, created, read=False, display=None, message=None, message_dict=None, icon_id=None):
		self.x, self.y = x, y
		self.id = id
		self.read = read
		self.created = created
		self.display = display if display is not None else horizons.main.db.get_msg_visibility(id)
		icon = icon_id if icon_id else horizons.main.db.get_msg_icon_id(id)
		self.up_image, self.down_image, self.hover_image = horizons.main.db.get_msg_icons(icon)
		if message is not None:
			assert isinstance(message, str) or isinstance(message, unicode)
			self.message = message
		else:
			msg = _(horizons.main.db.get_msg_text(id))
			try:
				self.message = msg.format(**message_dict if message_dict is not None else {})
			except KeyError as err:
				self.message = msg
				print u"Warning: Unsubstituted string {err} in {id} message \"{msg}\", dict {dic}".format(
				       err=err, msg=msg, id=id, dic=message_dict)

	def __repr__(self):
		return "% 4d: %s  '%s'  %s %s%s" % (self.created, self.id, self.message, '(%s,%s) ' % (self.x, self.y) if self.x and self.y else '', 'R' if self.read else ' ', 'D' if self.display else ' ')
