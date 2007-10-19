#!/usr/bin/env python

import sys, os, re
_paths = ('engine/swigwrappers/python', 'engine/extensions')
for p in _paths:
	if p not in sys.path:
		sys.path.append(os.path.sep.join(p.split('/')))

import fife, fifelog
from loaders import loadMapFile
from savers import saveMapFile

from fifedit import *

INFO_TEXT = '''
Welcome to the OpenAnno techdemo, release Alpha\n\nKeybindings:
--------------
- P = Make screenshot
- LEFT = Move camera left
- RIGHT = Move camera right
- UP = Move camera up
- DOWN = Move camera down
- F10 = Toggle console on / off
- ESC = Quit techdemo


Have fun,
The FIFE OpenAnno teams
        http://www.openanno.org
	http://www.fifengine.de
'''


class InstanceReactor(fife.InstanceListener):
	def OnActionFinished(self, instance, action):
		pass

SCROLL_MODIFIER = 0.1
class MyEventListener(fife.IKeyListener, fife.ICommandListener, fife.IMouseListener, 
	              fife.ConsoleExecuter, fife.IWidgetListener):
	def __init__(self, world):
		self.world = world
		engine = world.engine
		eventmanager = engine.getEventManager()
		eventmanager.setNonConsumableKeys([
			fife.IKey.ESCAPE,
			fife.IKey.F10,
			fife.IKey.F9,
			fife.IKey.F8,
			fife.IKey.TAB,
			fife.IKey.LEFT,
			fife.IKey.RIGHT,
			fife.IKey.UP,
			fife.IKey.DOWN])
		
		fife.IKeyListener.__init__(self)
		eventmanager.addKeyListener(self)
		fife.ICommandListener.__init__(self)
		eventmanager.addCommandListener(self)
		fife.IMouseListener.__init__(self)
		eventmanager.addMouseListener(self)
		fife.ConsoleExecuter.__init__(self)
		engine.getGuiManager().getConsole().setConsoleExecuter(self)
		fife.IWidgetListener.__init__(self)
		eventmanager.addWidgetListener(self)
		
		self.engine = engine		
		self.quitRequested = False
		self.newTarget = None
		
		# scroll support
		self.horizscroll = 0
		self.vertscroll = 0
		
		# gui
		self.showInfo = False

	def mousePressed(self, evt):
		self.newTarget = fife.ScreenPoint(evt.getX(), evt.getY())

	def mouseReleased(self, evt):
		pass
	def mouseEntered(self, evt):
		pass
	def mouseExited(self, evt):
		pass
	def mouseClicked(self, evt):
		pass
	def mouseWheelMovedUp(self, evt):
		pass
	def mouseWheelMovedDown(self, evt):
		pass
	def mouseMoved(self, evt):
		pass
	def mouseDragged(self, evt):
		pass

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		if (keyval == fife.IKey.ESCAPE):
			self.quitRequested = True		
		elif (keyval == fife.IKey.F10):
			self.engine.getGuiManager().getConsole().toggleShowHide()
		elif (keyval == fife.IKey.LEFT):
			self.horizscroll -= SCROLL_MODIFIER
		elif (keyval == fife.IKey.RIGHT):
			self.horizscroll += SCROLL_MODIFIER
		elif (keyval == fife.IKey.UP):
			self.vertscroll -= SCROLL_MODIFIER
		elif (keyval == fife.IKey.DOWN):
			self.vertscroll += SCROLL_MODIFIER
		elif (keystr == 'p'):
			self.engine.getRenderBackend().captureScreen('techdemo.bmp')
	
	def keyReleased(self, evt):
		pass

	def onCommand(self, command):
		self.quitRequested = (command.getCommandType() == fife.CMD_QUIT_GAME)

	def onToolsClick(self):
		print "No tools set up yet"
	
	def onConsoleCommand(self, command):
		result = "no result"
		if command.lower() in ('quit', 'exit'):
			self.quitRequested = True
			return "quitting"
		
		try:
			result = str(eval(command))
		except:
			pass
		return result
	
	def onWidgetAction(self, evt):
		evtid = evt.getId()
		if evtid == 'WidgetEvtQuit':
			self.quitRequested = True
		if evtid == 'WidgetEvtAbout':
			if self.showInfo:
				self.showInfo = False
			else:
				self.showInfo = True

class Gui(object):
	def __init__(self, engine):
		self.engine = engine
		self.guimanager = self.engine.getGuiManager()
		glyphs = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" + \
		         ".,!?-+/:();%`'*#=[]"
		self.font = self.guimanager.createFont('techdemo/fonts/samanata.ttf', 12, glyphs)
		self.guimanager.setGlobalFont(self.font)
		self.widgets = []
		self.infoVisible = False
		self.renderbackend = self.engine.getRenderBackend()
		self.create_panel()
		self.create_infoscreen()

	# to prevent mem problems in current codebase and shorten the code length
	def register_widget(self, w, container):
		self.widgets.append(w)
		container.add(w)
	
	def create_panel(self):
		container = fife.Container()
		container.setOpaque(True)
		self.register_widget(container, self.guimanager)
		
		label1 = fife.Label('OpenAnnoTechDemo')
		label1.setPosition(1, 0)
		label1.setFont(self.font)
		self.register_widget(label1, container)
		
		container.setSize(label1.getWidth() + 2, label1.getHeight() + 2)
		container.setPosition(2,2)
		
		container2 = fife.Container()
		container2.setOpaque(True)
		self.register_widget(container2, self.guimanager)

		button1 = fife.Button('Quit')
		button1.setActionEventId('WidgetEvtQuit')
		button1.addActionListener(self.engine.getGuiManager())
		button1.adjustSize()
		button1.setPosition(1, 0)
		button1.setFont(self.font)
		self.register_widget(button1, container2)
		button2 = fife.Button('?')
		button2.setActionEventId('WidgetEvtAbout')
		button2.addActionListener(self.engine.getGuiManager())
		button2.setPosition(button1.getWidth() + 10, 0)
		button2.setFont(self.font)
		self.register_widget(button2, container2)
		container2.setSize(button1.getWidth() + button2.getWidth() + 10, button1.getHeight())
		container2.setPosition(1,28)
		
		container.setVisible(True)
		container2.setVisible(True)
	
	def create_infoscreen(self):
		self.container_info = fife.Container()
		self.container_info.setOpaque(True)
		self.container_info.setSize(self.renderbackend.getScreenWidth() - 2 * 200, self.renderbackend.getScreenHeight() - 2 * 100)
		self.container_info.setPosition(200, 100)
		self.register_widget(self.container_info, self.guimanager)

		label_info = fife.Label('Information box')
		label_info.setPosition(10, 10)
		label_info.setSize(self.renderbackend.getScreenWidth() - 2 * 210, 20)
		label_info.setFont(self.font)
		self.register_widget(label_info, self.container_info)
		
		# text
		text_info = fife.TextBox()
		text_info.setPosition(10,40)
		text_info.setText(INFO_TEXT)
		text_info.setOpaque(False)
		text_info.setBorderSize(0)
		self.register_widget(text_info, self.container_info)
		self.container_info.setVisible(False)
				
	def show_info(self, show):
		if show != self.infoVisible:
			self.container_info.setVisible(show)
			self.infoVisible = show

class World(object):
	def __init__(self, engine, gui):
		self.engine = engine
		self.renderbackend = self.engine.getRenderBackend()
		self.reactor = InstanceReactor()
		logman = self.engine.getLogManager()
		self.log = fifelog.LogManager(self.engine, promptlog=True, filelog=False)
		#self.log.setVisibleModules('hexgrid')

		self.eventmanager = self.engine.getEventManager()
		self.model = self.engine.getModel()
		self.metamodel = self.model.getMetaModel()
		self.camera = None
		self.gui = gui
		
	def __del__(self):
		self.engine.getView().removeCamera(self.camera)

	def create_world(self, path):
		self.map = loadMapFile(path, self.engine)
	
		self.elevation = self.map.getElevationsByString("id", "TechdemoMapElevation")[0]
		self.layer = self.elevation.getLayersByString("id", "TechdemoMapTileLayer")[0]
		
		# little workaround to show the agent above mapobjects
		self.agent_layer = self.elevation.getLayersByString("id", "TechdemoAgentLayer")[0]
		
		img = self.engine.getImagePool().getImage(self.layer.getInstances()[0].getObject().getStaticImageIndexByAngle(0))
		self.screen_cell_w = img.getWidth()
		self.screen_cell_h = img.getHeight()
		
		self.target = fife.Location()
		self.target.setLayer(self.agent_layer)

	def save_world(self, path):
		saveMapFile(path, self.engine, self.map)
		
	def adjust_views(self):
		self.camloc = fife.Location()
		self.camloc.setLayer(self.layer)
		self.camloc.setLayerCoordinates(fife.ModelCoordinate(5,-1))
		
		self.camera = fife.Camera()
		self.camera.setCellImageDimensions(self.screen_cell_w, self.screen_cell_h)

		self.camera.setRotation(45)
		self.camera.setTilt(60)

		self.camera.setLocation(self.camloc)
		viewport = fife.Rect(0, 0, self.renderbackend.getScreenWidth(), self.renderbackend.getScreenHeight())
		self.camera.setViewPort(viewport)
		self.engine.getView().addCamera(self.camera)

	def create_background_music(self):
		# set up the audio engine
		self.audiomanager = self.engine.getAudioManager()

		# play track as background music
		self.audiomanager.setAmbientSound('techdemo/audio/music/lagerhalle5.ogg')
			
	def run(self):
		evtlistener = MyEventListener(self)
		self.engine.initializePumping()
		
		while True:
			self.engine.pump()
			
			if (evtlistener.quitRequested):
				break

			#scroll the map with cursor keys
			if (evtlistener.horizscroll or evtlistener.vertscroll):
				cam_scroll = self.camloc.getExactLayerCoordinates()
				cam_scroll.x += evtlistener.horizscroll
				cam_scroll.y += evtlistener.vertscroll
				cam_scroll = self.camloc.setExactLayerCoordinates(cam_scroll)
				self.camera.setLocation(self.camloc)
				evtlistener.horizscroll = evtlistener.vertscroll = 0

			self.gui.show_info(evtlistener.showInfo)
				
		self.engine.finalizePumping()


if __name__ == '__main__':
	engine = fife.Engine()
	gui = Gui(engine)
	w = World(engine, gui)

	e = FIFEdit(engine)

	w.create_world("techdemo/maps/openanno-test-map.xml")
	w.adjust_views()
	w.create_background_music()
	w.run()
	w.save_world("techdemo/maps/savefile.xml")