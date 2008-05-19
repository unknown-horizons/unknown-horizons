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

_buildingclasses = {}

def initBuildingClasses():
	buildings = game.main.instance.db.query("SELECT rowid, class_package, class_type, size_x, size_y, name FROM building")
	for building_id,  package,  class_type,  size_x,  size_y,  name in buildings.rows:

		#FIXME: these entrys should be deleted
		if len(class_type) == 0: continue

		module = __import__(package,  globals(), locals())
		baseclass = getattr(module,  class_type)

		propdict = {}
		propdict['size'] = (size_x,  size_y)

		properties = game.main.instance.db.query("SELECT name, value FROM building_property WHERE building_id = ?",  str(building_id))
		for (key,  value) in properties.rows:
			propdict[value] = key

		global _buildingclasses
		_buildingclasses[building_id] = type(str(name),  (baseclass, ),  propdict)

def getBuildingClass(building_id):
	bclass = _buildingclasses[building_id]
	assert (bclass is not None)
	return bclass
