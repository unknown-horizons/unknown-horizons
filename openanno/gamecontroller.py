# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import fife
from loaders import loadMapFile

class GameController(object):
	"""Base class representing a game controller"""
	
	def __init__(self, engine, model):
		self.engine = engine
		self.model = model
		self.metamodel = self.engine.getModel().getMetaModel()
		self.map = None
		
	def create_world(self, path):
		self.map = loadMapFile(path, self.engine)
		
		self.elevation = self.map.getElevations("id", "OpenAnnoMapElevation")[0]
		self.layer = self.elevation.getLayers("id", "landLayer")[0]
		self.spriteLayer = self.elevation.getLayers("id", "spriteLayer")[0]
		
		img = self.engine.getImagePool().getImage(self.layer.getInstances()[0].getObject().get2dGfxVisual().getStaticImageIndexByAngle(0))
		self.screen_cell_w = img.getWidth()
		self.screen_cell_h = img.getHeight()

		self.tent_obj = self.metamodel.getObjects("id", "tent")[0]
		self.tent = self.spriteLayer.createInstance(self.tent_obj, fife.ModelCoordinate(-2, -2))
		fife.InstanceVisual.create(self.tent)
		
		self.model.map = self.map
	
	def issue_command(self, command):
		"""Issue a command"""
		raise Exception("Virtual function!")
