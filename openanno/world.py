import fife, fifelog
from loaders import loadMapFile
from savers import saveMapFile

class QuitListener(fife.ICommandListener, fife.IKeyListener):
	def __init__(self, world):
		fife.ICommandListener.__init__(self)
		fife.IKeyListener.__init__(self)
		self.quitRequested = 0
		eventmanager = world.engine.getEventManager()
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
		
class World(object):
	def __init__(self, engine, gui):
		self.engine = engine
		self.renderbackend = self.engine.getRenderBackend()

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
		self.view.resetRenderers()
		self.ctrl_scrollwheelvalue = self.cameras['main'].getRotation()
		self.shift_scrollwheelvalue = self.cameras['main'].getZoom()
		
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
		quitlistener = QuitListener(self)
		self.engine.initializePumping()
		
		while True:
			if quitlistener.quitRequested:
				break
				
			self.engine.pump()
			
		self.engine.finalizePumping()
