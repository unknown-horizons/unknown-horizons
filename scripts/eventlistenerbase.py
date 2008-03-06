import fife

class EventListenerBase(fife.IKeyListener, fife.ICommandListener, fife.IMouseListener,
	                fife.ConsoleExecuter, fife.IWidgetListener):
	def __init__(self, engine, regKeys=False, regCmd=False, regMouse=False, regConsole=False, regWidget=False):
		self.eventmanager = engine.getEventManager()
		
		fife.IKeyListener.__init__(self)
		if regKeys:
			self.eventmanager.addKeyListener(self)
		fife.ICommandListener.__init__(self)
		if regCmd:
			self.eventmanager.addCommandListener(self)
		fife.IMouseListener.__init__(self)
		if regMouse:
			self.eventmanager.addMouseListener(self)
		fife.ConsoleExecuter.__init__(self)
		if regConsole:
			engine.getGuiManager().getConsole().setConsoleExecuter(self)
		fife.IWidgetListener.__init__(self)
		if regWidget:
			self.eventmanager.addWidgetListener(self)
		
	
	def mousePressed(self, evt):
		pass
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
		pass
	def keyReleased(self, evt):
		pass
	def onCommand(self, command):
		pass
	def onToolsClick(self):
		print "No tools set up yet"
	def onConsoleCommand(self, command):
		pass
	def onWidgetAction(self, evt):
		pass
