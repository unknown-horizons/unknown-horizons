# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from horizons.i18n import load_xml_translated
from horizons.util import Callback
from horizons.gui.utility import center_widget


class LogBook(object):
	"""Implementation of the logbook described here:
	http://wiki.unknown-horizons.org/index.php/DD/GUI/Message_System

	It displays longer messages, that are essential for campaigns.
	"""
	def __init__(self):
		self._messages = [] # list of all messages
		self._cur_message = None # remember current location; 0 to len(messages)-1

		self._init_gui()

		""" logbook test code""
		self.add_entry(u"Welcome to the 1337 logbook!")
		self.add_entry(u"It's also known as 'Captains log'")
		self.add_entry(u"But mostly freaks prefer this term")
		self.add_entry(u"Well, that's nonsense")
		self.show()
		"" """

	def add_entry(self, message):
		"""Adds a message to the logbook"""
		self._messages.append(message)
		self._cur_message = len(self._messages) - 1
		self._redraw()

	def show(self):
		self._gui.show()

	def hide(self):
		self._gui.hide()

	def _scroll(self, direction):
		"""Scroll back or forth one message.
		@param direction: -1 or 1"""
		assert direction in (-1, 1)
		new_cur = self._cur_message + direction
		if new_cur < 0 or new_cur >= len(self._messages):
			return # invalid scroll
		self._cur_message = new_cur
		self._redraw()

	def _init_gui(self):
		"""Initial init of gui."""
		self._gui = load_xml_translated("captains_log.xml")
		self._gui.mapEvents({
		  'backwardButton' : Callback(self._scroll, -1),
		  'forwardButton' : Callback(self._scroll, 1),
		  'cancelButton' : self._gui.hide
		  })
		center_widget(self._gui)

	def _redraw(self):
		"""Redraws gui. Necessary when current message has changed."""
		texts = [u'', u'']
		if len(self._messages) != 0: # there is a current message if there is a message
			if self._cur_message == 0: # special case, current one is left since there are no older messages
				texts[0] = self._messages[self._cur_message]
				if self._cur_message+1 < len(self._messages): # maybe also right one
					texts[1] = self._messages[self._cur_message+1]
			else: # default case; current message on right side
				texts[0] = self._messages[self._cur_message-1]
				texts[1] = self._messages[self._cur_message]

		self._gui.findChild(name="lbl_left").text = texts[0]
		self._gui.findChild(name="lbl_right").text = texts[1]


