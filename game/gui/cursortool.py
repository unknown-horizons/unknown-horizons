import fife

class CursorTool(fife.IMouseListener):
    def __init__(self, eventmanager):
        fife.IMouseListener.__init__(self)
        self.eventmanager = eventmanager
        self.eventmanager.addMouseListener(self)

def __del__(self):
        self.eventmanager.removeMouseListener(self)

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
