# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.ext.enum import Enum
from horizons.constants import BUILDINGS
from horizons.util import Point
from horizons.world.building.buildable import Buildable
from horizons.entities import Entities
from horizons.command.building import Build

class VillageBuilder(object):
	purpose = Enum('main_square', 'tent', 'road', 'reserved')
	
	def __init__(self, land_manager):
		self.land_manager = land_manager
		
	def create_plan(self):
		"""
		The algorithm is as follows:
		Place the main square and then form a road grid to support the tents;
		prefer the one with maximum number of tent locations and minimum number of
		impossible road locations.
		"""

		best = None
		best_value = -1
		xs = set([coords[0] for coords in self.land_manager.village])
		ys = set([coords[1] for coords in self.land_manager.village])
		session = self.land_manager.island.session
		tent_squares = [(0, 0), (0, 1), (1, 0), (1, 1)]
		road_connections = [(-1, -1), (-1, 0), (-1, 1), (-1, 2), (0, -1), (0, 2), (1, -1), (1, 2), (2, -1), (2, 0), (2, 1), (2, 2)]

		for x, y in self.land_manager.village:
			# will it fit in the area?
			if (x + 5, y + 5) not in self.land_manager.village:
				continue

			point = Point(x, y)
			sq_location = Entities.buildings[BUILDINGS.MARKET_PLACE_CLASS].check_build(session, point)
			if not sq_location.buildable:
				continue

			usage = dict.fromkeys(self.land_manager.village)
			bad_roads = 0
			good_tents = 0

			# place the main square
			for dy in xrange(6):
				for dx in xrange(6):
					usage[(x + dx, y + dy)] = (self.purpose.reserved, None)
			usage[(x, y)] = (self.purpose.main_square, sq_location)

			# place the roads running parallel to the y-axis
			for road_y in ys:
				if road_y < y:
					if (y - road_y) % 5 != 1:
						continue
				else:
					if road_y < y + 6 or (road_y - y) % 5 != 1:
						continue
				for road_x in xs:
					coords = (road_x, road_y)
					if coords not in self.land_manager.village:
						bad_roads += 1
						continue
					location = Entities.buildings[BUILDINGS.TRAIL_CLASS].check_build(session, Point(road_x, road_y))
					if location.buildable:
						usage[coords] = (self.purpose.road, location)
					else:
						bad_roads += 1

			# place the roads running parallel to the x-axis
			for road_x in xs:
				if road_x < x:
					if (x - road_x) % 5 != 1:
						continue
				else:
					if road_x < x + 6 or (road_x - x) % 5 != 1:
						continue
				for road_y in ys:
					coords = (road_x, road_y)
					if coords not in self.land_manager.village:
						bad_roads += 1
						continue
					location = Entities.buildings[BUILDINGS.TRAIL_CLASS].check_build(session, Point(road_x, road_y))
					if location.buildable:
						usage[coords] = (self.purpose.road, location)
					else:
						bad_roads += 1

			# place the tents
			for coords in sorted(usage):
				ok = True
				for dx, dy in tent_squares:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 not in usage or usage[coords2] is not None:
						ok = False
						break
				if not ok:
					continue
				location = Entities.buildings[BUILDINGS.RESIDENTIAL_CLASS].check_build(session, Point(coords[0], coords[1]))
				if not location.buildable:
					continue

				# is there a road connection?
				ok = False
				for dx, dy in road_connections:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 in usage and usage[coords2] is not None and usage[coords2][0] == self.purpose.road:
						ok = True
						break

				# connection to a road tile exists, build the tent
				if ok:
					for dx, dy in tent_squares:
						usage[(coords[0] + dx, coords[1] + dy)] = (self.purpose.reserved, None)
					usage[coords] = (self.purpose.tent, location)
					good_tents += 1

			value = 10 * good_tents - bad_roads
			if best_value < value:
				best = usage
				best_value = value

		self.plan = best

	def display(self):
		road_colour = (30, 30, 30)
		tent_colour = (255, 255, 255)
		sq_colour = (255, 0, 255)
		reserved_colour = (0, 0, 255)
		unknown_colour = (255, 0, 0)
		renderer = self.land_manager.island.session.view.renderer['InstanceRenderer']

		for coords, usage in self.plan.iteritems():
			tile = self.land_manager.island.ground_map[coords]
			if usage is None:
				renderer.addColored(tile._instance, *unknown_colour)
			else:
				usage = usage[0]
				if usage == self.purpose.main_square:
					renderer.addColored(tile._instance, *sq_colour)
				elif usage == self.purpose.tent:
					renderer.addColored(tile._instance, *tent_colour)
				elif usage == self.purpose.road:
					renderer.addColored(tile._instance, *road_colour)
				elif usage == self.purpose.reserved:
					renderer.addColored(tile._instance, *reserved_colour)
