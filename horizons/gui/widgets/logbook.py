# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

import json
import logging
from itertools import groupby

from fife.extensions.pychan.widgets import HBox, Icon, Label

from horizons.command.game import UnPauseCommand
from horizons.command.misc import Chat
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.widgets.pickbeltwidget import PickBeltWidget
from horizons.gui.windows import Window
from horizons.i18n import gettext as _, gettext_lazy as _lazy
from horizons.scenario.actions import show_message
from horizons.util.python.callback import Callback


class LogBook(PickBeltWidget, Window):
	"""Implementation of the logbook as described here:
	http://wiki.unknown-horizons.org/w/Message_System

	It displays longer messages, which are essential for scenarios.
	Headings can be specified for each entry.
	"""
	log = logging.getLogger('gui.widgets.logbook')

	widget_xml = 'captains_log.xml'
	page_pos = (170, 38)
	sections = (('logbook', _lazy('Logbook')),
	            ('statistics', _lazy('Statistics')),
	            ('chat_overview', _lazy('Chat')))

	def __init__(self, session, windows):
		self.statistics_index = [i for i, sec in self.sections].index('statistics')
		self.logbook_index = [i for i, sec in self.sections].index('logbook')
		self._page_ids = {} # dict mapping self._cur_entry to message.msgcount
		super(LogBook, self).__init__()
		self.session = session
		self._windows = windows
		self._parameters = [] # list of lists of all parameters added to a logbook page
		self._message_log = [] # list of all messages that have been displayed
		self._messages_to_display = [] # list messages to display on page close
		self._displayed_messages = [] # list of messages that were already displayed
		self._cur_entry = None # remember current location; 0 to len(messages)-1
		self._hiding_widget = False # True if and only if the widget is currently in the process of being hidden
		self.stats_visible = None
		self.last_stats_widget = 'players'
		self.current_mode = 0 # used to determine if the logbook is on the statistics page
		self._init_gui()

#		self.add_captainslog_entry([
#		  ['Headline', "Heading"],
#		  ['Image', "content/gui/images/background/hr.png"],
#		  ['Label', "Welcome to the Captain's log"],
#		  ['Label', "\n\n"],
#			]) # test code

	def _init_gui(self):
		"""Initial gui setup for all subpages accessible through pickbelts."""
		self._gui = self.get_widget()
		self._gui.mapEvents({
		  OkButton.DEFAULT_NAME : self._windows.close,
		  'backwardButton' : Callback(self._scroll, -2),
		  'forwardButton' : Callback(self._scroll, 2),
		  'stats_players' : Callback(self.show_statswidget, widget='players'),
		  'stats_settlements' : Callback(self.show_statswidget, widget='settlements'),
		  'stats_ships' : Callback(self.show_statswidget, widget='ships'),
		  'chatTextField' : self._send_chat_message,
		  })

		# stuff in the game message / chat history subwidget
		self.textfield = self._gui.findChild(name="chatTextField")
		self.textfield.capture(self._chatfield_onfocus, 'mouseReleased', 'default')
		self.chatbox = self._gui.findChild(name="chatbox")
		self.messagebox = self._gui.findChild(name="game_messagebox")
		#self._display_chat_history() # initially print all loaded messages
		#self._display_message_history()

		# these buttons flip pages in the captain's log if there are more than two
		self.backward_button = self._gui.findChild(name="backwardButton")
		self.forward_button = self._gui.findChild(name="forwardButton")
		self._redraw_captainslog()

	def update_view(self, number=0):
		""" update_view from PickBeltWidget, cleaning up the logbook subwidgets
		"""
		self.current_mode = number

		# self.session might not exist yet during callback setup for pickbelts
		if hasattr(self, 'session'):
			self._hide_statswidgets()
		if self.statistics_index == number:
			self.show_statswidget(self.last_stats_widget)
		super(LogBook, self).update_view(number)

	def save(self, db):
		db("INSERT INTO logbook(widgets) VALUES(?)", json.dumps(self._parameters))
		for message in self._message_log:
			db("INSERT INTO logbook_messages(message) VALUES(?)", message)
		db("INSERT INTO metadata(name, value) VALUES(?, ?)",
		   "logbook_cur_entry", self._cur_entry)

	def load(self, db):
		db_data = db("SELECT widgets FROM logbook")
		widget_list = json.loads(db_data[0][0] if db_data else "[]")
		for widgets in widget_list:
			self.add_captainslog_entry(widgets, show_logbook=False)

		for msg in db("SELECT message FROM logbook_messages"):
			self._message_log.append(msg[0]) # each line of the table is one tuple
		# wipe self._messages_to_display on load, otherwise all previous messages get displayed
		self._messages_to_display = []
		self._displayed_messages = []

		value = db('SELECT value FROM metadata WHERE name = "logbook_cur_entry"')
		if (value and value[0] and value[0][0]):
			self.set_cur_entry(int(value[0][0])) # this also redraws

		self.display_messages()

	def show(self, msg_id=None):
		if not hasattr(self, '_gui'):
			self._init_gui()
		if msg_id:
			self._cur_entry = self._page_ids[msg_id]
		if not self.is_visible():
			self._gui.show()
			self._redraw_captainslog()
			if self.current_mode == self.statistics_index:
				self.show_statswidget(self.last_stats_widget)

	def display_messages(self):
		"""Display all messages in self._messages_to_display and map the to the current logbook page"""
		for message in self._messages_to_display:
			if message in self._displayed_messages:
				continue
			for msg_id in show_message(self.session, "logbook", message):
				self._page_ids[msg_id] = self._cur_entry
				self._displayed_messages.append(message)

	def hide(self):
		if not self._hiding_widget:
			self._hiding_widget = True
			self._hide_statswidgets()
			self._gui.hide()
			self._hiding_widget = False

			self.display_messages()
			self._message_log.extend(self._messages_to_display)
			self._messages_to_display = []
		# Make sure the game is unpaused always and in any case
		UnPauseCommand(suggestion=False).execute(self.session)

	def is_visible(self):
		return hasattr(self, '_gui') and self._gui.isVisible()

	def _redraw_captainslog(self):
		"""Redraws gui. Necessary when current message has changed."""
		if self._parameters: # there is something to display if this has items
			self._display_parameters_on_page(self._parameters[self._cur_entry], 'left')
			if self._cur_entry+1 < len(self._parameters): # check for content on right page
				self._display_parameters_on_page(self._parameters[self._cur_entry+1], 'right')
			else:
				self._display_parameters_on_page([], 'right') # display empty page
		else:
			self._display_parameters_on_page([
			  ['Headline', _("Emptiness")],
			  ['Image', "content/gui/images/background/hr.png"],
			  ['Label', u"\n\n"],
			  ['Label', _('There is nothing written in your logbook yet!')],
				], 'left')
		self.backward_button.set_active()
		self.forward_button.set_active()
		if not self._parameters or self._cur_entry == 0:
			self.backward_button.set_inactive()
		if not self._parameters or self._cur_entry >= len(self._parameters) - 2:
			self.forward_button.set_inactive()
		self._gui.adaptLayout()


########
#        LOGBOOK  SUBWIDGET
########

	def parse_logbook_item(self, parameter):
		# Some error checking for widgets that are to be loaded.
		# This happens, for example, with outdated YAML stored in old
		# scenario savegames. Instead of crashing, display nothing.
		def _icon(image):
			try:
				# Pychan can only use str objects as file path.
				# json.loads() however returns unicode.
				return Icon(image=str(image))
			except RuntimeError:
				return None

		def _label(text, font='default'):
			try:
				return Label(text=unicode(text), wrap_text=True,
				             min_size=(325, 0), max_size=(325, 1024),
				             font=font)
			except RuntimeError:
				return None

		if parameter and parameter[0]: # allow empty Labels
			parameter_type = parameter[0]
		if isinstance(parameter, basestring):
			add = _label(parameter)
		elif parameter_type == u'Label':
			add = _label(parameter[1])
		elif parameter_type == u'Image':
			add = _icon(parameter[1])
		elif parameter_type == u'Gallery':
			add = HBox()
			for image in parameter[1]:
				new_icon = _icon(image)
				if new_icon is not None:
					add.addChild(new_icon)
		elif parameter_type == u'Headline':
			add = HBox()
			is_not_last_headline = self._parameters and self._cur_entry < (len(self._parameters) - 2)
			if is_not_last_headline:
				add.addChild(_icon("content/gui/images/tabwidget/done.png"))
			add.addChild(_label(parameter[1], font='headline'))
		elif parameter_type == u'BoldLabel':
			add = _label(parameter[1], font='default_bold')
		elif parameter_type == u'Message':
			add = None
			# parameters are re-read on page reload.
			# duplicate_message stops messages from
			# being duplicated on page reload.
			message = parameter[1]
			# message is already going to be displayed or has been displayed
			# before (e.g. re-opening older logbook pages)
			duplicate_message = (message in self._messages_to_display or
								message in self._message_log)

			if not duplicate_message:
				self._messages_to_display.append(message) # the new message has not been displayed
		else:
			self.log.warning('Unknown parameter type %s in parameter %s',
			                 parameter[0], parameter)
			add = None
		return add

	def _display_parameters_on_page(self, parameters, page):
		"""
		@param parameters: parameter list, cf. docstring of add_captainslog_entry
		@param page: 'left' or 'right'
		"""
		parameterbox = self._gui.findChild(name="custom_widgets_{page}".format(page=page))
		parameterbox.removeAllChildren()
		for parameter_definition in parameters:
			add = self.parse_logbook_item(parameter_definition)
			if add is not None:
				parameterbox.addChild(add)

	def add_captainslog_entry(self, parameters, show_logbook=True):
		"""Adds an entry to the logbook VBoxes consisting of a parameter list.
		Check e.g. content/scenarios/tutorial_en.yaml for real-life usage.

		@param parameters: Each item in here is a list like the following:
		[Label, "Awesome text to be displayed as a label"]
		"Shortcut notation for a Label"
		[Headline, "Label to be styled as headline (in small caps)"]
		[BoldLabel, "Like Label but with bold font, use to highlight lines"]
		[Image, "content/gui/images/path/to/the/file.png"]
		[Gallery, ["/path/1.png", "/path/file.png", "/file/3.png"]]
		[Message, "Text to display as a notification on logbook close"]
		[Pagebreak]
		"""
		#TODO last line of message text sometimes get eaten. Ticket #535
		def _split_on_pagebreaks(parameters):
			"""This black magic splits the parameter list on each ['Pagebreak']
			>> [['a','a'], ['b','b'], ['Pagebreak'], ['c','c'], ['d','d']]
			>>>> into [[['a', 'a'], ['b', 'b']], [['c', 'c'], ['d', 'd']]]
			#TODO n successive pagebreaks should insert (n-1) blank pages (currently 0 are inserted)
			"""
			return [list(l[1]) for l in groupby(parameters, lambda x: x != ['Pagebreak']) if l[0]]

		# If a scenario goal has been completed, remove the corresponding message
		for message in self._displayed_messages:
			self.session.ingame_gui.message_widget.remove(message)

		self._displayed_messages = [] # Reset displayed messages
		for parameter_list in _split_on_pagebreaks(parameters):
			self._parameters.append(parameter_list)
			for parameter_definition in parameter_list:
				self.parse_logbook_item(parameter_definition)
		# if a new entry contains more than one page, we want to display the first
		# unread message. note that len(parameters) starts at 1 and _cur_entry at 0.
		# position always refers to the left page, so only multiples of 2 are valid
		len_old = len(self._parameters) - len(_split_on_pagebreaks(parameters))
		if len_old % 2 == 1: # uneven amount => empty last page, space for 1 new
			self._cur_entry = len_old - 1
		else: # even amount => all pages filled. we could display two new messages
			self._cur_entry = len_old
		if show_logbook and hasattr(self, "_gui"):
			self._redraw_captainslog()
			self._windows.open(self)
			self.show_logbookwidget()

	def clear(self):
		"""Remove all entries"""
		self._parameters = []
		self._cur_entry = None

	def get_cur_entry(self):
		return self._cur_entry

	def set_cur_entry(self, cur_entry):
		if cur_entry < 0 or cur_entry >= len(self._parameters):
			raise ValueError
		self._cur_entry = cur_entry
		self._redraw_captainslog()

	def _scroll(self, direction):
		"""Scroll back or forth one message.
		@param direction: -1 or 1"""
		if not self._parameters:
			return
		new_cur = self._cur_entry + direction
		if new_cur < 0 or new_cur >= len(self._parameters):
			return # invalid scroll
		self._cur_entry = new_cur
		AmbientSoundComponent.play_special('flippage')
		self._redraw_captainslog()

	def show_logbookwidget(self):
		"""Shows logbook with Logbook page selected"""
		if self.current_mode != self.logbook_index:
			self.update_view(self.logbook_index)

########
#        STATISTICS  SUBWIDGET
########
#
#TODO list:
#  [ ] Extract this stuff to extra widget class that properly handles all the
#      hide and save calls
#  [ ] fix stats show/hide mess: how is update_view called before self.__init__
#  [ ] save last shown stats widget and re-show it when clicking on Statistics
#  [ ] semantic distinction between general widget and subwidgets (log, stats)
#
########

	def show_statswidget(self, widget='players'):
		"""Shows logbook with Statistics page selected"""
		if self.current_mode != self.statistics_index:
			self.update_view(self.statistics_index)
		self._hide_statswidgets()
		if widget:
			getattr(self, '_show_{widget}'.format(widget=widget))()
			self.stats_visible = widget
			self.last_stats_widget = widget

	def toggle_stats_visibility(self, widget='players'):
		"""
		Only hides logbook if hotkey of current stats selection pressed.
		Otherwise, switch to displaying the new widget instead of hiding.
		@param widget: 'players' or 'settlements' or 'ships'
		"""
		# we're treating every statswidget as a separate window, so if the stats change,
		# close the logbook and reopen it with a different active widget
		if self.stats_visible != widget:
			if self.stats_visible:
				self._windows.close()

			self._windows.open(self)
			self.show_statswidget(widget=widget)
		else:
			self._windows.close()

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
#  [x] update message history on new game messages. not on sending a chat line
#  [ ] implement word wrapping for message history display
#
########

	def _send_chat_message(self):
		"""Sends a chat message. Called when user presses enter in the input field"""
		msg = self.textfield.text
		if msg:
			Chat(msg).execute(self.session)
			self.textfield.text = u''
		self._display_chat_history()

	def display_message_history(self):
		self.messagebox.items = []
		messages = self.session.ingame_gui.message_widget.active_messages + \
		        self.session.ingame_gui.message_widget.archive
		for msg in sorted(messages, key=lambda m: m.created):
			if msg.id != 'CHAT': # those get displayed in the chat window instead
				self.messagebox.items.append(msg.message)
		self.messagebox.selected = len(self.messagebox.items) - 1 # scroll to bottom

	def _display_chat_history(self):
		self.chatbox.items = []
		messages = self.session.ingame_gui.message_widget.chat
		for msg in sorted(messages, key=lambda m: m.created):
			self.chatbox.items.append(msg.message)
		self.chatbox.selected = len(self.chatbox.items) - 1 # scroll to bottom

	def _chatfield_onfocus(self):
		"""Removes text in chat input field when it gets focused."""
		self.textfield.text = u''
		self.textfield.capture(None, 'mouseReleased', 'default')
