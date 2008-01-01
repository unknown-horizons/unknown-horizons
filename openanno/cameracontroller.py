from fife import IKeyListener

class CameraController(IKeyListener):
	def __init__(self):	
		IKeyListener.__init__(self)
		
	def keyPressed(self, event):
		pass
		
	def keyReleased(self, event):
		pass
	
