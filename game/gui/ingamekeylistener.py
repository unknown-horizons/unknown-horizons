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

	def __init__(self, engine, session):
		"""
		@var enginge: fife.Engine
		@var session: Game session
		"""
		super(IngameKeyListener, self).__init__()
		self.session = session
		self.eventmanager = engine.getEventManager()
		self.eventmanager.addKeyListener(self)

	def __del__(self):
		self.eventmanager.removeKeyListener(self)

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		if keyval == fife.Key.LEFT:
			self.session.view.scroll(-1, 0)
		elif keyval == fife.Key.RIGHT:
			self.session.view.scroll(1, 0)
		elif keyval == fife.Key.UP:
			self.session.view.scroll(0, -1)
		elif keyval == fife.Key.DOWN:
			self.session.view.scroll(0, 1)
		elif keystr == 'c':
			r = self.session.view.cam.getRenderer('CoordinateRenderer')
			r.setEnabled(not r.isEnabled())
		elif keystr == 'r':
			self.session.view.rotate_right()
		elif keystr == 'q':
			game.main.instance.fife.quit()
		elif keystr == 't':
			r = self.session.view.cam.getRenderer('GridRenderer')
			r.setEnabled(not r.isEnabled())
			evt.consume()

	def keyReleased(self, evt):
		pass
