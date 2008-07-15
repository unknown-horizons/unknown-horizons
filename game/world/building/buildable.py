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

import game.main
import math

class BuildableSingle(object):
	@classmethod
	def isBuildable(cls, x, y):
		return True

	@classmethod
	def getBuildList(cls, point1, point2):
		x = int(round(point2[0])) - (cls.size[0] - 1) / 2 if (cls.size[0] % 2) == 1 else int(math.ceil(point2[0])) - (cls.size[0]) / 2
		y = int(round(point2[1])) - (cls.size[1] - 1) / 2 if (cls.size[1] % 2) == 1 else int(math.ceil(point2[1])) - (cls.size[1]) / 2
		island = game.main.session.world.get_island(x, y)
		if island is None:
			return None
		for xx in xrange(x, x + cls.size[0]):
			for yy in xrange(y, y + cls.size[1]):
				if island.get_tile(xx,yy) is None:
					return None
		settlements = island.get_settlements(x, y, x + cls.size[0] - 1, y + cls.size[1] - 1)
		if len(settlements) > 1:
			return None
		return {'island' : island, 'settlement' : None if len(settlements) == 0 else settlements.pop(), 'buildings' : [{'x' : x, 'y' : y}]}

class BuildableRect(BuildableSingle):
	@classmethod
	def getBuildList(cls, point1, point2):
		island = None
		settlement = None
		buildings = []
		for x in xrange(int(min(round(point1[0]), round(point2[0]))), 1 + int(max(round(point1[0]), round(point2[0])))):
			for y in xrange(int(min(round(point1[1]), round(point2[1]))), 1 + int(max(round(point1[1]), round(point2[1])))):
				new_island = game.main.session.world.get_island(x, y)
				if new_island is None or (island is not None and island != new_island):
					continue
				island = new_island

				new_settlement = island.get_settlements(x, y, x, y)
				new_settlement = None if len(new_settlement) == 0 else new_settlement.pop()
				if new_settlement is None or (settlement is not None and settlement != new_settlement): #we cant build where no settlement is or from one settlement to another
					continue
				settlement = new_settlement

				buildings.append({'x' : x, 'y' : y})
		return None if len(buildings) == 0 else {'island' : island, 'settlement' : settlement, 'buildings' : buildings}

class BuildableLine(BuildableSingle):
	@classmethod
	def getBuildList(cls, point1, point2):
		"""
		@param point1:
		@param point2:
		"""
		island = None
		settlement = None
		buildings = []
		y = int(round(point1[1]))
		for x in xrange(int(round(point1[0])), int(round(point2[0])), (1 if int(round(point2[0])) > int(round(point1[0])) else -1)):
			new_island = game.main.session.world.get_island(x, y)
			if new_island is None or (island is not None and island != new_island):
				continue
			island = new_island

			new_settlement = island.get_settlements(x, y, x, y)
			new_settlement = None if len(new_settlement) == 0 else new_settlement.pop()
			if new_settlement is None or (settlement is not None and settlement != new_settlement): #we cant build where no settlement is or from one settlement to another
				continue
			settlement = new_settlement

			buildings.append({'x' : x, 'y' : y, 'action' : ('d' if int(round(point2[0])) < int(round(point1[0])) else 'b') if len(buildings) == 0 else 'bd'})
		x = int(round(point2[0]))
		is_first = True
		for y in xrange(int(round(point1[1])), int(round(point2[1])) + (1 if int(round(point2[1])) > int(round(point1[1])) else -1), (1 if int(round(point2[1])) > int(round(point1[1])) else -1)):
			new_island = game.main.session.world.get_island(x, y)
			if new_island is None or (island is not None and island != new_island):
				continue
			island = new_island

			new_settlement = island.get_settlements(x, y, x, y)
			new_settlement = None if len(new_settlement) == 0 else new_settlement.pop()
			if new_settlement is None or (settlement is not None and settlement != new_settlement): #we cant build where no settlement is or from one settlement to another
				continue
			settlement = new_settlement

			if len(buildings) == 0: #first tile
				if y == int(round(point2[1])): #only tile
					action = 'default'
				else:
					action = 'c' if int(round(point2[1])) > int(round(point1[1])) else 'a'
			elif y == int(round(point2[1])): #last tile
				if int(round(point1[1])) == int(round(point2[1])): #only tile in this loop
					action = 'd' if int(round(point2[0])) > int(round(point1[0])) else 'b'
				else:
					action = 'a' if int(round(point2[1])) > int(round(point1[1])) else 'c'
			elif y == int(round(point1[1])): #edge
				if int(round(point2[0])) > int(round(point1[0])):
					action = 'cd' if int(round(point2[1])) > int(round(point1[1])) else 'ad'
				else:
					action = 'bc' if int(round(point2[1])) > int(round(point1[1])) else 'ab'
			else:
				action = 'ac'
			buildings.append({'x' : x, 'y' : y, 'action' : action})
			is_first = False
		return None if len(buildings) == 0 else {'island' : island, 'settlement' : settlement, 'buildings' : buildings}
