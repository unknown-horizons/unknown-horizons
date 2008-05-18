import fife
import fifelog
import pychan

class Fife:
	def __init__(self):
		self.doQuit = False
		self.doBreak = False
		self.doReturn = None
		self.engine = fife.Engine()
		self.engineSettings = self.engine.getSettings()
		self.pychan = pychan
		self._gotFontSettings, self._gotSoundSettings, self._gotRenderSettings, self._gotScreenSettings = False, False, False, False
		self._gotSound, self._gotLogging, self._gotGUI = False, False, False
		self._gotInited = False

	def setDefaultFontSettings(self, font = 'content/gfx/fonts/samanata.ttf', size = 12, glyphs = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,!?-+/():;%&`'*#=[]\""):
		self.engineSettings.setDefaultFontPath(font)
		self.engineSettings.setDefaultFontSize(size)
		self.engineSettings.setDefaultFontGlyphs(glyphs)
		self._gotFontSettings = True

	def setSoundSettings(self, volume = 5.0):
		self.engineSettings.setInitialVolume(volume)
		self._gotSoundSettings = True

	def setRenderSettings(self, backend = 'OpenGL', removeFakeAlpha = False, imageChunkSize = 256):
		self.engineSettings.setRenderBackend(backend)
		self.engineSettings.setSDLRemoveFakeAlpha(1 if removeFakeAlpha else 0)
		try:
			self.engineSettings.setImageChunkingSize(imageChunkSize)
		except:
			pass
		self._gotRenderSettings = True

	def setScreenSettings(self, fullscreen = False, width = 1024, height = 768, bpp = 0):
		self.engineSettings.setFullScreen(1 if fullscreen else 0)
		self.engineSettings.setScreenWidth(width)
		self.engineSettings.setScreenHeight(height)
		self.engineSettings.setBitsPerPixel(bpp)
		self._gotFontSettings = True

	def initLogging(self, logToPrompt, logToFile, *modules):
		self.log = fifelog.LogManager(self.engine, 1 if logToPrompt else 0, 1 if logToFile else 0)
		self.log.setVisibleModules(*modules)
		self._gotLogging = True

	def initSound(self):
		self.soundmanager = self.engine.getSoundManager()
		self.soundmanager.init()
		self._gotSound = True

	def initGUI(self, debug = False):
		self.pychan.init(self.engine, debug)
		self.pychan.setupModalExecution(self.loop, self.breakLoop)
		self._gotGUI = True

	def init(self):
		#set default settings if none are set
		if not self._gotFontSettings:
			self.setDefaultFontSettings()
		if not self._gotSoundSettings:
			self.setSoundSettings()
		if not self._gotRenderSettings:
			self.setRenderSettings()
		if not self._gotScreenSettings:
			self.setScreenSettings()

		#start modules
		if not self._gotLogging:
			self.initLogging(True, True, 'controller')
		self.engine.init()
		if not self._gotSound:
			self.initSound()
		if not self._gotGUI:
			self.initGUI()
		self._gotInited = True

	def run(self):
		if not self._gotInited:
			self.init()
		self.engine.initializePumping()
		self.loop()
		self.engine.finalizePumping()

	def pump(self):
		pass

	def loop(self):
		while not self.doQuit:
			try:
				self.engine.pump()
			except fife.Exception, e:
				print e.getMessage()
				break
			self.pump()
			if self.doBreak:
				self.doBreak = False
				return self.doReturn

	def breakLoop(self, returnValue = None):
		self.doReturn = returnValue
		self.doBreak = True
	
	def quit(self):
		self.doQuit = True
