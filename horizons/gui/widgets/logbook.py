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

from horizons.util.gui import load_uh_widget
from horizons.util import Callback
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.command.game import UnPauseCommand, PauseCommand



@metaChangeListenerDecorator("pause_request")
@metaChangeListenerDecorator("unpause_request")
class LogBook(object):
	"""Implementation of the logbook as described here:
	http://wiki.unknown-horizons.org/w/Message_System

	It displays longer messages, that are essential for scenarios.
	Headings can be specified for each entry.
	"""
	def __init__(self, session):
		self.session = session
		self._headings = []
		self._messages = [] # list of all headings / messages
		self._cur_entry = None # remember current location; 0 to len(messages)-1

		self._init_gui()
		self._hiding_widget = False # True if and only if the widget is currently in the process of being hidden

		#self.add_entry(u"Heading",u"Welcome to the Captains log") # test code

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
		value = db("SELECT value FROM metadata WHERE name = \"logbook_cur_entry\"")
		if (value and value[0] and value[0][0]):
			self._cur_entry = int(value[0][0])
		self._redraw()

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
		if show_logbook:
			self._redraw()

	def clear(self):
		"""Remove all entries"""
		self._headings = []
		self._messages = []
		self._cur_entry = None

	def show(self):
		# don't show if there are no messages
		#if len(self._messages) == 0:
		#	return
		if not self._gui.isVisible():
			self._gui.show()
			self.session.ingame_gui.on_switch_main_widget(self)
			PauseCommand(suggestion=True).execute(self.session)

	def hide(self):
		if not self._hiding_widget:
			self._hiding_widget = True
			self.session.ingame_gui.on_switch_main_widget(None)
			self._gui.hide()
			self._hiding_widget = False
			UnPauseCommand(suggestion=True).execute(self.session)

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def get_cur_entry(self):
		return self._cur_entry

	def set_cur_entry(self, cur_entry):
		if cur_entry < 0 or cur_entry >= len(self._messages):
			raise ValueError
		self._cur_entry = cur_entry
		self._redraw()

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
		self._redraw()

	def _init_gui(self):
		"""Initial init of gui."""
		self._gui = load_uh_widget("captains_log.xml")
		self._gui.mapEvents({
		  'backwardButton' : Callback(self._scroll, -2),
		  'forwardButton' : Callback(self._scroll, 2),
		  'okButton' : self.hide
		  })
		self._gui.position_technique = "automatic" # "center:center"

		self.backward_button = self._gui.findChild(name="backwardButton")
		self.forward_button = self._gui.findChild(name="forwardButton")

	def _redraw(self):
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


