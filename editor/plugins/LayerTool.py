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

""" A layer tool for FIFedit """

from fife import fife
from fife.extensions import pychan
import fife.extensions.pychan.widgets as widgets
from fife.extensions.pychan.tools import callbackWithArguments as cbwa

import scripts.plugin as plugin
import scripts.editor
from scripts.events import *
from scripts.gui.action import Action
from scripts.gui.layerdialog import LayerDialog

class LayerTool(plugin.Plugin):
	""" The B{LayerTool} allows to select and show / hide layers of a loaded
		map as well as creating new layers or edit layer properties
	"""
	
	# default should be pychan default, highlight can be choosen (format: r,g,b)
	DEFAULT_BACKGROUND_COLOR = pychan.internal.DEFAULT_STYLE['default']['base_color']
	HIGHLIGHT_BACKGROUND_COLOR = pychan.internal.DEFAULT_STYLE['default']['selection_color']

	# the dynamicly created widgets have the name scheme prefix + layerid
	LABEL_NAME_PREFIX = "select_"

	def __init__(self):	
		# Editor instance
		self._editor = None
		
		# Plugin variables
		self._enabled = False
		
		# Current mapview
		self._mapview = None
		
		# Toolbar button to display LayerTool
		self._action_show = None
		
		# GUI
		self._layer_wizard = None
		self._container = None
		self._wrapper = None
		self._remove_layer_button = None
		self._create_layer_button = None
		self._edit_layer_button = None
			
	#--- Plugin functions ---#
	def enable(self):
		""" Enable plugin """
		if self._enabled is True:
			return
			
		# Fifedit plugin data
		self._editor = scripts.editor.getEditor()
		self._action_show = Action(u"LayerTool", checkable=True)
		scripts.gui.action.activated.connect(self.toggle, sender=self._action_show)
		self._editor._tools_menu.addAction(self._action_show)

		self._createGui()
		
		self.toggle()
		
		events.postMapShown.connect(self.update)
		events.preMapClosed.connect(self._mapClosed)

	def disable(self):
		""" Disable plugin """
		if self._enabled is False:
			return
		self._container.setDocked(False)
		self._container.hide()
		
		events.postMapShown.disconnect(self.update)
		events.preMapClosed.disconnect(self._mapClosed)
		
		self._editor._tools_menu.removeAction(self._action_show)

	def isEnabled(self):
		""" Returns True if plugin is enabled """
		return self._enabled;

	def getName(self):
		""" Return plugin name """
		return u"Layertool"
	
	#--- End plugin functions ---#
	def _mapClosed(self):
		self.update(mapview=None)
		
	
	def showLayerWizard(self):
		""" Show layer wizard """
		if not self._mapview: return
		
		if self._layer_wizard: self._layer_wizard._widget.hide()
		self._layer_wizard = LayerDialog(self._editor.getEngine(), self._mapview.getMap(), callback=self._layerCreated)
		
	def showEditDialog(self):
		""" Show layerdialog for active layer """
		if not self._mapview: return
		layer = self.getActiveLayer()
		if not layer: return
		
		if self._layer_wizard: self._layer_wizard._widget.hide()
		self._layer_wizard = LayerDialog(self._editor.getEngine(), self._mapview.getMap(), layer=layer, callback=cbwa(self.update, self._mapview))
		
	def clear(self):
		""" Remove all subwrappers """
		self._wrapper.removeAllChildren()
		
	def update(self, mapview):
		""" Update layertool with information from mapview
		
		We group one ToggleButton and one Label into a HBox, the main wrapper
		itself is a VBox and we also capture both the Button and the Label to listen
		for mouse actions
		
		@type	event:	object
		@param	event:	pychan mouse event
		"""
		layers = []
		self._mapview = mapview
		if self._mapview is not None:
			layers = self._mapview.getMap().getLayers()
		
		self.clear()
		
		if len(layers) <= 0:
			if not self._mapview:
				layerid = "No map is open"
			else:
				layerid = "No layers"
			subwrapper = pychan.widgets.HBox()

			layerLabel = pychan.widgets.Label()
			layerLabel.text = unicode(layerid)
			layerLabel.name = LayerTool.LABEL_NAME_PREFIX + layerid
			subwrapper.addChild(layerLabel)
			
			self._wrapper.addChild(subwrapper)
		
		active_layer = self.getActiveLayer()
		if active_layer:
			active_layer = active_layer.getId()
		for layer in reversed(layers):
			layerid = layer.getId()
			subwrapper = pychan.widgets.HBox()

			toggleVisibleButton = pychan.widgets.ToggleButton(hexpand=0, up_image="gui/icons/is_visible.png", down_image="gui/icons/is_visible.png", hover_image="gui/icons/is_visible.png")
			toggleVisibleButton.name = "toggle_" + layerid
			if layer.areInstancesVisible():
				toggleVisibleButton.toggled = True
			toggleVisibleButton.capture(self.toggleLayerVisibility)
			
			layerLabel = pychan.widgets.Label()
			layerLabel.text = unicode(layerid)
			layerLabel.name = LayerTool.LABEL_NAME_PREFIX + layerid
			layerLabel.capture(self.selectLayer,"mousePressed")
			
			if active_layer == layerid:
				layerLabel.background_color	= LayerTool.HIGHLIGHT_BACKGROUND_COLOR
				layerLabel.foreground_color	= LayerTool.HIGHLIGHT_BACKGROUND_COLOR
				layerLabel.base_color		= LayerTool.HIGHLIGHT_BACKGROUND_COLOR
			
			subwrapper.addChild(toggleVisibleButton)
			subwrapper.addChild(layerLabel)
			
			self._wrapper.addChild(subwrapper)
		
		self._container.adaptLayout()		
			
	def toggleLayerVisibility(self, event, widget):
		""" Callback for ToggleButtons 
		
		Toggle the chosen layer visible / invisible. If the active layer is hidden,
		it will be deselected.
		
		@type	event:	object
		@param	event:	pychan mouse event
		@type	widget:	object
		@param	widget:	the pychan widget where the event occurs, transports the layer id in it's name
		"""

		layerid = widget.name[len(LayerTool.LABEL_NAME_PREFIX):]
		
		layer = self._mapview.getMap().getLayer(layerid)
		active_layer = self.getActiveLayer()
		if active_layer:
			active_layer = active_layer.getId()
		
		if layer.areInstancesVisible():
			layer.setInstancesVisible(False)
		else:
			layer.setInstancesVisible(True)
			
		if active_layer == layerid:
			self.resetSelection()
			
	def getActiveLayer(self):
		""" Returns the active layer """
		if self._mapview:
			return self._mapview.getController()._layer
		
	def selectLayer(self, event, widget=None, layerid=None):
		""" Callback for Labels 
		
		We hand the layerid over to the mapeditor module to select a 
		new active layer
		
		Additionally, we mark the active layer widget (changing base color) and reseting the previous one

		@type	event:	object
		@param	event:	pychan mouse event
		@type	widget:	object
		@param	widget:	the pychan widget where the event occurs, transports the layer id in it's name
		@type	layerid: string
		@param	layerid: the layer id
		"""
		
		if not widget and not layerid:
			print "No layer ID or widget passed to LayerTool.selectLayer"
			return
		
		if widget is not None:
			layerid = widget.name[len(LayerTool.LABEL_NAME_PREFIX):]	
		
		self.resetSelection()
		
		widget.background_color = LayerTool.HIGHLIGHT_BACKGROUND_COLOR
		widget.foreground_color = LayerTool.HIGHLIGHT_BACKGROUND_COLOR
		widget.base_color = LayerTool.HIGHLIGHT_BACKGROUND_COLOR
		
		self._mapview.getController().selectLayer(layerid)
		
	def resetSelection(self):
		""" Deselects selected layer """
		previous_active_layer = self.getActiveLayer()
		if previous_active_layer is not None:
			previous_layer_id = previous_active_layer.getId()
			previous_active_widget = self._container.findChild(name=LayerTool.LABEL_NAME_PREFIX + previous_layer_id)
			previous_active_widget.background_color = LayerTool.DEFAULT_BACKGROUND_COLOR
			previous_active_widget.foreground_color = LayerTool.DEFAULT_BACKGROUND_COLOR
			previous_active_widget.base_color = LayerTool.DEFAULT_BACKGROUND_COLOR
			previous_active_widget.text = unicode(previous_layer_id)
			
		self._mapview.getController().selectLayer(None)
		
		
	def removeSelectedLayer(self):
		""" Deletes the selected layer """
		if not self._mapview: return
		
		if self._mapview.getMap().getNumLayers() <= 1:
			print "Can't remove the last layer"
			return
		
		layer = self.getActiveLayer()
		if not layer: return
		
		self.resetSelection()
		
		map = self._mapview.getMap()		
		
		# FIFE will crash if we try to delete the layer which is in use by a camera
		# so we will set the camera to another layer instead
		for cam in map.getCameras:
			if cam.getLocationRef().getMap().getId() != map.getId():
				continue
				
			if cam.getLocation().getLayer().getId() != layer.getId():
				continue
				
			for l in map.getLayers():
				if l.getId() == layer.getId(): 
					continue
				
				cam.getLocationRef().setLayer(l)
				break
		
		map.deleteLayer(layer)
		self.update(self._mapview)

	def toggle(self):
		"""	Toggles the layertool visible / invisible and sets
			dock status 
		"""
		if self._container.isVisible() or self._container.isDocked():
			self._container.setDocked(False)
			self._container.hide()

			self._action_show.setChecked(False)
		else:
			self._container.show()
			self._action_show.setChecked(True)
			self._adjustPosition()
			
	def _createGui(self):
		""" Create the basic gui container """
		self._container =  pychan.loadXML('gui/layertool.xml')
		self._wrapper = self._container.findChild(name="layers_wrapper")
		self._remove_layer_button = self._container.findChild(name="remove_layer_button")
		self._create_layer_button = self._container.findChild(name="add_layer_button")
		self._edit_layer_button = self._container.findChild(name="edit_layer_button")
		
		self._remove_layer_button.capture(self.removeSelectedLayer)
		self._remove_layer_button.capture(cbwa(self._editor.getStatusBar().showTooltip, self._remove_layer_button.helptext), 'mouseEntered')
		self._remove_layer_button.capture(self._editor.getStatusBar().hideTooltip, 'mouseExited')
		
		self._create_layer_button.capture(self.showLayerWizard)
		self._create_layer_button.capture(cbwa(self._editor.getStatusBar().showTooltip, self._create_layer_button.helptext), 'mouseEntered')
		self._create_layer_button.capture(self._editor.getStatusBar().hideTooltip, 'mouseExited')
		
		self._edit_layer_button.capture(self.showEditDialog)
		self._edit_layer_button.capture(cbwa(self._editor.getStatusBar().showTooltip, self._edit_layer_button.helptext), 'mouseEntered')
		self._edit_layer_button.capture(self._editor.getStatusBar().hideTooltip, 'mouseExited')
		
		self.update(None)

	def _adjustPosition(self):
		"""	Adjusts the position of the container - we don't want to
		let the window appear at the center of the screen.
		(new default position: left, beneath the tools window)
		"""
		self._container.position = (50, 200)

	def _layerCreated(self, layer):
		self.update(self._mapview)
		self.selectLayer(None, self._wrapper.findChild(name=LayerTool.LABEL_NAME_PREFIX + layer.getId()))
		


