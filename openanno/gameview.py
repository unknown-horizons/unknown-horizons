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

import fife, fifelog
from openanno.cameracontroller import CameraController
from openanno.world import World
from openanno.player import Player
from openanno.localcontroller import LocalController

class QuitListener(fife.ICommandListener, fife.IKeyListener):
	def __init__(self, gamestate):
		fife.ICommandListener.__init__(self)
		fife.IKeyListener.__init__(self)
		self.quitRequested = 0
		eventmanager = gamestate.engine.getEventManager()
		eventmanager.addCommandListener(self)
		eventmanager.addKeyListener(self)
		
	def onCommand(self, command):
		self.quitRequested = (command.getCommandType() == fife.CMD_QUIT_GAME)
		
	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		if keyval == fife.IKey.ESCAPE:
			self.quitRequested = True
			
	def keyReleased(self, evt):
		pass
		
class GameView(object):
	def __init__(self, controller):
		self.controller = controller
		self.engine = controller.engine
		self.renderbackend = self.engine.getRenderBackend()
		self.model = controller.model

		self.eventmanager = self.engine.getEventManager()
		self.fifemodel = self.engine.getModel()
		self.metamodel = self.fifemodel.getMetaModel()
		self.view = self.engine.getView()		
		
		self.map = self.model.map
		self.elevation = self.map.getElevations("id", "OpenAnnoMapElevation")[0]
		self.layer = self.elevation.getLayers("id", "landLayer")[0]

		img = self.engine.getImagePool().getImage(self.layer.getInstances()[0].getObject().get2dGfxVisual().getStaticImageIndexByAngle(0))
		self.screen_cell_w = img.getWidth()
		self.screen_cell_h = img.getHeight()
		self.cameras = {}

	def _create_camera(self, name, coordinate, viewport):
		camera = self.view.addCamera("default", self.layer, fife.Rect(*[int(c) for c in viewport]), fife.ExactModelCoordinate(coordinate[0],coordinate[1],0))
		camera.setCellImageDimensions(self.screen_cell_w, self.screen_cell_h)
		camera.setRotation(45)
		camera.setTilt(62)

		self.cameras[name] = camera
	
	def adjust_views(self):
		W = self.renderbackend.getScreenWidth()
		H = self.renderbackend.getScreenHeight()
		maincoords = (1, 1)
		self._create_camera('main', maincoords, (0, 0, W, H))
		self.view.resetRenderers()
		
	def create_background_music(self):
		pass
		# play track as background music
#		emitter = self.soundmanager.createEmitter()
#		emitter.load('content/audio/music/music2.ogg')
#		emitter.setLooping(True)
#		emitter.play()
		
	def create_camera_controller(self):
		controller = CameraController()
		self.engine.getEventManager().addKeyListener(controller)
		
	def run(self):
		quitlistener = QuitListener(self)
		controller = CameraController(self)
		self.engine.initializePumping()
		
		while True:
			if quitlistener.quitRequested:
				break
				
			self.engine.pump()
			
		self.engine.finalizePumping()
