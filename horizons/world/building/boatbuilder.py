# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
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

from building import Building, Selectable
from buildable import BuildableSingle
from horizons.world.unitproducer import UnitProducer
from horizons.world.consumer import Consumer

class BoatBuilder(Selectable, BuildableSingle, UnitProducer, Building):

	def __init__(self, **kwargs):
		super(BoatBuilder, self).__init__(**kwargs)


	@classmethod
	def isSettlementBuildRequirementSatisfied(cls, x, y, island, ship, **state):
		settlements = island.get_settlements(Rect(x, y, x + cls.size[0] - 1, y + cls.size[1] - 1))
		#if multi branch office allowed:
		#if len(settlements) == 1:
		#	return settlements.pop()
		if len(settlements) != 0:
			return {'buildable' : False}
		#ship check
		if (max(x - ship.position.x, 0, ship.position.x - x - cls.size[0] + 1) ** 2) + \
		   (max(y - ship.position.y, 0, ship.position.y - y - cls.size[1] + 1) ** 2) > 25:
			return {'buildable' : False}
		return {'settlement' : None}

	@classmethod
	def isGroundBuildRequirementSatisfied(cls, x, y, island, **state):
		#todo: check cost line
		coast_tile_found = False
		for xx,yy in [ (xx,yy) for xx in xrange(x, x + cls.size[0]) for yy in xrange(y, y + cls.size[1]) ]:
			#print "x y:", xx, yy
			tile = island.get_tile(Point(xx,yy))
			classes = tile.__class__.classes
			#print classes
			if 'coastline' in classes:
				coast_tile_found = True
			elif 'constructible' not in classes:
				return {'buildable' : False}

		return {} if coast_tile_found else {'buildable' : False}
