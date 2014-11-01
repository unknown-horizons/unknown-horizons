# ###################################################
# Copyright (C) 2008-2014 The Unknown Horizons Team
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
from horizons.gui.keylisteners import KeyConfig


class IngameKeyListener(fife.IKeyListener, LivingObject):
	"""KeyListener Class to process key presses ingame"""

	def __init__(self, session):
		super(IngameKeyListener, self).__init__()
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		horizons.globals.fife.eventmanager.addKeyListenerFront(self)
		self.keys_pressed = []
		# Used to sum up the keyboard autoscrolling
		self.key_scroll = [0, 0]

	def end(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)
		self.session = None
		super(IngameKeyListener, self).end()

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		action = KeyConfig().translate(evt)

		_Actions = KeyConfig._Actions

		was_pressed = keyval in self.keys_pressed
		if not was_pressed:
			self.keys_pressed.append(keyval)
			if action == _Actions.LEFT:
				self.key_scroll[0] -= 25
			if action == _Actions.RIGHT:
				self.key_scroll[0] += 25
			if action == _Actions.UP:
				self.key_scroll[1] -= 25
			if action == _Actions.DOWN:
				self.key_scroll[1] += 25

		# We scrolled, do autoscroll
		if self.key_scroll[0] != 0 or self.key_scroll[1] != 0:
			self.session.view.autoscroll_keys(*self.key_scroll)

		if self.session.ingame_gui.on_key_press(action, evt):
			evt.consume()  # prevent other listeners from being called

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		_Actions = KeyConfig._Actions
		action = KeyConfig().translate(evt)
		try:
			self.keys_pressed.remove(keyval)
		except Exception:
			return
		stop_horizontal = action in (_Actions.LEFT, _Actions.RIGHT)
		stop_vertical = action in (_Actions.UP, _Actions.DOWN)
		if stop_horizontal:
			self.key_scroll[0] = 0
		elif stop_vertical:
			self.key_scroll[1] = 0
		self.session.view.autoscroll_keys(*self.key_scroll)
