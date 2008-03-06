import sys, os, re, math, random

def _jp(path):
	return os.path.sep.join(path.split('/'))

_paths = ('../../engine/swigwrappers/python', '../../engine/extensions')
for p in _paths:
	if p not in sys.path:
		sys.path.append(_jp(p))

import fife, fifelog
from scripts import world, eventlistenerbase
from basicapplication import ApplicationBase
import pychan
import pychan.widgets as widgets
import settings as TDS


class ApplicationListener(eventlistenerbase.EventListenerBase):
	def __init__(self, engine, world):
		super(ApplicationListener, self).__init__(engine,regKeys=True,regCmd=True, regMouse=False, regConsole=True, regWidget=True)
		self.engine = engine
		self.world = world
		engine.getEventManager().setNonConsumableKeys([
			fife.Key.ESCAPE,
			fife.Key.F10,
			fife.Key.LEFT,
			fife.Key.RIGHT,
			fife.Key.UP,
			fife.Key.DOWN])
		
		self.quit = False
		self.aboutWindow = None
		
		self.rootpanel = pychan.loadXML('content/gui/rootpanel.xml')
		self.rootpanel.mapEvents({ 
			'quitButton' : self.onQuitButtonPress,
			'aboutButton' : self.onAboutButtonPress,
		})
		self.rootpanel.show()

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		consumed = False
		if keyval == fife.Key.ESCAPE:
			self.quit = True
			evt.consume()
		elif keyval == fife.Key.F10:
			self.engine.getGuiManager().getConsole().toggleShowHide()
			evt.consume()
		elif keystr == 'p':
			self.engine.getRenderBackend().captureScreen('screenshot.bmp')
			evt.consume()
	
	def onCommand(self, command):
		self.quit = (command.getCommandType() == fife.CMD_QUIT_GAME)
		if self.quit:
			command.consume()

	def onConsoleCommand(self, command):
		result = ''
		if command.lower() in ('quit', 'exit'):
			self.quit = True
			result = 'quitting'
		elif command.lower() in ( 'help', 'help()' ):
			self.engine.getGuiManager().getConsole().println( open( 'content/infotext.txt', 'r' ).read() )
			result = "-- End of help --"
		else:
			result = self.world.onConsoleCommand(command)
		if not result:
			try:
				result = str(eval(command))
			except:
				pass
		if not result:
			result = 'no result'
		return result

	def onQuitButtonPress(self):
		cmd = fife.Command()
		cmd.setSource(None)
		cmd.setCommandType(fife.CMD_QUIT_GAME)
		self.engine.getEventManager().dispatchCommand(cmd)
		
	def onAboutButtonPress(self):
		if not self.aboutWindow:
			self.aboutWindow = pychan.loadXML('content/gui/help.xml')
			self.aboutWindow.mapEvents({ 'closeButton' : self.aboutWindow.hide })
			self.aboutWindow.distributeData({ 'helpText' : open("content/infotext.txt").read() })
		self.aboutWindow.show()


class IslandDemo(ApplicationBase):
	def __init__(self):
		super(IslandDemo,self).__init__()
		pychan.init(self.engine, debug=TDS.PychanDebug)
		self.world = world.World(self.engine)
		self.listener = ApplicationListener(self.engine, self.world)
		self.world.load(TDS.MapFile)
		
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()
		
		if TDS.PlaySounds:
			# play track as background music
			emitter = self.soundmanager.createEmitter()
			id = self.engine.getSoundClipPool().addResourceFromFile('content/audio/music/music2.ogg')
			emitter.setSoundClip(id)
			emitter.setLooping(True)
			emitter.play()

	def createListener(self):
		pass # already created in constructor
		
	def _pump(self):
		if self.listener.quit:
			self.breakRequested = True
			self.world.save('content/datasets/maps/savefile.xml')
		else:
			self.world.pump()

def main():
	app = IslandDemo()
	app.run()


if __name__ == '__main__':
	if TDS.UsePsyco:
		# Import Psyco if available
		try:
			import psyco
			psyco.full()
			print "Psyco acceleration in use"
		except ImportError:
			print "Psyco acceleration not used"
	else:
		print "Psyco acceleration not used"
	main()
