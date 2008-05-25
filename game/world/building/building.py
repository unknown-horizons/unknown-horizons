# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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
import game.main
#TODO: Implement selection support over a common interface with Unit

class BlockedError(Exception):
	pass

class Building(object):
	def __init__(self, x, y, owner, instance = None):
		self.x = x
		self.y = y
		self.owner = owner
		if instance == None:
			self.createInstance(x, y)
		else:
			self._instance = instance
			game.main.game.entities.updateInstance(self._instance, self)

	def calcBuildingCost(cls, ground_layer,  building_layer, position):
		#TODO do ground checking and throw exception if blocked
		def checkLayer(layer):
			for x in xrange(cls.size[0]):
				for y in xrange(cls.size[1]):
					coord = fife.ModelCoordinate(int(position.x + y),  int(position.y + y))
					if (layer.cellContainsBlockingInstance(coord)):
						raise BlockedError

		checkLayer(ground_layer)
		checkLayer(building_layer)

		cost = (100,  1,  1,  1)
		return cost

	calcBuildingCost = classmethod(calcBuildingCost)
