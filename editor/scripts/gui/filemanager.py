# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
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

import os, math, traceback, sys
from fife import fife
from fife.extensions import pychan
from fife.extensions import filebrowser
from fife.extensions import loaders, savers
from fife.extensions.serializers.xmlobject import XMLObjectLoader
from fife.extensions.serializers.xml_loader_tools import loadImportFile, loadImportDir, loadImportDirRec
import action
import scripts.editor
import fife.extensions.pychan.widgets as widgets
from fife.extensions.pychan.tools import callbackWithArguments as cbwa
from scripts.gui.error import ErrorDialog
from action import Action, ActionGroup
from input import InputDialog
from selection import SelectionDialog, ClickSelectionDialog
from scripts.events import events
from scripts.gui.cameradialog import CameraDialog
from scripts.gui.layerdialog import LayerDialog

class FileManager(object):
	def __init__(self):
		from fife import fife
		self.editor = scripts.editor.getEditor()
		self.engine = self.editor.getEngine()
		self._map = None
		self._layer = None
		self._mapdlg = None
		self._layerdlg = None
		self._cameradlg = None
		
		self._filebrowser = None
		self._importbrowser = None
		self._savebrowser = None

		self.obj_loader = XMLObjectLoader(
			self.engine.getImagePool(),
			self.engine.getAnimationPool(),
			self.engine.getModel(),
			self.engine.getVFS()
		)		

		newAction = Action(u"New map", "gui/icons/new_map.png")
		loadAction = Action(u"Open", "gui/icons/load_map.png")
		closeAction = Action(u"Close", "gui/icons/close_map.png")
		saveAction = Action(u"Save", "gui/icons/save_map.png")
		saveAsAction = Action(u"Save as", "gui/icons/save_mapas.png")
		saveAllAction = Action(u"Save all", "gui/icons/save_allmaps.png")
		importFileAction = Action(u"Import file", "gui/icons/import_file.png")
		importDirAction = Action(u"Import directory", "gui/icons/import_dir.png")
		
		newAction.helptext = u"Create new map"
		loadAction.helptext = u"Open existing map"
		closeAction.helptext = u"Close map"
		saveAction.helptext = u"Save map"
		saveAsAction.helptext = u"Save map as"
		saveAllAction.helptext = u"Save all opened maps"
		importFileAction.helptext = u"Imports an object file"
		importDirAction.helptext = u"Recursively imports all objects from a directory"
		
		action.activated.connect(self.showMapWizard, sender=newAction)
		action.activated.connect(self.showLoadDialog, sender=loadAction)
		action.activated.connect(self.closeCurrentMap, sender=closeAction)
		action.activated.connect(self.save, sender=saveAction)
		action.activated.connect(self.saveAs, sender=saveAsAction)
		action.activated.connect(self.editor.saveAll, sender=saveAllAction)
		
		self._importFileCallback = cbwa(self.showImportDialog, self.importFile, False)
		self._importDirCallback = cbwa(self.showImportDialog, self.importDir, True)
		action.activated.connect(self._importFileCallback, sender=importFileAction)
		action.activated.connect(self._importDirCallback, sender=importDirAction)
		
		eventlistener = self.editor.getEventListener()
		
		eventlistener.getKeySequenceSignal(fife.Key.N, ["ctrl"]).connect(self.showMapWizard)
		eventlistener.getKeySequenceSignal(fife.Key.O, ["ctrl"]).connect(self.showLoadDialog)
		eventlistener.getKeySequenceSignal(fife.Key.W, ["ctrl"]).connect(self.closeCurrentMap)
		eventlistener.getKeySequenceSignal(fife.Key.S, ["ctrl"]).connect(self.save)
		eventlistener.getKeySequenceSignal(fife.Key.S, ["ctrl", "shift"]).connect(self.editor.saveAll)
		
		fileGroup = ActionGroup()
		fileGroup.addAction(newAction)
		fileGroup.addAction(loadAction)
		fileGroup.addSeparator()
		fileGroup.addAction(closeAction)
		fileGroup.addSeparator()
		fileGroup.addAction(saveAction)
		fileGroup.addAction(saveAsAction)
		fileGroup.addAction(saveAllAction)
		fileGroup.addSeparator()
		fileGroup.addAction(importFileAction)
		fileGroup.addAction(importDirAction)
		
		self.editor.getToolBar().insertAction(fileGroup, 0)
		self.editor.getToolBar().insertSeparator(None, 1)
		self.editor._file_menu.insertAction(fileGroup, 0)
		self.editor._file_menu.insertSeparator(None, 1)
		
	def closeCurrentMap(self):
		mapview = self.editor.getActiveMapView()
		if mapview is None:
			print "No map to close"
			return
			
		mapview.close()

	def showLoadDialog(self):
		if self._filebrowser is None:
			self._filebrowser = filebrowser.FileBrowser(self.engine, self.loadFile, extensions = loaders.fileExtensions)
		self._filebrowser.showBrowser()
		
	def showSaveDialog(self):
		if self._savebrowser is None:
			self._savebrowser = filebrowser.FileBrowser(self.engine, self.saveFile, savefile=True, extensions = loaders.fileExtensions)
		self._savebrowser.showBrowser()
		
	def showImportDialog(self, callback, selectdir):
		if self._importbrowser is None:
			self._importbrowser = filebrowser.FileBrowser(self.engine, callback, extensions = loaders.fileExtensions)
		self._importbrowser.fileSelected = callback
		self._importbrowser.selectdir = selectdir
		self._importbrowser.showBrowser()

	def saveFile(self, path, filename):
		mapview = self.editor.getActiveMapView()
		if mapview is None:
			print "No map is open"
			return
			
		fname = '/'.join([path, filename])
		mapview.saveAs(fname)
		
	def saveAs(self):
		mapview = self.editor.getActiveMapView()
		if mapview is None:
			print "No map is open"
			return
		self.showSaveDialog()
		
	def loadFile(self, path, filename):
		self.editor.openFile('/'.join([path, filename]))
		
	def showMapWizard(self):
		if self._cameradlg:
			self._cameradlg._widget.show()
		elif self._layerdlg:
			self._layerdlg._widget.show()
		elif self._mapdlg:
			self._mapdlg._widget.show()
		else:
			self._newMap()

	def _newMap(self):
		self._mapdlg = InputDialog(u'Enter a map name:', self._newLayer, self._clean)
		
	def _newLayer(self, mapId):
		if mapId == '':
			print "Please enter a map ID"
			return self._newMap()
			
		self._map = self.engine.getModel().createMap(str(mapId))
		self._layerdlg = LayerDialog(self.engine, self._map, self._newCamera, self._clean)
		
	def _newCamera(self, layer):
		self._layer = layer
		
		self._cameradlg = CameraDialog(self.engine, self._addMap, self._clean, self._map, self._layer)
		
	def _addMap(self):
		self.editor.newMapView(self._map)
		self._clean()
		
	def _clean(self):
		self._mapdlg = None
		self._layerdlg = None
		self._cameradlg = None
		self._map = None
		self._layer = None

	def save(self):
		curname = None
		mapview = self.editor.getActiveMapView()
		if mapview is None:
			print "No map is open"
			return
		
		try:
			curname = mapview.getMap().getResourceLocation().getFilename()
		except RuntimeError:
			self.showSaveDialog()
			return
		
		mapview.save()
		
	def importFile(self, path, filename):
		file = os.path.normpath(os.path.join(path, filename))
		# FIXME: This is necassary for the files to be loaded properly.
		#		 The loader should be fixed to support native (windows)
		#		 path separators.
		file = file.replace('\\', '/') 
		
		try:
			if os.path.isfile(file):
				loadImportFile(self.obj_loader, file, self.engine)
			else:
				raise file+ " is not a file!"
		except:
			traceback.print_exc(sys.exc_info()[1])
			errormsg = u"Importing file failed:\n"
			errormsg += u"File: "+unicode(file)+u"\n"
			errormsg += u"Error: "+unicode(sys.exc_info()[1])
			ErrorDialog(errormsg)
			return None
		
		events.onObjectsImported.send(sender=self)
			
	def importDir(self, path, filename=""):
		if os.path.isdir(os.path.join(path, filename)):
			path = os.path.join(path, filename)
			path = os.path.normpath(path)
		
		# FIXME: This is necassary for the files to be loaded properly.
		#		 The loader should be fixed to support native (windows)
		#		 path separators.
		path = path.replace('\\', '/') 
		
		try:
			if os.path.isdir(path):
				loadImportDirRec(self.obj_loader, path, self.engine)
			else:
				raise file+ " is not a directory!"
		except:
			traceback.print_exc(sys.exc_info()[1])
			errormsg = u"Importing directory failed:\n"
			errormsg += u"File: "+unicode(file)+u"\n"
			errormsg += u"Error: "+unicode(sys.exc_info()[1])
			ErrorDialog(errormsg)
			return None
			
		events.onObjectsImported.send(sender=self)

