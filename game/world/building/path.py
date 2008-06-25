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

from building import Building
import fife
import game.main
import math

class Path(Building):
	@classmethod
	def getBuildList(cls, point1, point2):
		island = None
		settlement = None
		buildings = []
		y = int(round(point1[1]))
		is_first = True
		for x in xrange(int(min(round(point1[0]), round(point2[0]))), int(max(round(point1[0]), round(point2[0])))):
			new_island = game.main.session.world.get_island(x, y)
			if new_island == None or (island != None and island != new_island):
				continue
			island = new_island

			new_settlement = island.get_settlements(x, y, x, y)
			new_settlement = None if len(new_settlement) == 0 else new_settlement.pop()
			if new_settlement == None or (settlement != None and settlement != new_settlement): #we cant build where no settlement is or from one settlement to another
				continue
			settlement = new_settlement

			buildings.append({'x' : x, 'y' : y, 'action' : 'c' if is_first else 'ac'})
			is_first = False
		x = int(round(point2[0]))
		is_first2 = True
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

			buildings.append({'x' : x, 'y' : y, 'action' : ('d' if is_first else 'ad') if is_first2 else 'bd'})
			is_first2 = False
		return None if len(buildings) == 0 else {'island' : island, 'settlement' : settlement, 'buildings' : buildings}
