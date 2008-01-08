# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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
from openanno.buildgamecommand import BuildGameCommand

class CameraController(fife.IKeyListener):
	"""Camera event processor"""
	
	def __init__(self, gamestate):
		fife.IKeyListener.__init__(self)
		eventmanager = gamestate.engine.getEventManager()
		eventmanager.addKeyListener(self)
		self.world = gamestate.world
		self.controller = gamestate.controller
		
	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		if keyval == fife.IKey.LEFT:
			self.controller.issue_command(BuildGameCommand(1, "Tent", self.world.local_playerid), self.world)
		
	def keyReleased(self, evt):
		pass
	
