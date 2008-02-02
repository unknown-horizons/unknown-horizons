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
import math
from openanno.buildgamecommand import BuildGameCommand

class CameraController(fife.IKeyListener):
	"""Camera event processor"""
	
	def __init__(self, gamestate):
		fife.IKeyListener.__init__(self)
		eventmanager = gamestate.engine.getEventManager()
		eventmanager.addKeyListener(self)
		self.world = gamestate.world
		self.controller = gamestate.controller
		self.gamestate = gamestate
		
	def move_camera(self, xdir, ydir):
		loc = self.gamestate.cameras['main'].getLocation()
		cam_scroll = loc.getExactLayerCoordinates()
		if xdir != 0:
			cam_scroll.x += 0.1*xdir*(2/self.gamestate.cameras['main'].getZoom()) * math.cos(self.gamestate.cameras['main'].getRotation()/180.0 * math.pi)
			cam_scroll.y += 0.1*xdir*(2/self.gamestate.cameras['main'].getZoom()) * math.sin(self.gamestate.cameras['main'].getRotation()/180.0 * math.pi)
		if ydir != 0:
			cam_scroll.x += 0.1*ydir*(2/self.gamestate.cameras['main'].getZoom()) * math.sin(-self.gamestate.cameras['main'].getRotation()/180.0 * math.pi);
			cam_scroll.y += 0.1*ydir*(2/self.gamestate.cameras['main'].getZoom()) * math.cos(-self.gamestate.cameras['main'].getRotation()/180.0 * math.pi);
		loc.setExactLayerCoordinates(cam_scroll)
		self.gamestate.cameras['main'].setLocation(loc)

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		if keyval == fife.IKey.LEFT:
			self.move_camera(-3, 0)
		elif keyval == fife.IKey.RIGHT:
			self.move_camera(3, 0)
		elif keyval == fife.IKey.UP:
			self.move_camera(0, -3)
		elif keyval == fife.IKey.DOWN:
			self.move_camera(0, 3)
	
	def keyReleased(self, evt):
		pass
	
