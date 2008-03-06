import fife, math
from eventlistenerbase import EventListenerBase
from loaders import loadMapFile
from savers import saveMapFile
#from hero import Hero
#from girl import Girl
#from cloud import Cloud
#from beekeeper import Beekeeper
from agent import create_anonymous_agents
import settings as TDS

class World(EventListenerBase):
	def __init__(self, engine):
		super(World, self).__init__(engine, regMouse=True, regKeys=True)
		self.engine = engine
		self.eventmanager = engine.getEventManager()
		self.model = engine.getModel()
		self.metamodel = self.model.getMetaModel()
		self.view = self.engine.getView()
		self.filename = ''
		self.pump_ctr = 0 # for testing purposis
		self.ctrldown = False
		
		
	def reset(self):
		self.map, self.agentlayer = None, None
		self.cameras = {}
		#self.hero, self.girl, self.clouds, self.beekeepers = None, None, [], []
		self.cur_cam2_x, self.initial_cam2_x, self.cam2_scrolling_right = 0, 0, True
		self.target_rotation = 0

	def load(self, filename):
		self.filename = filename
		self.reset()
		self.map = loadMapFile(filename, self.engine)
		#self.agentlayer = self.map.getLayers("id", "TechdemoMapObjectLayer")[0]
		#self.hero = Hero(self.model, 'PC', self.agentlayer)
		#self.hero.start()
		#self.girl = Girl(self.model, 'NPC:girl', self.agentlayer)
		#self.girl.start()
		#cloudlayer = self.map.getLayers("id", "TechdemoMapCloudLayer")[0]
		#self.clouds = create_anonymous_agents(self.model, 'Cloud', cloudlayer, Cloud)
		#for cloud in self.clouds:
			#cloud.start(0.1, 0.05)
		#self.beekeepers = create_anonymous_agents(self.model, 'Beekeeper', self.agentlayer, Beekeeper)
		#for beekeeper in self.beekeepers:
			#beekeeper.start()

		for cam in self.view.getCameras():
			self.cameras[cam.getId()] = cam
		self.cameras['main'].attach(self.hero.agent)
				
		self.view.resetRenderers()
		renderer = fife.FloatingTextRenderer.getInstance(self.cameras['main'])
		textfont = self.engine.getGuiManager().createFont('content/fonts/rpgfont.png', 0, TDS.FontGlyphs);
		renderer.changeDefaultFont(textfont)
		
		renderer = fife.FloatingTextRenderer.getInstance(self.cameras['small'])
		renderer.changeDefaultFont(None)
		
		renderer = self.cameras['main'].getRenderer('CoordinateRenderer')
		renderer.clearActiveLayers()
		renderer.addActiveLayer(self.map.getLayers("id", TDS.CoordinateLayerName)[0])
		
		renderer = self.cameras['main'].getRenderer('QuadTreeRenderer')
		renderer.setEnabled(True)
		renderer.clearActiveLayers()
		if TDS.QuadTreeLayerName:
			renderer.addActiveLayer(self.map.getLayers("id", TDS.QuadTreeLayerName)[0])
		
		self.cameras['small'].getLocationRef().setExactLayerCoordinates( fife.ExactModelCoordinate( 40.0, 40.0, 0.0 ))
		self.initial_cam2_x = self.cameras['small'].getLocation().getExactLayerCoordinates().x
		self.cur_cam2_x = self.initial_cam2_x
		self.cam2_scrolling_right = True
		self.cameras['small'].setEnabled(False)
		
		self.target_rotation = self.cameras['main'].getRotation()
	
	def save(self, filename):
		saveMapFile(filename, self.engine, self.map)

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		if keystr == 't':
			r = self.cameras['main'].getRenderer('GridRenderer')
			r.setEnabled(not r.isEnabled())
		elif keystr == 'c':
			r = self.cameras['main'].getRenderer('CoordinateRenderer')
			r.setEnabled(not r.isEnabled())
		elif keystr == 's':
			c = self.cameras['small']
			c.setEnabled(not c.isEnabled())
		elif keystr == 'r':
			self.model.deleteMaps()
			self.metamodel.deleteDatasets()
			self.view.clearCameras()
			self.load(self.filename)
		elif keystr == 'o':
			self.target_rotation = (self.target_rotation + 90) % 360
		elif keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
			self.ctrldown = True
	
	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		if keyval in (fife.Key.LEFT_CONTROL, fife.Key.RIGHT_CONTROL):
			self.ctrldown = False
	
	def mouseWheelMovedUp(self, evt):
		if self.ctrldown:
			self.cameras['main'].setZoom(self.cameras['main'].getZoom() * 1.05)
	
	def mouseWheelMovedDown(self, evt):
		if self.ctrldown:
			self.cameras['main'].setZoom(self.cameras['main'].getZoom() / 1.05)
	
	def changeRotation(self):
		currot = self.cameras['main'].getRotation()
		if self.target_rotation != currot:
			self.cameras['main'].setRotation((currot + 5) % 360)
	
	def mouseReleased(self, evt):
		clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
		if (evt.getButton() == fife.MouseEvent.LEFT):
			target_mapcoord = self.cameras['main'].toMapCoordinates(clickpoint, False)
			target_mapcoord.z = 0
			l = fife.Location(self.agentlayer)
			l.setMapCoordinates(target_mapcoord)
			self.hero.run(l)
		elif (evt.getButton() == fife.MouseEvent.RIGHT):
			instances = self.cameras['main'].getMatchingInstances(clickpoint, self.agentlayer);
			print "selected instances on agent layer: ", [i.getObject().Id() for i in instances]

	def mouseMoved(self, evt):
		renderer = fife.InstanceRenderer.getInstance(self.cameras['main'])
		renderer.removeAllOutlines()
		
		pt = fife.ScreenPoint(evt.getX(), evt.getY())
		instances = self.cameras['main'].getMatchingInstances(pt, self.agentlayer);
		for i in instances:
			#if i.getObject().Id() in ('Girl', 'Beekeeper'):
				renderer.addOutlined(i, 173, 255, 47, 2)
	
	
	def onConsoleCommand(self, command):
		result = ''
		try:
			result = str(eval(command))
		except:
			pass
		return result

		
	def pump(self):
		if self.cameras['small'].isEnabled():
			loc = self.cameras['small'].getLocation()
			c = loc.getExactLayerCoordinatesRef()
			if self.cam2_scrolling_right:
				self.cur_cam2_x = c.x = c.x+0.1
				if self.cur_cam2_x > self.initial_cam2_x+10:
					self.cam2_scrolling_right = False
			else:
				self.cur_cam2_x = c.x = c.x-0.1
				if self.cur_cam2_x < self.initial_cam2_x-10:
					self.cam2_scrolling_right = True
			self.cameras['small'].setLocation(loc)
		if (self.pump_ctr % 50) == 0:
			#heroloc = self.hero.agent.getLocationRef()
			#girlloc = self.girl.agent.getLocationRef()
			#print 'hero - girl distance. layer: %f, map: %f' % (
				#heroloc.getLayerDistanceTo(girlloc), heroloc.getMapDistanceTo(girlloc))
		self.changeRotation()
		self.pump_ctr += 1
