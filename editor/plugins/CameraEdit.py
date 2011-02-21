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

""" a tool for FIFEdit to edit camera attributes.  It does not
currently support multiple cameras.
"""

from fife import fife
from fife.extensions import pychan
import fife.extensions.pychan.widgets as widgets
from fife.extensions.pychan.tools import callbackWithArguments as cbwa

from fife.extensions.fife_timer import Timer

import scripts
import scripts.plugin as plugin
from scripts.events import *
from scripts.gui.action import Action


import os
try:
	import xml.etree.cElementTree as ET
except:
	import xml.etree.ElementTree as ET

import math


class CameraEdit(plugin.Plugin):

	def __init__(self):
		self._enabled = False
		
		# Camera instance
		self._camera = None
		
		# Editor instance
		self._editor = None
		
		# Toolbar button to display Camera Editor
		self._action_show = None
		
		# GUI
		self._container = None
		self._ok_button = None
		self._cancel_button = None

	def enable(self):
		""" plugin method """
		if self._enabled is True:
			return
		
		self._editor = scripts.editor.getEditor()
		#self._camera = self._editor.getActiveMapView().getCamera()
		self._action_show = Action(u"Camera Editor", checkable=True)
		scripts.gui.action.activated.connect(self.toggle, sender=self._action_show)
		self._editor._tools_menu.addAction(self._action_show)
		
		self._createGui()
		
		self._enabled = True

	def disable(self):
		""" plugin method """
		if self._enabled is False:
			return
			
		self._container.setDocked(False)
		self._container.hide()
		
		self._editor._tools_menu.removeAction(self._action_show)
		
		self._enabled = False
			

	def isEnabled(self):
		""" plugin method """
		return self._enabled;

	def getName(self):
		""" plugin method """
		return "Camera Editor"
		
	def toggle(self):
		"""	Toggles the cameratool visible / invisible and sets
			dock status 
		"""
		if self._container.isVisible() or self._container.isDocked():
			self._container.setDocked(False)
			self._container.hide()

			self._action_show.setChecked(False)
		else:
			self._container.show()
			self.loadSettings()
			self._action_show.setChecked(True)
			self._adjustPosition()
	
	def saveSettings(self):
		engine = self._editor.getEngine()
	
		id = self._container.collectData('idBox')
		if id == '':
			print 'Please enter a camera id.'
			return
	
		try:
			map = engine.getModel().getMap(str(self._container.collectData('mapBox')))
		except fife.Exception:
			print 'Cannot find the specified map id.'
			return
	
		try:
			layer = map.getLayer(str(self._container.collectData('layerBox')))
		except fife.Exception:
			print 'Cannot find the specified layer id.'	
			return
	
		try:
			vals = self._container.collectData('viewBox').split(',')
			if len(vals) != 4:
				raise ValueError	
	
			viewport = fife.Rect(*[int(c) for c in vals])
		except ValueError:
			print 'Please enter 4 comma (,) delimited values for viewport x,y,width,height.'
			return
	
		try:
			refh = int(self._container.collectData('refhBox'))
			refw = int(self._container.collectData('refwBox'))
		except ValueError:
			print 'Please enter positive integer values for reference width and height.'
			return
	
		try:
			rot = int(self._container.collectData('rotBox'))
			tilt = int(self._container.collectData('tiltBox'))
		except ValueError:
			print 'Please enter positive integer values for rotation and tilt.'
			return
	
		self._camera = self._editor.getActiveMapView().getCamera()
		self._camera.setId(str(id))
		self._camera.getLocation().setLayer(layer)
		self._camera.setViewPort(viewport)
		self._camera.setCellImageDimensions(refw, refh)
		self._camera.setRotation(rot)
		self._camera.setTilt(tilt)
		
		self.toggle()

	def loadSettings(self):
		if self._editor.getActiveMapView() is None:
			return
		else:
			self._camera = self._editor.getActiveMapView().getCamera()
			
			map = self._editor.getActiveMapView().getMap().getId()
			self._container.findChild(name="mapBox").text = unicode(str(map))
			
			layer = self._camera.getLocation().getLayer().getId()
			self._container.findChild(name="layerBox").text = unicode(layer)
			
			vp = self._camera.getViewPort()
			viewport_str = unicode(str(vp.x) + "," + str(vp.y) + "," + str(vp.w) + "," + str(vp.h))
			self._container.findChild(name="viewBox").text = viewport_str
			
			ref = self._camera.getCellImageDimensions()
			refw_str = unicode(str(ref.x))
			refh_str = unicode(str(ref.y))
			self._container.findChild(name="refhBox").text = refh_str
			self._container.findChild(name="refwBox").text = refw_str
			
			self._container.findChild(name="idBox").text = unicode(str(self._camera.getId()))
			self._container.findChild(name="rotBox").text = unicode(str(int(self._camera.getRotation())))
			self._container.findChild(name="tiltBox").text = unicode(str(int(self._camera.getTilt())))

	def _createGui(self):
		""" Create the basic gui container """
		self._container =  pychan.loadXML('gui/cameradialog.xml')
		
		self._ok_button = self._container.findChild(name="okButton")
		self._cancel_button = self._container.findChild(name="cancelButton")
		
		self._ok_button.capture(self.saveSettings)
		self._ok_button.capture(cbwa(self._editor.getStatusBar().showTooltip, unicode("Save changes to the camera")), 'mouseEntered')
		self._ok_button.capture(self._editor.getStatusBar().hideTooltip, 'mouseExited')

		self._cancel_button.capture(self.toggle)
		self._cancel_button.capture(cbwa(self._editor.getStatusBar().showTooltip, unicode("Discard any changes to the camera")), 'mouseEntered')
		self._cancel_button.capture(self._editor.getStatusBar().hideTooltip, 'mouseExited')

		
	def _adjustPosition(self):
		"""	Adjusts the position of the container - we don't want to
		let the window appear at the center of the screen.
		(new default position: left, beneath the tools window)
		"""
		self._container.position = (50, 200)
		
		

