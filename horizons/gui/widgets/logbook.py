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

from horizons.util import Callback
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.command.game import UnPauseCommand, PauseCommand
from horizons.command.misc import Chat
from horizons.gui.widgets.pickbeltwidget import PickBeltWidget

@metaChangeListenerDecorator("pause_request")
@metaChangeListenerDecorator("unpause_request")
class LogBook(PickBeltWidget):
	"""Implementation of the logbook as described here:
	http://wiki.unknown-horizons.org/w/Message_System

	It displays longer messages, that are essential for scenarios.
	Headings can be specified for each entry.
	"""
	widget_xml = 'captains_log.xml'
	style = None
	page_pos = (170,38)
	sections = (('logbook', _(u'Logbook')),
				('statistics', _(u'Statistics')),
				('chat_overview', _(u'Chat')))

	def __init__(self, session):
		super(LogBook, self).__init__()
		self.session = session
		self._headings = []
		self._messages = [] # list of all headings / messages
		self._cur_entry = None # remember current location; 0 to len(messages)-1
		self._hiding_widget = False # True if and only if the widget is currently in the process of being hidden
		self.stats_visible = None

		#self.add_entry(u"Heading",u"Welcome to the Captains log") # test code

	def _init_gui(self):
		"""Initial gui setup for all subpages accessible through pickbelts."""
		if hasattr(self,'_gui'):
			return
		self._gui = self.get_widget()
		self._gui.mapEvents({
		  'okButton' : self.hide,
		  'backwardButton' : Callback(self._scroll, -2),
		  'forwardButton' : Callback(self._scroll, 2),
		  'stats_players' : Callback(self.show_statswidget, widget='players'),
		  'stats_settlements' : Callback(self.show_statswidget, widget='settlements'),
		  'stats_ships' : Callback(self.show_statswidget, widget='ships'),
		  'chatTextField' : self._send_chat_message,
		  })
		self._gui.position_technique = "automatic" # "center:center"

		# stuff in the game message / chat history subwidget
		self.textfield = self._gui.findChild(name="chatTextField")
		self.textfield.capture(self._chatfield_onfocus, 'mouseReleased', 'default')
		self.chatbox = self._gui.findChild(name="chatbox")
		self.messagebox = self._gui.findChild(name="game_messagebox")
		self._display_chat_history() # initially print all loaded messages
		self._display_message_history()

		# these buttons flip pages in the captain's log if there are more than two
		self.backward_button = self._gui.findChild(name="backwardButton")
		self.forward_button = self._gui.findChild(name="forwardButton")
		self._redraw_captainslog()

	def update_view(self, number=0):
		""" update_view from PickBeltWidget, cleaning up the logbook subwidgets
		"""
		# self.session might not exist yet during callback setup for pickbelts
		if hasattr(self, 'session'):
			self._hide_statswidgets()
		super(LogBook, self).update_view(number)

	def save(self, db):
		for i in xrange(0, len(self._headings)):
			db("INSERT INTO logbook(heading, message) VALUES(?, ?)", \
			   self._headings[i], self._messages[i])
		db("INSERT INTO metadata(name, value) VALUES(?, ?)", \
		   "logbook_cur_entry", self._cur_entry)

	def load(self, db):
		for heading, message in db("SELECT heading, message FROM logbook"):
			# We need unicode strings as the entries are displayed on screen.
			self.add_entry(unicode(heading, 'utf-8'), unicode(message, 'utf-8'), False)
		value = db('SELECT value FROM metadata WHERE name = "logbook_cur_entry"')
		if (value and value[0] and value[0][0]):
			self._cur_entry = int(value[0][0])

	def show(self):
		if not hasattr(self,'_gui'):
			self._init_gui()
		if not self.is_visible():
			self._gui.show()
			self.session.ingame_gui.on_switch_main_widget(self)
			PauseCommand(suggestion=True).execute(self.session)

	def hide(self):
		if not self._hiding_widget:
			self._hiding_widget = True
			self.session.ingame_gui.on_switch_main_widget(None)
			self._hide_statswidgets()
			self._gui.hide()
			self._hiding_widget = False
			UnPauseCommand(suggestion=True).execute(self.session)

	def is_visible(self):
		return hasattr(self, '_gui') and self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def _redraw_captainslog(self):
		"""Redraws gui. Necessary when current message has changed."""
		texts = [u'', u'']
		heads = [u'', u'']
		if len(self._messages) != 0: # there is a current message if there is an entry
			texts[0] = self._messages[self._cur_entry]
			heads[0] = self._headings[self._cur_entry]
			if self._cur_entry+1 < len(self._messages): # maybe also one for the right side?
				texts[1] = self._messages[self._cur_entry+1]
				heads[1] = self._headings[self._cur_entry+1]
		else:
			heads[0] = _('Emptiness')
			texts[0] = "\n\n" + _('There is nothing written in your logbook yet!')

		self.backward_button.set_active()
		self.forward_button.set_active()

		if len(self._messages) == 0 or self._cur_entry == 0:
			self.backward_button.set_inactive()
		if len(self._messages) == 0 or self._cur_entry == len(self._messages) - 2:
			self.forward_button.set_inactive()

		self._gui.findChild(name="head_left").text = heads[0]
		self._gui.findChild(name="lbl_left").text = texts[0]
		self._gui.findChild(name="head_right").text = heads[1]
		self._gui.findChild(name="lbl_right").text = texts[1]
		self._gui.adaptLayout()

########
#        LOGBOOK  SUBWIDGET
########

	def add_entry(self, heading, message, show_logbook=True):
		"""Adds an entry to the logbook consisting of:
		@param heading: printed in top line.
		@param message: printed below heading, wraps. """
		#TODO last line of message text sometimes get eaten. Ticket #535
		heading = unicode(heading)
		message = unicode(message)
		self._headings.append(heading)
		self._messages.append(message)
		if len(self._messages) % 2 == 1:
			self._cur_entry = len(self._messages) - 1
		else:
			self._cur_entry = len(self._messages) - 2
		if show_logbook and hasattr(self, "_gui"):
			self._redraw_captainslog()

	def clear(self):
		"""Remove all entries"""
		self._headings = []
		self._messages = []
		self._cur_entry = None

	def get_cur_entry(self):
		return self._cur_entry

	def set_cur_entry(self, cur_entry):
		if cur_entry < 0 or cur_entry >= len(self._messages):
			raise ValueError
		self._cur_entry = cur_entry
		self._redraw_captainslog()

	def _scroll(self, direction):
		"""Scroll back or forth one message.
		@param direction: -1 or 1"""
		if len(self._messages) == 0:
			return
		#assert direction in (-1, 1)
		new_cur = self._cur_entry + direction
		if new_cur < 0 or new_cur >= len(self._messages):
			return # invalid scroll
		self._cur_entry = new_cur
		AmbientSoundComponent.play_special('flippage')
		self._redraw_captainslog()

########
#        STATISTICS  SUBWIDGET
########
#
#TODO list:
#  [ ] fix stats show/hide mess: how is update_view called before self.__init__
#  [ ] save last shown stats widget and re-show it when clicking on Statistics
#  [ ] semantic distinction between general widget and subwidgets (log, stats)
#
########

	def show_statswidget(self, widget='players'):
		"""Shows logbook with Statistics page selected"""
		logbook_index = [i for i,sec in enumerate(self.sections) if sec[0] == 'statistics'][0]
		self.update_view(logbook_index)
		self._hide_statswidgets()
		if widget:
			getattr(self, '_show_{widget}'.format(widget=widget))()
			self.stats_visible = widget

	def toggle_stats_visibility(self, widget='players'):
		"""
		Only hides logbook if hotkey of current stats selection pressed.
		Otherwise, switch to displaying the new widget instead of hiding.
		@param widget: 'players' or 'settlements' or 'ships'
		"""
		if self.stats_visible is not None and self.stats_visible == widget :
			self.hide()
		else:
			self.show()
			self.show_statswidget(widget=widget)

	def _show_ships(self):
		self.session.ingame_gui.players_ships.show()

	def _show_settlements(self):
		self.session.ingame_gui.players_settlements.show()

	def _show_players(self):
		self.session.ingame_gui.players_overview.show()

	def _hide_statswidgets(self):
		statswidgets = [
		  self.session.ingame_gui.players_overview,
		  self.session.ingame_gui.players_ships,
		  self.session.ingame_gui.players_settlements,
		  ]
		for statswidget in statswidgets:
			# we don't care which one is shown currently (if any), just hide all of them
			statswidget.hide()
		self.stats_visible = None



########
#        MESSAGE  AND  CHAT  HISTORY  SUBWIDGET
########
#
#TODO list:
#  [ ] use message bus to check for new updates
#  [ ] only display new message on update, not reload whole history
#  [ ] update message history on new game messages. not on sending a chat line
#
########

	def _send_chat_message(self):
		"""Sends a chat message. Called when user presses enter in the input field"""
		msg = self.textfield.text
		if msg:
			Chat(msg).execute(self.session)
			self.textfield.text = u''
		self._display_chat_history()
		self._display_message_history()

	def _display_message_history(self):
		self.messagebox.items = []
		messages = self.session.ingame_gui.message_widget.active_messages + \
		           self.session.ingame_gui.message_widget.archive
		for msg in sorted(messages,	key=lambda m: m.created):
			if msg.id != 'CHAT': # those get displayed in the chat window instead
				self.messagebox.items.append(msg.message)
		self.messagebox.selected = len(self.messagebox.items) - 1 # scroll to bottom

	def _display_chat_history(self):
		self.chatbox.items = []
		for msg in sorted(self.session.ingame_gui.message_widget.chat, key=lambda m: m.created):
			self.chatbox.items.append(msg.message)
		self.chatbox.selected = len(self.chatbox.items) - 1 # scroll to bottom

	def _chatfield_onfocus(self):
		"""Removes text in chat input field when it gets focused."""
		self.textfield.text = u""
		self.textfield.capture(None, 'mouseReleased', 'default')
