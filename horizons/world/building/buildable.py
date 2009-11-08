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

import math

from horizons.util import Point, Rect, decorators

class Buildable(object):
	"""Base class for every kind of buildables"""

class BuildableSingle(Buildable):
	"""Buildings you can build single.
	The Buildable* classes are a collection of classmethods checking the building
	requirements on a certain place, each returning None if build is not possible here.
	In case of a possible build location, a dict is returned with related attribute (possibly empty).
	TODO: document those return values

	For general use, only get_build_list is intended.
	"""

	@decorators.make_constants()
	@classmethod
	def _are_build_requirements_satisfied(cls, session, x, y, before = None, **kwargs):
		state = {'x' : x, 'y' : y}
		state.update(kwargs)
		# apply all build checks
		for check in (cls._is_island_build_requirement_satisfied, \
									cls._is_settlement_build_requirement_satisfied, \
									cls._is_ground_build_requirement_satisfied, \
									cls._is_building_build_requirement_satisfied, \
									cls._is_unit_build_requirement_satisfied):
			update = check(session, **state)
			if update is None:
				return None
			else:
				state.update(update)
				if 'buildable' in update and update['buildable'] == False:
					return state
		if before is not None:
			update = cls._is_multi_build_requirement_satisfied(session, *before, **state)
			if update is None:
				return None
			else:
				state.update(update)
				if 'buildable' in update and update['buildable'] == False:
					return state
		return state

	@decorators.make_constants()
	@classmethod
	def _is_multi_build_requirement_satisfied(cls, session, *before, **state):
		for i in before:
			if not i.get('buildable', True):
				continue
			if i['island'] != state['island']:
				return {'buildable' : False}
		return {}

	@decorators.make_constants()
	@classmethod
	def _is_island_build_requirement_satisfied(cls, session, x, y, **state):
		"""Checks if there is an island at x,y
		Returns either {'buildable': False} or {'island': island}"""
		island = session.world.get_island(Point(x, y))
		if island is None:
			return {'buildable' : False}
		p = Point(0, 0)
		for p.x, p.y in ((xx, yy) for xx in xrange(x, x + cls.size[0]) for yy in xrange(y, y + cls.size[1])):
			if island.get_tile(p) is None:
				return {'buildable' : False}
		return {'island' : island}

	@decorators.make_constants()
	@classmethod
	def _is_settlement_build_requirement_satisfied(cls, session, x, y, island, **state):
		"""Checks if there is a settlement at x, y
		Returns either {'buildable': False} or {'settlement': settlement}"""
		settlements = island.get_settlements(Rect(x, y, x + cls.size[0] - 1, y + cls.size[1] - 1))
		if len(settlements) != 1:
			return {'buildable' : False}
		return {'settlement' : settlements.pop()}

	@decorators.make_constants()
	@classmethod
	def _is_ground_build_requirement_satisfied(cls, session, x, y, island, **state):
		"""Checks if the ground at x, y is buildable.
		Returns either {} (success) or {'buildable': False}"""
		p = Point(0, 0)
		for p.x, p.y in ((xx, yy) for xx in xrange(x, x + cls.size[0]) for yy in xrange(y, y + cls.size[1])):
			if 'constructible' not in island.get_tile(p).__class__.classes:
				return {'buildable' : False}
			settlement = island.get_settlement(p)
			if not settlement or settlement.owner.id != session.world.player.id:
				return {'buildable' : False}
		return {}

	@decorators.make_constants()
	@classmethod
	def _is_building_build_requirement_satisfied(cls, session, x, y, island, **state):
		"""Checks if buildings are blocking the position, and wether they can be teared.
		Returns {'buildable': False} if we can't build, {} if we can build without tearing,
		or {'tear': [building1id, ...]} if we have to tear building1, ... before the build"""
		tear = set()
		p = Point(0, 0)
		for p.x, p.y in ((xx, yy) for xx in xrange(x, x + cls.size[0]) for yy in xrange(y, y + cls.size[1])):
			obj = island.get_tile(p).object
			if obj is not None:
				if obj.buildable_upon:
					if obj.__class__ is cls:
						return None
					tear.add(obj.getId())
				else:
					return {'buildable' : False}
		return {} if len(tear) == 0 else {'tear' : list(tear)}

	@decorators.make_constants()
	@classmethod
	def _is_unit_build_requirement_satisfied(cls, session, x, y, island, **state):
		return {}

	@decorators.make_constants()
	@classmethod
	def get_build_list(cls, session, point1, point2, **kwargs):
		"""Return list of buildings between startpoint (point1) and endpoint (point2)
		that can be built here.
		This is called when the user drags the mouse between these two points

		Here, we only build at the endpoint.
    """
		x = int(round(point2[0])) - (cls.size[0] - 1) / 2 if \
			(cls.size[0] % 2) == 1 else int(math.ceil(point2[0])) - (cls.size[0]) / 2
		y = int(round(point2[1])) - (cls.size[1] - 1) / 2 if \
			(cls.size[1] % 2) == 1 else int(math.ceil(point2[1])) - (cls.size[1]) / 2
		building = cls._are_build_requirements_satisfied(session, x, y, **kwargs)
		if building is None:
			return []
		else:
			return [building]

class BuildableRect(BuildableSingle):
	@decorators.make_constants()
	@classmethod
	def get_build_list(cls, session, point1, point2, **kwargs):
		buildings = []
		# iterate over all coords as rect between the points
		for x, y in ((x, y) \
								 for x in xrange(int(min(round(point1[0]), round(point2[0]))), \
																 1 + int(max(round(point1[0]), round(point2[0]))), \
		                             cls.size[0]) \
								 for y in xrange(int(min(round(point1[1]), round(point2[1]))), \
																 1 + int(max(round(point1[1]), round(point2[1]))), \
		                             cls.size[1])):
			building = cls._are_build_requirements_satisfied(session, x, y, buildings, **kwargs)
			if building is not None:
				buildings.append(building)

		return buildings

class BuildableLine(BuildableSingle):
	@decorators.make_constants()
	@classmethod
	def get_build_list(cls, session, point1, point2, **kwargs):
		buildings = []
		kwargs['rotation'] = 45
		point1_int = (int(round(point1[0])), int(round(point1[1])))
		point2_int = (int(round(point2[0])), int(round(point2[1])))
		y = point1_int[1]
		# iterate in x direction with fixed y
		for x in xrange(point1_int[0], point2_int[0], \
		                (1 if point2_int[0] > point1_int[0] else -1)*cls.size[0]):
			building = cls._are_build_requirements_satisfied(session, x, y, buildings, **kwargs)
			if building is not None:
				building.update({'action' : ('d' if point2_int[0] < point1_int[0] else 'b') if len(buildings) == 0 else 'bd'})
				buildings.append(building)
		x = point2_int[0]
		# iterate in y direction with fixed x
		for y in xrange(point1_int[1], \
										point2_int[1] + (1 if point2_int[1] > point1_int[1] else -1), \
										(1 if point2_int[1] > point1_int[1] else -1)*cls.size[1]):
			if len(buildings) == 0: #first tile
				if y == point2_int[1]: #only tile
					action = 'ac'
				else:
					action = 'c' if point2_int[1] > point1_int[1] else 'a'
			elif y == point2_int[1]: #last tile
				if point1_int[1] == point2_int[1]: #only tile in this loop
					action = 'd' if point2_int[0] > point1_int[0] else 'b'
				else:
					action = 'a' if point2_int[1] > point1_int[1] else 'c'
			elif y == point1_int[1]: #edge
				if point2_int[0] > point1_int[0]:
					action = 'cd' if point2_int[1] > point1_int[1] else 'ad'
				else:
					action = 'bc' if point2_int[1] > point1_int[1] else 'ab'
			else:
				action = 'ac' #default

			building = cls._are_build_requirements_satisfied(session, x, y, buildings, **kwargs)
			if building is not None:
				building.update({'action' : action})
				buildings.append(building)
		return buildings

""" this is not used for now, and might be defunct
class BuildableSingleWithSurrounding(BuildableSingle):
	@classmethod
	def get_build_list(cls, point1, point2, **kwargs):
		x = int(round(point2[0])) - (cls.size[0] - 1) / 2 if (cls.size[0] % 2) == 1 else int(math.ceil(point2[0])) - (cls.size[0]) / 2
		y = int(round(point2[1])) - (cls.size[1] - 1) / 2 if (cls.size[1] % 2) == 1 else int(math.ceil(point2[1])) - (cls.size[1]) / 2
		building = cls._are_build_requirements_satisfied(x, y, **kwargs)
		if building is None:
			return []
		buildings = [building]
		for xx in xrange(x - cls.radius, x + cls.size[0] + cls.radius):
			for yy in xrange(y - cls.radius, y + cls.size[1] + cls.radius):
				if ((xx < x or xx >= x + cls.size[0]) or (yy < y or yy >= y + cls.size[1])) and \
					 ((max(x - xx, 0, xx - x - cls.size[0] + 1) ** 2) + (max(y - yy, 0, yy - y - cls.size[1] + 1) ** 2)) <= cls.radius ** 2:
					building = Entities.buildings[cls._surroundingBuildingClass]._are_build_requirements_satisfied(xx, yy, **kwargs)
					if building is not None:
						building.update(building = Entities.buildings[cls._surroundingBuildingClass], **kwargs)
						buildings.append(building)
		return buildings
"""

class BuildableSingleOnCoast(BuildableSingle):
	"""BranchOffice, BoatBuilder, Fisher"""
	@decorators.make_constants()
	@classmethod
	def _is_ground_build_requirement_satisfied(cls, session, x, y, island, **state):
		coast_tile_found = False
		for xx, yy in [ (xx, yy) for xx in xrange(x, x + cls.size[0]) for yy in xrange(y, y + cls.size[1]) ]:
			tile = island.get_tile(Point(xx, yy))
			classes = tile.__class__.classes
			if 'coastline' in classes:
				coast_tile_found = True
			elif 'constructible' not in classes:
				return None

		return {} if coast_tile_found else None

	@decorators.make_constants()
	@classmethod
	def check_build_rotation(cls, session, rotation, x, y):
		"""Rotate so that the building looks out to sea"""
		if not session.world.inited:
			# while loading, skip this check
			return rotation
		# array of coords (points are True if is coastline)
		coastline = {}
		position = Rect.init_from_topleft_and_size(x, y, cls.size[0]-1, cls.size[1]-1)
		for point in position:
			if session.world.map_dimensions.contains_without_border(point):
				is_coastline = ('coastline' in session.world.get_tile(point).classes)
			else:
				is_coastline = False
			coastline[point.x-x, point.y-y] = is_coastline

		""" coastline looks something like this:
		111
		000
		000
		we have to rotate to the direction with most 1s

		Rotations:
		   45
		135   315
		   225
		"""
		coast_line_points_per_side = {
		  45: sum( coastline[(x,0)] for x in xrange(0, cls.size[0]) ),
		  135: sum( coastline[(0,y)] for y in xrange(0, cls.size[1]) ),
		  225: sum( coastline[(x, cls.size[1]-1 )] for x in xrange(0, cls.size[0]) ),
		  315: sum( coastline[(cls.size[0]-1,y)] for y in xrange(0, cls.size[1]) ),
		}

		# return rotation with biggest value
		max = -1
		rotation = -1
		for rot, val in coast_line_points_per_side.iteritems():
			if val > max:
				max = val
				rotation = rot
		return rotation
