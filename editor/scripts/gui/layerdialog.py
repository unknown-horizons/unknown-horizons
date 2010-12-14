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
from fife.extensions import pychan
from fife.extensions.pychan import dialogs

class LayerDialog(object):
	""" 
	The B{LayerDialog} provides a gui dialog for creating and editing layers.
	
		FIXME:
			- gridtypes can only be square for now
			- pathing strategy 
    """
	def __init__(self, engine, map, callback=None, onCancel=None, layer=None):
		self.engine = engine
		self.model = engine.getModel()
		self.map = map
		self.layer = layer
		self.callback = callback
		self.onCancel = onCancel
		self._widget = pychan.loadXML('gui/layerdialog.xml')

		# TODO: Add access method for adopted grid types?
		self._widget.findChild(name="gridBox").items = ['square', 'hexagonal']
		
		# TODO: Ditto for pather?
		self._widget.findChild(name="pathingBox").items = ['cell_edges_only', 'cell_edges_and_diagonals', 'freeform']

		if layer:
			cg = layer.getCellGrid()
			cgtype = 0
			if cg.getType() == 'hexagonal':
				cgtype = 1
			
			self._widget.distributeData({
				"layerBox" : unicode(layer.getId()),
				"xScaleBox" : unicode(cg.getXScale()),
				"yScaleBox" : unicode(cg.getYScale()),
				"rotBox" : unicode(cg.getRotation()),
				"xOffsetBox" : unicode(cg.getXShift()),
				"yOffsetBox" : unicode(cg.getYShift()),
				"transBox" : unicode(layer.getLayerTransparency())
			})
			
			self._widget.findChild(name="pathingBox").selected = int(layer.getPathingStrategy())
			self._widget.findChild(name="gridBox").selected = int(cgtype)
		else:
			self._widget.findChild(name="pathingBox").selected = 0
			self._widget.findChild(name="gridBox").selected = 0

		self._widget.mapEvents({
			'okButton'     : self._finished,
			'cancelButton' : self._cancelled
		})

		self._widget.show()
		
	def _cancelled(self):
		""" """
		if self.onCancel:
			self.onCancel()
		self._widget.hide()		

	def _finished(self):
		""" """
		# Collect and validate data
		layerId = self._widget.collectData('layerBox')
		if layerId == '':
			dialogs.message(message=unicode("Please enter a layer id."), caption=unicode("Error"))
			return
			
		try:
			x_offset = float(self._widget.collectData('xOffsetBox'))
			y_offset = float(self._widget.collectData('yOffsetBox'))
		except ValueError:
			dialogs.message(message=unicode("Please enter integer or decimal values for offset."), caption=unicode("Error"))
			return

		try:
			x_scale = float(self._widget.collectData('xScaleBox'))
			y_scale = float(self._widget.collectData('yScaleBox'))
		except ValueError:
			dialogs.message(message=unicode("Please enter integer or decimal values for scale."), caption=unicode("Error"))
			return

		try:
			rotation = float(self._widget.collectData('rotBox'))
		except ValueError:
			dialogs.message(message=unicode("Please enter integer or decimal value for rotation."), caption=unicode("Error"))
			return
			
		try:
			transparency = int(self._widget.collectData('transBox'))
		except ValueError:
			dialogs.message(message=unicode("Please enter an integer value in the range of 0-255 for transparency."), caption=unicode("Error"))
			return
			
		
		#Clamp the transparency value between 0 and 255
		if transparency < 0:
			transparency = 0
		if transparency > 255:
			transparency = 255
		
		grid_type = int(self._widget.collectData('gridBox'))
		pathing = int(self._widget.collectData('pathingBox'))

		if grid_type == 0:
			grid_type = "square"
		else:
			grid_type = "hexagonal"

		# Set up layer
		layer = self.layer
		cellgrid = None
		
		cellgrid = self.model.getCellGrid(grid_type)
		if not cellgrid:
			print "Invalid grid type"
			return

		cellgrid.setRotation(rotation)
		cellgrid.setXScale(x_scale)
		cellgrid.setYScale(y_scale)
		cellgrid.setXShift(x_offset)
		cellgrid.setYShift(y_offset)
	
		if not self.layer:
			try:
				layer = self.map.createLayer(str(layerId), cellgrid)
				
			except fife.NameClash:
				print 'The layer ' + str(layerId) + ' already exists!'
				return
		else:
			layer.setCellGrid(cellgrid)
			try:
				layer.setId(str(layerId))
			except fife.NameClash:
				print 'The layer ' + str(layerId) + ' already exists!'
				return
		
		layer.setPathingStrategy(pathing)
		layer.setLayerTransparency(transparency)
		
		for cam in self.map.getCameras():
			cam.resetRenderers()
		
		# Hide dialog and call back
		self._widget.hide()
		
		if self.callback:
			pychan.tools.applyOnlySuitable(self.callback, layer=layer)
