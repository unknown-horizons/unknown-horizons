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
import game.main
import math

class Building(object):
	"""Class that represents a building. The building class is mainly a super class for other buildings.
	@param x, y: int position of the building.
	@param owner: Player that owns the building.
	@param instance: fife.Instance - only singleplayer: preview instance from the buildingtool."""
	def __init__(self, x, y, owner, instance = None):
		self.x = x
		self.y = y
		self.owner = owner
		if instance == None:
			self.createInstance(x, y)
		else:
			self._instance = instance
			game.main.session.entities.updateInstance(self._instance.getId(), self)
		self.health = 50

	def remove(self):
		for x in xrange(self.x, self.x + self.__class__.size[0]):
			for y in xrange(self.y, self.y + self.__class__.size[1]):
				tile = self.island.get_tile(x,y)
				tile.blocked = False
				tile.object = None
		game.main.session.entities.deleteInstance(self._instance.getId())
		game.main.session.view.layers[1].deleteInstance(self._instance)
		self._instance.thisown = 1

	@classmethod
	def getInstance(cls, x, y, **trash):
		instance = game.main.session.view.layers[1].createInstance(cls._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.session.entities.registerInstance(cls))
		fife.InstanceVisual.create(instance)
		instance.act('default', instance.getLocation(), True)
		return instance

	@classmethod
	def getBuildList(cls, point1, point2):
		if cls.size[0] == 1 and cls.size[1] == 1: #rect build mode
			island = None
			settlement = None
			buildings = []
			for x in xrange(int(min(round(point1[0]), round(point2[0]))), 1 + int(max(round(point1[0]), round(point2[0])))):
				for y in xrange(int(min(round(point1[1]), round(point2[1]))), 1 + int(max(round(point1[1]), round(point2[1])))):
					new_island = game.main.session.world.get_island(x, y)
					if new_island == None or (island != None and island != new_island):
						continue
					island = new_island

					new_settlement = island.get_settlements(x, y, x, y)
					new_settlement = None if len(new_settlement) == 0 else new_settlement.pop()
					if new_settlement == None or (settlement != None and settlement != new_settlement): #we cant build where no settlement is or from one settlement to another
						continue
					settlement = new_settlement

					buildings.append({'x' : x, 'y' : y})
			return None if len(buildings) == 0 else {'island' : island, 'settlement' : settlement, 'buildings' : buildings}

		else: #single build mode
			x = int(round(point2[0])) - (cls.size[0] - 1) / 2 if (cls.size[0] % 2) == 1 else int(math.ceil(point2[0])) - (cls.size[0]) / 2
			y = int(round(point2[1])) - (cls.size[1] - 1) / 2 if (cls.size[1] % 2) == 1 else int(math.ceil(point2[1])) - (cls.size[1]) / 2
			island = game.main.session.world.get_island(x, y)
			if island == None:
				return None
			for xx in xrange(x, x + cls.size[0]):
				for yy in xrange(y, y + cls.size[1]):
					if island.get_tile(xx,yy) == None:
						return None
			settlements = island.get_settlements(x, y, x + cls.size[0] - 1, y + cls.size[1] - 1)
			if len(settlements) > 1:
				return None
			return {'island' : island, 'settlement' : None if len(settlements) == 0 else settlements.pop(), 'buildings' : [{'x' : x, 'y' : y}]}

	@classmethod
	def getBuildCosts(self, **trash):
		return self.costs

	def start(self):
		"""This function is called when the building is built, to start production for example."""
		pass
