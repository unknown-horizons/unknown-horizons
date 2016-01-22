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
		# Used to sum up the keyboard autoscrolling
		self.key_scroll = [0, 0]
		self.upKeyPressed = False
		self.downKeyPressed = False
		self.leftKeyPressed = False
		self.rightKeyPressed = False
		self.keyScrollSpeed = 25

	def end(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)
		self.session = None
		super(IngameKeyListener, self).end()

	def updateAutoscroll(self):
		self.key_scroll = [0, 0]
		if self.upKeyPressed:
			self.key_scroll[1] -= self.keyScrollSpeed;
		if self.downKeyPressed:
			self.key_scroll[1] += self.keyScrollSpeed;
		if self.leftKeyPressed:
			self.key_scroll[0] -= self.keyScrollSpeed;
		if self.rightKeyPressed:
			self.key_scroll[0] += self.keyScrollSpeed;

		self.session.view.autoscroll_keys(*self.key_scroll)

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		action = KeyConfig().translate(evt)

		_Actions = KeyConfig._Actions

		if action == _Actions.UP:
			self.upKeyPressed = True
		if action == _Actions.DOWN:
			self.downKeyPressed = True
		if action == _Actions.LEFT:
			self.leftKeyPressed = True
		if action == _Actions.RIGHT:
			self.rightKeyPressed = True

		self.updateAutoscroll()

		if self.session.ingame_gui.on_key_press(action, evt):
			evt.consume() # prevent other listeners from being called

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		_Actions = KeyConfig._Actions
		action = KeyConfig().translate(evt)


		if action == _Actions.UP:
			self.upKeyPressed = False
		if action == _Actions.DOWN:
			self.downKeyPressed = False
		if action == _Actions.LEFT:
			self.leftKeyPressed = False
		if action == _Actions.RIGHT:
			self.rightKeyPressed = False
		
		self.updateAutoscroll()
