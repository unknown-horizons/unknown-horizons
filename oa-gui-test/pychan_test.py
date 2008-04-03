#!/usr/bin/env python
# coding: utf-8

import sys, os, re

def _jp(path):
	return os.path.sep.join(path.split('/'))

_paths = ('../../fife/engine/swigwrappers/python', '../../fife/engine/extensions')
for p in _paths:
	if p not in sys.path:
		sys.path.append(_jp(p))

import fife
import fifelog
import basicapplication
import pychan

class PyChanExample(object):
	def __init__(self,xmlFile):
		self.xmlFile = xmlFile
		self.widget = None
	
	def start(self):
		self.widget = pychan.loadXML(self.xmlFile)
		eventMap = {
			'closeButton':self.stop,
			'okButton'   :self.stop,
			'button'     :self.stop
		}
		self.widget.mapEvents(eventMap, ignoreMissing = True)
		self.widget.show()

	def stop(self):
		if self.widget:
			self.widget.hide()
		self.widget = None

class DemoApplication(basicapplication.ApplicationBase):
	def __init__(self):
		super(DemoApplication,self).__init__()
		
		pychan.init(self.engine,debug=True)
		pychan.setupModalExecution(self.mainLoop,self.breakFromMainLoop)
		
		self.gui = pychan.loadXML('content/gui/gui.xml')
		
		eventMap = {
			'settingsLink' : self.showSettings,
			'creditsLink'  : self.showCredits,
			'closeButton'  : self.quit,
		}
		self.gui.mapEvents(eventMap)
		self.gui.show()
		
		self.currentExample = None
		self.creditsWidget = None

	def showCredits(self):
		print pychan.loadXML('content/gui/credits.xml').execute({ 'okButton' : "Yay!" })

	def showSettings(self):
		print pychan.loadXML('content/gui/settings.xml').execute({ 'okButton' : "Yay!" })

if __name__ == '__main__':
	import sys
	if len(sys.argv) == 2:
		app = TestXMLApplication(sys.argv[1])
	else:
		app = DemoApplication()
	app.run()
