import fife

class CameraController(fife.IKeyListener):
	def __init__(self, world):
		fife.IKeyListener.__init__(self)
		eventmanager = world.engine.getEventManager()
		eventmanager.addKeyListener(self)
		
	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		if keyval == fife.IKey.LEFT:
			print "blablubb"
		
	def keyReleased(self, evt):
		pass
	
