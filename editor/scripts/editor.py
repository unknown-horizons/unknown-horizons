# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2010 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

"""
Editor
======

This class serves as 
"""

import sys
import os
import traceback

fife_path = os.path.join('..','..','engine','python')
if os.path.isdir(fife_path) and fife_path not in sys.path:
	sys.path.insert(0,fife_path)

from fife import fife
print "Using the FIFE python module found here: ", os.path.dirname(fife.__file__)

from fife.extensions import loaders
import events
import plugin

from fife.extensions.basicapplication import ApplicationBase

from fife.extensions import pychan
from fife.extensions.pychan.tools import callbackWithArguments as cbwa

from events import *
from gui import ToolBar, action
from gui.action import Action, ActionGroup
from gui.filemanager import FileManager
from gui.mainwindow import MainWindow
from gui.mapeditor import MapEditor
from gui.menubar import Menu, MenuBar
from gui.error import ErrorDialog
from mapview import MapView
from fife.extensions.fife_settings import Setting

TDS = Setting(app_name="editor")

def getEditor():
	""" Returns the Global editor instance """
	if Editor.editor is None:
		Editor(None)
	return Editor.editor

class Editor(ApplicationBase, MainWindow):
	""" Editor sets up all subsystems and provides access to them """
	editor = None

	def __init__(self, params, *args, **kwargs):
		Editor.editor = self
	
		self._filemanager = None
	
		self._params = params
		self._eventlistener = None
		self._pluginmanager = None
		
		self._inited = False
		
		self._mapview = None
		self._mapviewlist = []
		self._mapgroup = None
		self._mapbar = None
		self._maparea = None
		self._mapeditor = None
		
		self._file_menu = None
		self._edit_menu = None
		self._view_menu = None
		self._tools_menu = None
		self._help_menu = None
		
		self._change_map = -1
		
		self._settings = TDS

		self._lighting_mode = int(TDS.get("FIFE", "Lighting"))		
		self._help_dialog = None
	
		ApplicationBase.__init__(self, TDS, *args, **kwargs)
		MainWindow.__init__(self, *args, **kwargs)
		
	def _initTools(self):
		""" Initializes tools """
		self._pluginmanager = plugin.PluginManager(self.getSettings())
		
		self._filemanager = FileManager()
		self._toolbar.adaptLayout()
		self._mapeditor = MapEditor()
		
	def _initGui(self):
		""" Sets up the GUI """
		screen_width = self.engine.getSettings().getScreenWidth()
		screen_height = self.engine.getSettings().getScreenHeight()
		MainWindow.initGui(self, screen_width, screen_height)

		self._toolbox = ToolBar(title=u"", orientation=1)
		self._toolbox.position_technique = "explicit"
		self._toolbox.position = (150, 150)
		
		self._mapbar = ToolBar(name="MapBar", panel_size=20)
		self._mapbar.setDocked(True)
		
		self._maparea = pychan.widgets.VBox()
		self._maparea.opaque = False
		self._maparea.is_focusable = True
		
		# Capture mouse and key events for EventListener
		cw = self._maparea
		cw.capture(self.__sendMouseEvent, "mouseEntered")
		cw.capture(self.__sendMouseEvent, "mouseExited")
		cw.capture(self.__sendMouseEvent, "mousePressed")
		cw.capture(self.__sendMouseEvent, "mouseReleased")
		cw.capture(self.__sendMouseEvent, "mouseClicked")
		cw.capture(self.__sendMouseEvent, "mouseMoved")
		cw.capture(self.__sendMouseEvent, "mouseWheelMovedUp")
		cw.capture(self.__sendMouseEvent, "mouseWheelMovedDown")
		cw.capture(self.__sendMouseEvent, "mouseDragged")
		cw.capture(self.__sendKeyEvent, "keyPressed")
		cw.capture(self.__sendKeyEvent, "keyReleased")
		
		self._centralwidget.addChild(self._mapbar)
		self._centralwidget.addChild(self._maparea)
		
		self._initActions()
		
		self._toolbox.show()
		
		events.preMapClosed.connect(self._mapRemoved)

	def _initActions(self):
		""" Initializes toolbar and menubar buttons """
		exitAction = Action(u"Exit", "gui/icons/quit.png")
		exitAction.helptext = u"Exit program"
		action.activated.connect(self.quit, sender=exitAction)
		
		self._file_menu = Menu(name=u"File")
		self._file_menu.addAction(exitAction)
		
		self._edit_menu = Menu(name=u"Edit")
		self._view_menu = Menu(name=u"View")
		self._tools_menu = Menu(name=u"Tools")
		self._window_menu = Menu(name=u"Window")
		self._help_menu = Menu(name=u"Help")
		
		self._action_show_statusbar = Action(u"Statusbar")
		self._action_show_statusbar.helptext = u"Toggle statusbar"
		action.activated.connect(self.toggleStatusbar, sender=self._action_show_statusbar)
		
		self._action_show_toolbar = Action(u"Toolbar")
		self._action_show_toolbar.helptext = u"Toggle toolbar"
		action.activated.connect(self.toggleToolbar, sender=self._action_show_toolbar)
		
		self._action_show_toolbox = Action(u"Tool box")
		self._action_show_toolbox.helptext = u"Toggle tool box"
		action.activated.connect(self.toggleToolbox, sender=self._action_show_toolbox)
		
		self._view_menu.addAction(self._action_show_statusbar)
		self._view_menu.addAction(self._action_show_toolbar)
		self._view_menu.addAction(self._action_show_toolbox)
		self._view_menu.addSeparator()
	
	
		test_action1 = Action(u"Cycle buttonstyles", "gui/icons/cycle_styles.png")
		test_action1.helptext = u"Cycles button styles. There are currently four button styles."
		action.activated.connect(self._actionActivated, sender=test_action1)
		self._view_menu.addAction(test_action1)

		test_action2 = Action(u"Toggle Blocking")
		test_action2.helptext = u"Toggles the blocking infos for the instances."
		action.activated.connect(self.toggleBlocking, sender=test_action2)
		self._view_menu.addAction(test_action2)

		test_action3 = Action(u"Toggle Grid")
		test_action3.helptext = u"Toggles the grids of the map."
		action.activated.connect(self.toggleGrid, sender=test_action3)
		self._view_menu.addAction(test_action3)

		test_action4 = Action(u"Toggle Coordinates")
		test_action4.helptext = u"Toggles the coordinates of the map."
		action.activated.connect(self.toggleCoordinates, sender=test_action4)
		self._view_menu.addAction(test_action4)		
		
		self._mapgroup = ActionGroup(exclusive=True, name="Mapgroup")
		self._mapbar.addAction(self._mapgroup)
		self._window_menu.addAction(self._mapgroup)
		
		help_action = Action(u"Help", "gui/icons/help.png")
		help_action.helptext = u"Displays a window with some simple instructions"
		action.activated.connect(self._showHelpDialog, sender=help_action)
		self._help_menu.addAction(help_action)
		
		self._menubar.addMenu(self._file_menu)
		self._menubar.addMenu(self._edit_menu)
		self._menubar.addMenu(self._view_menu)
		self._menubar.addMenu(self._tools_menu)
		self._menubar.addMenu(self._window_menu)
		self._menubar.addMenu(self._help_menu)
	
	def _actionActivated(self, sender):
		self._toolbar.button_style += 1
		
	def _showHelpDialog(self, sender):
		""" Shows the help dialog """
		if self._help_dialog is not None:
			self._help_dialog.show()
			return
		
		self._help_dialog = pychan.loadXML("gui/help.xml")
		self._help_dialog.findChild(name="closeButton").capture(self._help_dialog.hide)
		
		f = open('lang/infotext.txt', 'r')
		self._help_dialog.findChild(name="helpText").text = unicode(f.read())
		f.close()
		
		self._help_dialog.show()
		
	def toggleStatusbar(self):
		""" Toggles status bar """
		statusbar = self.getStatusBar()
		if statusbar.max_size[1] > 0:
			statusbar.min_size=(statusbar.min_size[0], 0)
			statusbar.max_size=(statusbar.max_size[0], 0)
			self._action_show_statusbar.setChecked(False)
		else:
			statusbar.min_size=(statusbar.min_size[0], statusbar.min_size[0])
			statusbar.max_size=(statusbar.max_size[0], statusbar.max_size[0])
			self._action_show_statusbar.setChecked(True)
		statusbar.adaptLayout()
			
	def toggleToolbar(self):
		""" Toggles toolbar """
		toolbar = self.getToolBar()
		if toolbar.isVisible():
			toolbar.setDocked(False)
			toolbar.hide()
			self._action_show_toolbar.setChecked(False)
		else: 
			tx = toolbar.x
			ty = toolbar.y
			toolbar.show()
			toolbar.x = tx
			toolbar.y = ty
			self._action_show_toolbar.setChecked(True)
			
	def toggleToolbox(self):
		""" Toggles tool box """
		toolbox = self.getToolbox()
		if toolbox.isVisible():
			toolbox.setDocked(False)
			toolbox.hide()
			self._action_show_toolbox.setChecked(False)
		else:
			tx = toolbox.x
			ty = toolbox.y
			toolbox.show()
			toolbox.x = tx
			toolbox.y = ty
			self._action_show_toolbox.setChecked(True)
		toolbox.adaptLayout()

	def toggleBlocking(self, sender):
		if self._mapview is not None:
			for cam in self._mapview.getMap().getCameras():			
				r = fife.BlockingInfoRenderer.getInstance(cam)
				r.setEnabled(not r.isEnabled())

	def toggleGrid(self, sender):
		if self._mapview is not None:
			for cam in self._mapview.getMap().getCameras():			
				r = fife.GridRenderer.getInstance(cam)
				r.setEnabled(not r.isEnabled())

	def toggleCoordinates(self, sender):
		if self._mapview is not None:
			for cam in self._mapview.getMap().getCameras():
				r = fife.CoordinateRenderer.getInstance(cam)
				if not r.isEnabled():
					r.clearActiveLayers()
					color = str(self._settings.get("Colors", "Coordinate", "255,255,255"))
					r.setColor(*[int(c) for c in color.split(',')])
					for layer in self._mapview.getMap().getLayers():
						if layer.areInstancesVisible():
							r.addActiveLayer(layer)
					r.setEnabled(True)
				else:
					r.setEnabled(False)

	def getToolbox(self): 
		return self._toolbox
	
	def getPluginManager(self): 
		return self._pluginmanager
		
	def getEngine(self): 
		return self.engine

	def getMapViews(self):
		return self._mapviewlist
		
	def getActiveMapView(self):
		return self._mapview
		
	def getSettings(self):
		return self._settings;

	def getObject(self):
		return self._mapeditor.getObject()

	def showMapView(self, mapview):
		""" Switches to mapview. """
		if mapview is None or mapview == self._mapview:
			return
			
		if self._mapview != None and mapview != self._mapview:
			# need to disable the cameras from the previous map
			# if it exists before switching
			if self._mapview.getMap() != None:
				for cam in self._mapview.getMap().getCameras():
					cam.setEnabled(False)
		
		# if light model is set then enable LightRenderer for all layers
		if self._lighting_mode is not 0:
			for cam in mapview.getMap().getCameras():
				renderer = fife.LightRenderer.getInstance(cam)
				renderer.activateAllLayers(mapview.getMap())
				renderer.setEnabled(not renderer.isEnabled())
		
		events.preMapShown.send(sender=self, mapview=mapview)
		self._mapview = mapview
		self._mapview.show()
		events.postMapShown.send(sender=self, mapview=mapview)

	def createListener(self):
		""" Creates the event listener. This is called by ApplicationBase """
		if self._eventlistener is None:
			self._eventlistener = EventListener(self.engine)
		
		return self._eventlistener
		
	def getEventListener(self):
		""" Returns the event listener """
		return self._eventlistener
	
	def newMapView(self, map):
		""" Creates a new map view """
		mapview = MapView(map)
		
		self._mapviewlist.append(mapview)
		
		map_action = Action(unicode(map.getId()))
		action.activated.connect(cbwa(self.showMapView, mapview), sender=map_action, weak=False)
		self._mapgroup.addAction(map_action)
		
		self.showMapView(mapview)
		
		events.mapAdded.send(sender=self, map=map)
		
		return mapview
		
	def _mapRemoved(self, mapview):
		index = self._mapviewlist.index(mapview)-1
		
		for cam in mapview.getMap().getCameras():
			cam.setEnabled(False)
			
		self._mapviewlist.remove(mapview)
		
		# Remove tab
		for map_action in self._mapgroup.getActions():
			if map_action.text == unicode(mapview.getMap().getId()):
				self._mapgroup.removeAction(map_action)
				break
				
		# Change mapview
		if len(self._mapviewlist) > 0:
			if index < 0: 
				index = 0
			self._change_map = index
		else:
			self._mapview = None

	def openFile(self, path):
		""" Opens a file """
		try:
			if self._lighting_mode == 0:
				map = loaders.loadMapFile(path, self.engine)
			else:
				map = loaders.loadMapFile(path, self.engine, extensions = {'lights': True})
			return self.newMapView(map)
		except:
			traceback.print_exc(sys.exc_info()[1])
			errormsg = u"Opening map failed:\n"
			errormsg += u"File: "+unicode(path, sys.getfilesystemencoding())+u"\n"
			errormsg += u"Error: "+unicode(sys.exc_info()[1])
			ErrorDialog(errormsg)
			return None
	
	def saveAll(self):
		""" Saves all open maps """
		tmpview = self._mapview
		for mapview in self._mapviewlist:
			self._mapview = mapview
			self._filemanager.save()
		self._mapview = tmpview
		
	def quit(self):
		""" Quits the editor. An onQuit signal is sent before the application closes """
		events.onQuit.send(sender=self)
		
		self._settings.saveSettings()
		ApplicationBase.quit(self)

	def _pump(self):
		""" Called once per frame """
		# ApplicationBase and Engine should be done initializing at this point
		if self._inited == False:
			self._initGui()
			self._initTools()
			if self._params: self.openFile(self._params)
			self._inited = True
			
		# FIXME: This isn't very nice, but it is needed to change the map
		#		 outside the callback.
		if self._change_map >= 0 and len(self._mapviewlist) > 0:
			if self._change_map >= len(self._mapviewlist):
				self._change_map = len(self._mapviewlist)-1
			mapview = self._mapviewlist[self._change_map]
			
			self.showMapView(mapview)
			self._change_map = -1
		
		events.onPump.send(sender=self)
		
	def __sendMouseEvent(self, event, **kwargs):
		""" Function used to capture mouse events for EventListener """
		ms_event = fife.MouseEvent
		type = event.getType()
		
		if type == ms_event.MOVED:
			mouseMoved.send(sender=self._maparea, event=event)
			
		elif type == ms_event.PRESSED:
			mousePressed.send(sender=self._maparea, event=event)
			
		elif type == ms_event.RELEASED:
			mouseReleased.send(sender=self._maparea, event=event)
			
		elif type == ms_event.WHEEL_MOVED_DOWN:
			mouseWheelMovedDown.send(sender=self._maparea, event=event)
			
		elif type == ms_event.WHEEL_MOVED_UP:
			mouseWheelMovedUp.send(sender=self._maparea, event=event)
			
		elif type == ms_event.CLICKED:
			mouseClicked.send(sender=self._maparea, event=event)
			
		elif type == ms_event.ENTERED:
			mouseEntered.send(sender=self._maparea, event=event)
			
		elif type == ms_event.EXITED:
			mouseExited.send(sender=self._maparea, event=event)
			
		elif type == ms_event.DRAGGED:
			mouseDragged.send(sender=self._maparea, event=event)
		
	def __sendKeyEvent(self, event, **kwargs):
		""" Function used to capture key events for EventListener """
		type = event.getType()
		
		if type == fife.KeyEvent.PRESSED:
			keyPressed.send(sender=self._maparea, event=event)
		
		elif type == fife.KeyEvent.RELEASED:
			keyReleased.send(sender=self._maparea, event=event)
			
		

		
