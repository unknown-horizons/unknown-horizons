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

from fife import fife
import editor
from fife.extensions import loaders, savers
from events import events
from mapcontroller import MapController

class MapView:
	""" MapView represents a map in the editor. 
	
	It handles opening, saving and closing of a map,
	as well as displaying it on screen.
	"""
	def __init__(self, map):
		self._map = map
		self._editor = editor.getEditor()
		self._controller = MapController(self._map)
		self._camera = None
		
		if map is None:
			raise AttributeError("No map passed to MapView!")
		
		if not self._map.getLayers():
			raise AttributeError('Editor error: map ' + self._map.getId() + ' has no layers. Cannot edit.')

		map.addChangeListener(self._editor.getEventListener().mapchangelistener)
		for layer in map.getLayers():
			layer.addChangeListener(self._editor.getEventListener().layerchangelistener)
			
		events.onLayerCreate.connect(self._layerCreated)

		self.importlist = []
		if hasattr(map, "importDirs"):
			self.importlist.extend(map.importDirs)
			
	def _cleanUp(self):
		events.onLayerCreate.disconnect(self._layerCreated)
		
		if self._map:
			for layer in self._map.getLayers():
				layer.removeChangeListener(self._editor.getEventListener().layerchangelistener)
		
		self.importlist = []
		self._map = None
		self._editor = None
		self._controller = None
		self._camera = None
			
	def _layerCreated(self, map, layer):
		if map.getId() == self._map.getId():
			layer.addChangeListener(self._editor.getEventListener().layerchangelistener)
		
	# Copied from mapeditor.py
	def show(self):
		""" Sets up the camera to display the map. Size of the camera is equal to the
		screen size """
		_camera = None
		
		engine = self._editor.getEngine()
		
		for cam in self._map.getCameras():
			cam.resetRenderers()
			cam.setEnabled(False)

		for cam in self._map.getCameras():
			if cam.getLocationRef().getMap().getId() == self._map.getId():
				rb = engine.getRenderBackend()
				cam.setViewPort(fife.Rect(0, 0, rb.getScreenWidth(), rb.getScreenHeight()))
				cam.setEnabled(True)
				self._camera = cam
				break
		else:
			raise AttributeError('No cameras found associated with this map: ' + self._map.getId())

	def getCamera(self):
		return self._camera
		
	def setCamera(self, camera):
		if not camera:
			print "Camera can not be None"
			return
		
		if camera.getLocation().getLayer().getMap() != self._map:
			print "Camera is not associated with this map"
			return
			
		self._camera = camera
	
	def getController(self):
		return self._controller
		
	def getMap(self):
		return self._map
		
	def save(self):
		""" Saves the map using the previous filename.
		
		Emits preSave and postSave signals.
		"""
		curname = ""
		try:
			curname = self._map.getResourceLocation().getFilename()
		except RuntimeError:
			print "Map has no filename yet, can't save."
			return

		events.preSave.send(sender=self, mapview=self)
		savers.saveMapFile(curname, self._editor.getEngine(), self._map, importList=self.importlist)
		events.postSave.send(sender=self, mapview=self)
		
	def saveAs(self, filename):
		""" Saves the map using a specified filename.
		
		Emits preSave and postSave signals.
		"""
		events.preSave.send(sender=self, mapview=self)
		savers.saveMapFile(str(filename), self._editor.getEngine(), self._map, importList=self.importlist)
		events.postSave.send(sender=self, mapview=self)
		
	def close(self):
		""" Closes the mapview """
		events.preMapClosed.send(sender=self, mapview=self)
		
		self._controller.cleanUp()
				
		for cam in self._map.getCameras():
			cam.resetRenderers()
		
		# Unload the map from FIFE
		self._editor.getEngine().getModel().deleteMap(self._map)
		self._map = None
		self._cleanUp()
		
		events.postMapClosed.send(sender=self, mapview=self)
	
