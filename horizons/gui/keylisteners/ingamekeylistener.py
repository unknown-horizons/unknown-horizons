# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from fife import fife

import horizons.globals
from horizons.util.living import LivingObject

from .keyconfig import KeyConfig


class IngameKeyListener(fife.IKeyListener, LivingObject):
	"""KeyListener Class to process key presses ingame"""

	def __init__(self, session):
		super().__init__()
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		self.keyconfig = KeyConfig()
		horizons.globals.fife.eventmanager.addKeyListenerFront(self)
		# Used to sum up the keyboard autoscrolling
		self.key_scroll = [0, 0]
		self.up_key_pressed = False
		self.down_key_pressed = False
		self.left_key_pressed = False
		self.right_key_pressed = False
		self.key_scroll_speed = 25
		# Last event (to avoid double-firing)
		self.last_evt = {'type': None, 'value': None}

	def end(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)
		self.session = None
		super().end()

	def updateAutoscroll(self):
		self.key_scroll = [0, 0]
		if self.up_key_pressed:
			self.key_scroll[1] -= self.key_scroll_speed
		if self.down_key_pressed:
			self.key_scroll[1] += self.key_scroll_speed
		if self.left_key_pressed:
			self.key_scroll[0] -= self.key_scroll_speed
		if self.right_key_pressed:
			self.key_scroll[0] += self.key_scroll_speed

		self.session.view.autoscroll_keys(*self.key_scroll)

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		action = self.keyconfig.translate(evt)

		_Actions = KeyConfig._Actions

		if action == _Actions.UP:
			self.up_key_pressed = True
		if action == _Actions.DOWN:
			self.down_key_pressed = True
		if action == _Actions.LEFT:
			self.left_key_pressed = True
		if action == _Actions.RIGHT:
			self.right_key_pressed = True

		self.updateAutoscroll()

		# if the current event is identical to the previous one, ignore it
		if (evt.getType() == self.last_evt['type'] and
				evt.getKey().getValue() == self.last_evt['value']):
			evt.consume() # prevent other listeners from being called
			return

		if self.session.ingame_gui.on_key_press(action, evt):
			evt.consume() # prevent other listeners from being called

		# update last event
		self.last_evt['type'] = evt.getType()
		self.last_evt['value'] = evt.getKey().getValue()

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		_Actions = KeyConfig._Actions
		action = self.keyconfig.translate(evt)

		if action == _Actions.UP:
			self.up_key_pressed = False
		if action == _Actions.DOWN:
			self.down_key_pressed = False
		if action == _Actions.LEFT:
			self.left_key_pressed = False
		if action == _Actions.RIGHT:
			self.right_key_pressed = False

		self.updateAutoscroll()

		# update last event
		self.last_evt['type'] = evt.getType()
		self.last_evt['value'] = evt.getKey().getValue()
