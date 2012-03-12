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

import json
from itertools import groupby
from fife.extensions.pychan.widgets import HBox, Icon, Label

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
		self._widgets = [] # list of lists of all widgets added to a logbook page
		self._cur_entry = None # remember current location; 0 to len(messages)-1
		self._hiding_widget = False # True if and only if the widget is currently in the process of being hidden
		self.stats_visible = None
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
		#self._display_chat_history() # initially print all loaded messages
		#self._display_message_history()

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
		db("INSERT INTO logbook(widgets) VALUES(?)", json.dumps(self._widgets))
		db("INSERT INTO metadata(name, value) VALUES(?, ?)", \
		   "logbook_cur_entry", self._cur_entry)

	def load(self, db):
		db_data = db("SELECT widgets FROM logbook")
		widget_list = json.loads(db_data[0][0] if db_data else "[]")
		for widgets in widget_list:
			self.add_captainslog_entry(widgets, show_logbook=False)
		value = db('SELECT value FROM metadata WHERE name = "logbook_cur_entry"')
		if (value and value[0] and value[0][0]):
			self.set_cur_entry(int(value[0][0])) # this also redraws

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
		if len(self._widgets) > 0: # there is something to display if this has items
			self._display_widgets_on_page(self._widgets[self._cur_entry], 'left')
			if self._cur_entry+1 < len(self._widgets): # check for content on right page
				self._display_widgets_on_page(self._widgets[self._cur_entry+1], 'right')
			else:
				self._display_widgets_on_page([], 'right') # display empty page
		else:
			self._display_widgets_on_page([
			  ['Headline', _("Emptiness")],
			  ['Image', "content/gui/images/background/hr.png"],
			  ['Label', "\n\n"],
			  ['Label', _('There is nothing written in your logbook yet!')],
				], 'left')
		self.backward_button.set_active()
		self.forward_button.set_active()
		if len(self._widgets) == 0 or self._cur_entry == 0:
			self.backward_button.set_inactive()
		if len(self._widgets) == 0 or self._cur_entry >= len(self._widgets) - 2:
			self.forward_button.set_inactive()
		self._gui.adaptLayout()

########
#        LOGBOOK  SUBWIDGET
########

	def parse_logbook_item(self, widget):
		# json.loads() returns unicode, thus convert strings and compare to unicode
		# Image works with str() since pychan can only use str objects as file path
		if widget and widget[0]: # allow empty Labels
			widget_type = unicode(widget[0])
		if isinstance(widget, basestring):
			add = Label(text=unicode(widget), wrap_text=True, max_size=(340,508))
		elif widget_type == u'Label':
			add = Label(text=unicode(widget[1]), wrap_text=True, max_size=(340,508))
		elif widget_type == u'Image':
			add = Icon(image=str(widget[1]))
		elif widget_type == u'Gallery':
			add = HBox()
			for image in widget[1]:
				add.addChild(Icon(image=str(image)))
		elif widget_type == u'Headline':
			add = Label(text=unicode(widget[1]))
			add.stylize('headline')
		else:
			print '[WW] Warning: Unknown widget type {typ} in widget {wdg}'.format(
				typ=widget[0], wdg=widget)
			add = None
		return add

	def _display_widgets_on_page(self, widgets, page):
		"""
		@param widgets: widget list, cf. docstring of add_captainslog_entry
		@param page: 'left' or 'right'
		"""
		widgetbox = self._gui.findChild(name="custom_widgets_{page}".format(page=page))
		widgetbox.removeAllChildren()
		for widget_definition in widgets:
			add = self.parse_logbook_item(widget_definition)
			if add is not None:
				widgetbox.addChild(add)

	def add_captainslog_entry(self, widgets, show_logbook=True):
		"""Adds an entry to the logbook VBoxes consisting of a widget list.
		Check e.g. content/scenarios/tutorial_en.yaml for real-life usage.

		@param widgets: Each item in here is a list like the following:
		[Label, "Awesome text to be displayed as a label"]
		"Shortcut notation for a Label"
		[Headline, "Label to be styled as headline (in small caps)"]
		[Image, "content/gui/images/path/to/the/file.png"]
		[Gallery, ["/path/1.png", "/path/file.png", "/file/3.png"]]
		[Pagebreak]  <==  not implemented yet
		"""
		#TODO last line of message text sometimes get eaten. Ticket #535
		def _split_on_pagebreaks(widgets):
			"""This black magic splits the widget list on each ['Pagebreak']
			>> [['a','a'], ['b','b'], ['Pagebreak'], ['c','c'], ['d','d']]
			>>>> into [[['a', 'a'], ['b', 'b']], [['c', 'c'], ['d', 'd']]]
			#TODO n successive pagebreaks should insert (n-1) blank pages (currently 0 are inserted)
			"""
			return [list(l[1]) for l in groupby(widgets, lambda x: x != ['Pagebreak']) if l[0]]

		for widget_list in _split_on_pagebreaks(widgets):
			self._widgets.append(widget_list)
			for widget_definition in widget_list:
				self.parse_logbook_item(widget_definition)
		# if a new entry contains more than one page, we want to display the first
		# unread message. note that len(widgets) starts at 1 and _cur_entry at 0.
		# position always refers to the left page, so only multiples of 2 are valid
		len_old = len(self._widgets) - len(_split_on_pagebreaks(widgets))
		if len_old % 2 == 1: # uneven amount => empty last page, space for 1 new
			self._cur_entry = len_old - 1
		else: # even amount => all pages filled. we could display two new messages
			self._cur_entry = len_old
		if show_logbook and hasattr(self, "_gui"):
			self._redraw_captainslog()
			self.show()

	def clear(self):
		"""Remove all entries"""
		self._widgets = []
		self._cur_entry = None

	def get_cur_entry(self):
		return self._cur_entry

	def set_cur_entry(self, cur_entry):
		if cur_entry < 0 or cur_entry >= len(self._widgets):
			raise ValueError
		self._cur_entry = cur_entry
		self._redraw_captainslog()

	def _scroll(self, direction):
		"""Scroll back or forth one message.
		@param direction: -1 or 1"""
		if len(self._widgets) == 0:
			return
		new_cur = self._cur_entry + direction
		if new_cur < 0 or new_cur >= len(self._widgets):
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
