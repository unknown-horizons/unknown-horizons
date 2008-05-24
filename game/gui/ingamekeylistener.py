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

import fife
import game.main

class IngameKeyListener(fife.IKeyListener):
	"""KeyListener Class to process key presses ingame"""

	def __init__(self):
		super(IngameKeyListener, self).__init__()
		game.main.fife.eventmanager.addKeyListener(self)
		self.keysPressed = []

	def __del__(self):
		game.main.fife.eventmanager.removeKeyListener(self)

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		was = keyval in self.keysPressed
		if was:
			self.keysPressed.append(keyval)
		if keyval == fife.Key.LEFT:
			if not was: game.main.game.view.autoscroll(-1, 0)
		elif keyval == fife.Key.RIGHT:
			if not was: game.main.game.view.autoscroll(1, 0)
		elif keyval == fife.Key.UP:
			if not was: game.main.game.view.autoscroll(0, -1)
		elif keyval == fife.Key.DOWN:
			if not was: game.main.game.view.autoscroll(0, 1)
		elif keystr == 'c':
			r = game.main.game.view.renderer['CoordinateRenderer']
			r.setEnabled(not r.isEnabled())
		elif keystr == 't':
			r = game.main.game.view.renderer['GridRenderer']
			r.setEnabled(not r.isEnabled())
		else:
			return
		evt.consume()

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		try:
			self.keysPressed.remove(keyval)
		except:
			return
		if keyval == fife.Key.LEFT:
			game.main.game.view.autoscroll(1, 0)
		elif keyval == fife.Key.RIGHT:
			game.main.game.view.autoscroll(-1, 0)
		elif keyval == fife.Key.UP:
			game.main.game.view.autoscroll(0, 1)
		elif keyval == fife.Key.DOWN:
			game.main.game.view.autoscroll(0, -1)
