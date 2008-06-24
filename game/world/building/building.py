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
#TODO: Implement selection support over a common interface with Unit

class BlockedError(Exception):
	pass

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
	def getBuildList(cls, point1, point2):
		if (int(point1[0] + 0.5) == int(point2[0] + 0.5) and int(point1[1] + 0.5) == int(point2[1] + 0.5)) or cls.size[0] > 1 or cls.size[1] > 1:
			island = game.main.session.world.get_island(int(point2[0] + 0.5), int(point2[1] + 0.5))
			print island
			if island == None:
				return []
			settlements = island.get_settlements(int(point2[0] + 0.5), int(point2[1] + 0.5), int(point2[0] + 0.5) + cls.size[0] - 1, int(point2[1] + 0.5) + cls.size[1] - 1)
			return [{'class' : cls, 'x' : point2[0], 'y' : point2[1], 'instance' : cls.createInstance(*point2), 'settlement' : None if len(settlements) == 0 else settlements.pop()}]
		else:
			ret = []
			for x in xrange(min(int(point1[0] + 0.5), int(point2[0] + 0.5)), max(int(point1[0] + 1.5), int(point2[0] + 1.5))):
				for y in xrange(min(int(point1[1] + 0.5), int(point2[1] + 0.5)), max(int(point1[1] + 1.5), int(point2[1] + 1.5))):
					island = game.main.session.world.get_island(x, y)
					print island
					if island != None:
						settlements = island.get_settlements(x, y, x, y)
						ret.append({'class' : cls, 'x' : x, 'y' : y, 'instance' : cls.createInstance(x, y), 'settlement' : None if len(settlements) == 0 else settlements.pop()})
			return ret

	@classmethod
	def calcBuildingCost(self):
		#TODO do ground checking and throw exception if blocked
		return self.costs

	def start(self):
		"""This function is called when the building is built, to start production for example."""
		pass
