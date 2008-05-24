import fife
import game.main

class CursorTool(fife.IMouseListener):
	def __init__(self):
		super(CursorTool, self).__init__()
		game.main.fife.eventmanager.addMouseListener(self)

	def __del__(self):
		game.main.fife.eventmanager.removeMouseListener(self)

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
