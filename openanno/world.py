import fife, fifelog
from loaders import loadMapFile
from savers import saveMapFile

class World(object):
	def __init__(self, engine, gui):
		self.engine = engine
		self.renderbackend = self.engine.getRenderBackend()
#		self.reactor = InstanceReactor()

		self.eventmanager = self.engine.getEventManager()
		self.model = self.engine.getModel()
		self.metamodel = self.model.getMetaModel()
		self.gui = gui
		self.view = self.engine.getView()
		
		self.ctrl_scrollwheelvalue = 0
		self.shift_scrollwheelvalue = 0
		self.scrollwheelvalue = 0
		
	def create_world(self, path):
		self.map = loadMapFile(path, self.engine)
		
		self.elevation = self.map.getElevations("id", "OpenAnnoMapElevation")[0]
		self.layer = self.elevation.getLayers("id", "landLayer")[0]
		
		self.agent_layer = self.elevation.getLayers("id", "spriteLayer")[0]
		
		img = self.engine.getImagePool().getImage(self.layer.getInstances()[0].getObject().get2dGfxVisual().getStaticImageIndexByAngle(0))
		self.screen_cell_w = img.getWidth()
		self.screen_cell_h = img.getHeight()
		
		self.target = fife.Location()
		self.target.setLayer(self.agent_layer)
		
		self.cameras = {}
		
		#self.scrollwheelvalue = self.elevation.getLayers("id", TDS.TestRotationLayerName)[0].getCellGrid().getRotation()

		# no movement at start
		self.target.setLayerCoordinates(fife.ModelCoordinate(4,4))

	def save_world(self, path):
		saveMapFile(path, self.engine, self.map)
		
	def _create_camera(self, name, coordinate, viewport):
		camera = self.view.addCamera()
		camera.setCellImageDimensions(self.screen_cell_w, self.screen_cell_h)
		camera.setRotation(45)
		camera.setTilt(60)

		camloc = fife.Location()
		camloc.setLayer(self.layer)
		camloc.setLayerCoordinates(fife.ModelCoordinate(*coordinate))
		camera.setViewPort(fife.Rect(*[int(c) for c in viewport]))
		camera.setLocation(camloc)		
		self.cameras[name] = camera
	
	def adjust_views(self):
		W = self.renderbackend.getScreenWidth()
		H = self.renderbackend.getScreenHeight()
		maincoords = (1, 1)
		self._create_camera('main', maincoords, (0, 0, W, H))
#		self._create_camera('small', (6,1), (W*0.6, H*0.01, W*0.39, H*0.36))
		self.view.resetRenderers()
		self.ctrl_scrollwheelvalue = self.cameras['main'].getRotation()
		self.shift_scrollwheelvalue = self.cameras['main'].getZoom()
		
#		renderer = self.view.getRenderer('CoordinateRenderer')#
#		renderer.clearActiveLayers()
#		renderer.addActiveLayer(self.elevation.getLayers("id", TDS.CoordinateLayerName)[0])

	def create_background_music(self):
		# set up the audio engine
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()

		# play track as background music
		emitter = self.soundmanager.createEmitter()
		emitter.load('content/audio/music/music2.ogg')
		emitter.setLooping(True)
		emitter.play()
			
	def run(self):
		camloc = fife.Location()
#		evtlistener = MyEventListener(self)
#		evtlistener.scrollwheelvalue = self.scrollwheelvalue
#		evtlistener.ctrl_scrollwheelvalue = self.ctrl_scrollwheelvalue
#		evtlistener.shift_scrollwheelvalue = self.shift_scrollwheelvalue
		self.engine.initializePumping()
		
#		showTileOutline = not evtlistener.showTileOutline
#		showCoordinates = not evtlistener.showCoordinates
#		showSecondCamera = not evtlistener.showSecondCamera
		
	#	smallcamx = self.cameras['small'].getLocation().getExactLayerCoordinates().x
	#	initial_camx = smallcamx
	#	cam_to_right = True
	#		self.cameras['small'].setEnabled(showSecondCamera)
		
		while True:
#			if showTileOutline != evtlistener.showTileOutline:
#				self.view.getRenderer('GridRenderer').setEnabled(evtlistener.showTileOutline)
#				showTileOutline = evtlistener.showTileOutline
#				
#			if showCoordinates != evtlistener.showCoordinates:
#				renderer = self.view.getRenderer('CoordinateRenderer')
#				showCoordinates = evtlistener.showCoordinates
#				renderer.setEnabled(showCoordinates)
#				
#			if showSecondCamera != evtlistener.showSecondCamera:
#				showSecondCamera = evtlistener.showSecondCamera
#				self.cameras['small'].setEnabled(showSecondCamera)
#				
#			if self.ctrl_scrollwheelvalue != evtlistener.ctrl_scrollwheelvalue:
#				self.ctrl_scrollwheelvalue = evtlistener.ctrl_scrollwheelvalue
#				self.cameras['main'].setRotation(self.ctrl_scrollwheelvalue)
#				print "camera rotation " + str(self.ctrl_scrollwheelvalue)
#			
#			if self.shift_scrollwheelvalue != evtlistener.shift_scrollwheelvalue:
#				self.shift_scrollwheelvalue = evtlistener.shift_scrollwheelvalue
#				self.cameras['main'].setZoom(self.shift_scrollwheelvalue)
#				print "camera zoom " + str(self.shift_scrollwheelvalue)
			
#			if self.scrollwheelvalue != evtlistener.scrollwheelvalue:
#				self.scrollwheelvalue = evtlistener.scrollwheelvalue
#				l = self.elevation.getLayers("id", TDS.TestRotationLayerName)[0]
#				l.getCellGrid().setRotation(self.scrollwheelvalue)
#				print "cell grid rotation " + str(self.scrollwheelvalue)
			
			self.engine.pump()
			
			# agent movement
#			if evtlistener.newTarget:
#				ec = self.cameras['main'].toElevationCoordinates(evtlistener.newTarget)
#				self.target.setElevationCoordinates(ec)
#				self.agent.act('walk', self.target, TDS.TestAgentSpeed)
#				print self.agent.getFifeId()
#				evtlistener.newTarget = None
			
#			if evtlistener.quitRequested:
#				break
			
#			if evtlistener.reloadRequested:
	#			camcoords = self.cameras['main'].getLocation().getExactLayerCoordinates()
#				evtlistener.reloadRequested = False
#				self.model.deleteMaps()
#				self.metamodel.deleteDatasets()
#				self.create_world(MAPFILE)
#				self.view.clearCameras()
#				self.adjust_views()
#				self.cameras['small'].setEnabled(showSecondCamera)
#				camloc = self.cameras['main'].getLocation()
#				camloc.setExactLayerCoordinates(camcoords)
#				self.cameras['main'].setLocation(camloc)
#				evtlistener.scrollwheelvalue = self.scrollwheelvalue
#
#			agentcoords = self.agent.getLocation().getElevationCoordinates()
#			if not ((self.agentcoords.x == agentcoords.x) and (self.agentcoords.y == agentcoords.y)):
#				loc = self.cameras['main'].getLocation()
#				loc.setElevationCoordinates(agentcoords)
#				self.cameras['main'].setLocation(loc)
#				self.agentcoords.x = agentcoords.x
#				self.agentcoords.y = agentcoords.y
			
			# scroll the map with cursor keys
#			if (evtlistener.horizscroll or evtlistener.vertscroll):
#				loc = self.cameras['main'].getLocation()
#				cam_scroll = loc.getExactLayerCoordinates()
#				cam_scroll.x += evtlistener.horizscroll
#				cam_scroll.y += evtlistener.vertscroll
#				loc.setExactLayerCoordinates(cam_scroll)
#				self.cameras['main'].setLocation(loc)
#				if 
#				.TestCameraPlacement:
#					print "camera thinks being in position ", cam_scroll.x, ", ", cam_scroll.y
#				evtlistener.horizscroll = evtlistener.vertscroll = 0

#			smallcam_loc = self.cameras['small'].getLocation()
#			c = smallcam_loc.getExactLayerCoordinates()
#			if showSecondCamera:
#				if cam_to_right:
#					smallcamx = c.x = c.x+0.01
#					if smallcamx > initial_camx+2:
#						cam_to_right = False
#				else:
#					smallcamx = c.x = c.x-0.01
#					if smallcamx < initial_camx-2:
#						cam_to_right = True
#				smallcam_loc.setExactLayerCoordinates(c)
#				self.cameras['small'].setLocation(smallcam_loc)
#
#			self.gui.show_info(evtlistener.showInfo)
			
		self.engine.finalizePumping()
