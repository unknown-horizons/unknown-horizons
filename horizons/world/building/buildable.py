# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import itertools

from horizons.util import Point, Rect, decorators, Circle, WorldObject
from horizons.util.pathfinding.roadpathfinder import RoadPathFinder
from horizons.constants import BUILDINGS
from horizons.entities import Entities

class BuildableErrorTypes(object):
	"""Killjoy class. Collection of reasons why you can't build."""
	NO_ISLAND, UNFIT_TILE, NO_SETTLEMENT, OTHER_PLAYERS_SETTLEMENT, \
	OTHER_PLAYERS_SETTLEMENT_ON_ISLAND, OTHER_BUILDING_THERE, UNIT_THERE, NO_COAST, \
	NO_OCEAN_NEARBY, ONLY_NEAR_SHIP, NEED_RES_SOURCE, ISLAND_ALREADY_SETTLED = range(12)

	text = {
	  NO_ISLAND : _("This building must be built on an island."),
	  UNFIT_TILE : _("This ground is not suitable for this building."),
	  NO_SETTLEMENT : _("This building has to be built within your settlement."),
	  OTHER_PLAYERS_SETTLEMENT : _("This area is already occupied by another player."),
	  OTHER_BUILDING_THERE : _("This area is already occupied by another building."),
	  UNIT_THERE : _("This area is already occupied by a unit."),
	  NO_COAST : _("This building must be built on the coastline."),
	  NO_OCEAN_NEARBY : _("This building has to be placed at the ocean."),
	  ONLY_NEAR_SHIP : _("This spot is too far away from your ship."),
	  NEED_RES_SOURCE : _("This building can only be built on a resource source."),
	  ISLAND_ALREADY_SETTLED : _("You have already settled this island.")
	}
	# TODO: say res source which one we need, maybe even highlight those

class _BuildPosition(object):
	"""A possible build position in form of a data structure.
	Don't use directly outside of this file"""
	def __init__(self, position, rotation, tearset, buildable, action='idle',
	             problem=None):
		"""
		@param position: Rect, building position and size
		@param rotation: int rotation of building
		@param tearset: list of worldids of buildings to tear for this building to build
		@param buildable: whether building is actually buildable there
		@param action: action (animation of building)
		@param problem: (error number, error string) reason it's not buildable or None
		"""
		self.position = position
		self.rotation = rotation
		self.tearset = tearset
		self.buildable = buildable
		self.action = action
		self.problem = problem

	def __nonzero__(self):
		"""Returns buildable value. This enables code such as "if cls.check_build()"""
		return self.buildable

	def __eq__(self, other):
		if not isinstance(other, _BuildPosition):
			return False
		return self.position == other.position and \
		       self.rotation == other.rotation and \
		       self.action == other.action and \
		       self.tearset == other.tearset

	def __ne__(self, other):
		return not self.__eq__(other)

class _NotBuildableError(Exception):
	"""Internal exception."""
	def __init__(self, errortype):
		super(_NotBuildableError, self).__init__()
		self.errortype = errortype

class Buildable(object):
	"""Interface for every kind of buildable objects.
	Contains methods to determine whether a building can be placed on a coordinate, regarding
	island, settlement, ground requirements etc. Does not care about building costs."""

	irregular_conditions = False # whether all ground tiles have to fulfill the same conditions

	# check this far for fuzzy build
	CHECK_NEARBY_LOCATIONS_UP_TO_DISTANCE = 3

	# INTERFACE

	@classmethod
	def check_build(cls, session, point, rotation=45, check_settlement=True, ship=None, issuer=None):
		"""Check if a building is buildable here.
		All tiles, that the building occupies are checked.
		@param point: Point instance, coords
		@param rotation: prefered rotation of building
		@param check_settlement: whether to check for a settlement (for settlementless buildings)
		@param ship: ship instance if building from ship
		@return instance of _BuildPosition"""
		# for non-quadratic buildings, we have to switch width and height depending on the rotation
		if rotation == 45 or rotation == 225:
			position = Rect.init_from_topleft_and_size(point.x, point.y, cls.size[0], cls.size[1])
		else:
			position = Rect.init_from_topleft_and_size(point.x, point.y, cls.size[1], cls.size[0])

		buildable = True
		problem = None
		tearset = []
		try:
			island = cls._check_island(session, position)
			# TODO: if the rotation changes here for non-quadratic buildings, wrong results will be returned
			rotation = cls._check_rotation(session, position, rotation)
			tearset = cls._check_buildings(session, position, island=island)
			cls._check_units(session, position)
			if check_settlement:
				cls._check_settlement(session, position, ship=ship, issuer=issuer)
		except _NotBuildableError as e:
			buildable = False
			problem = (e.errortype, _(BuildableErrorTypes.text[e.errortype]))

		return _BuildPosition(position, rotation, tearset, buildable, problem=problem)

	@classmethod
	def check_build_line(cls, session, point1, point2, rotation=45, ship=None):
		"""Checks out a line on the map for build possibilities.
		The line usually is a draw of the mouse.
		@param point1, point2: Point instance, start and end of the line
		@param rotation: prefered rotation
		@param ship: ship instance if building from ship
		@return list of _BuildPositions
		"""
		raise NotImplementedError()

	@classmethod
	def is_tile_buildable(cls, session, tile, ship, island=None, check_settlement=True):
		"""Checks a tile for buildability.
		@param tile: Ground object
		@param ship: Ship instance if building from ship
		@param island: Island instance, if already known. If None, it will be calculated
		@param check_settlement: bool, whether to check for settlement
		@return bool, True for "is buildable" """
		position = Point(tile.x, tile.y)
		try:
			cls._check_island(session, position, island)
			if check_settlement:
				cls._check_settlement(session, position, ship=ship)
			cls._check_buildings(session, position)
		except _NotBuildableError:
			return False

		if cls.irregular_conditions:
			# check in case not all ground tiles have to fulfill the same conditions (e.g. when 1 tile has to be coast)

			# at least one location that has this tile must be actually buildable
			# area of the buildings is (x, y) + width/height, therefore all build positions that
			# include (x, y) are (x, y) - ( [0..width], [0..height] )
			return any( cls.check_build(session, Point(tile.x - x_off, tile.y - y_off), ship=ship) for
				          x_off, y_off in itertools.product(xrange(cls.size[0]), xrange(cls.size[1])) )
		else:
			return True

	@classmethod
	def check_build_fuzzy(cls, session, point, *args, **kwargs):
		"""Same as check_build, but consider point to be a vague suggestions
		and search nearby area for buildable position.
		Returns one of the closest viable positions or the original position as not buildable if none can be found"""

		# this is some kind of case study of applied functional programming

		def filter_duplicates(gen, transform=lambda x : x):
			"""
			@param transform: transforms elements to hashable equivalent
			"""
			checked = set()
			for elem in itertools.ifilterfalse(lambda e : transform(e) in checked, gen):
				checked.add( transform(elem) )
				yield elem

		# generate coords near point, search coords of small circles to larger ones
		def get_positions():
			iters = (iter(Circle(point, radius)) for radius in xrange(cls.CHECK_NEARBY_LOCATIONS_UP_TO_DISTANCE) )
			return itertools.chain.from_iterable( iters )

		# generate positions and check for matches
		check_pos = lambda pos : cls.check_build(session, pos, *args, **kwargs)
		checked = itertools.imap(check_pos,
		                         filter_duplicates( get_positions(), transform=lambda p : p.to_tuple() ) )

		# filter positive solutions
		result_generator = itertools.ifilter(lambda buildpos: buildpos.buildable, checked)

		try:
			# return first match
			return result_generator.next()
		except StopIteration:
			# found none, fail with specified paramters
			return check_pos(point)


	# PRIVATE PARTS

	@classmethod
	def _check_island(cls, session, position, island=None):
		"""Check if there is an island and enough tiles.
		@throws _NotBuildableError if building can't be built.
		@param position: coord Point to build at
		@param island: Island instance if known before"""
		if island is None:
			if position.__class__ is Rect: # performance optimisation
				at = position.left, position.top
			else:
				at = position.center().to_tuple()
			island = session.world.get_island_tuple( at )
			if island is None:
				raise _NotBuildableError(BuildableErrorTypes.NO_ISLAND)
		for tup in position.tuple_iter():
			# can't use get_tile_tuples since it discards None's
			tile = island.get_tile_tuple(tup)
			if tile is None:
				raise _NotBuildableError(BuildableErrorTypes.NO_ISLAND)
			if 'constructible' not in tile.classes:
				raise _NotBuildableError(BuildableErrorTypes.UNFIT_TILE)
		return island

	@classmethod
	def _check_rotation(cls, session, position, rotation):
		"""Returns a possible rotation for this building.
		@param position: Rect or Point instance, position and size
		@param rotation: The prefered rotation
		@return: integer, an available rotation in degrees"""
		return rotation

	@classmethod
	def _check_settlement(cls, session, position, ship=None, issuer=None):
		"""Check if there is a settlement and if it belongs to the human player"""
		settlement = session.world.get_settlement(position.center())
		player = issuer if issuer is not None else session.world.player
		if settlement is None:
			raise _NotBuildableError(BuildableErrorTypes.NO_SETTLEMENT)
		if player != settlement.owner:
			raise _NotBuildableError(BuildableErrorTypes.OTHER_PLAYERS_SETTLEMENT)

	@classmethod
	def _check_buildings(cls, session, position, island=None):
		"""Check if there are buildings blocking the build.
		@return Iterable of worldids of buildings that need to be teared in order to build here"""
		if island is None:
			island = session.world.get_island(position.center())
			# _check_island already confirmed that there must be an island here, so no check for None again
		tearset = set()
		for tile in island.get_tiles_tuple( position.tuple_iter() ):
			obj = tile.object
			if obj is not None: # tile contains an object
				if obj.buildable_upon:
					if obj.__class__ is cls:
						# don't tear trees to build trees over them
						raise _NotBuildableError(BuildableErrorTypes.OTHER_BUILDING_THERE)
					# tear it so we can build over it
					tearset.add(obj.worldid)
				else:
					# building is blocking the build
					raise _NotBuildableError(BuildableErrorTypes.OTHER_BUILDING_THERE)
		if hasattr(session.manager, 'get_builds_in_construction'):
			builds_in_construction = session.manager.get_builds_in_construction()
			for build in builds_in_construction:
				(sizex, sizey) = Entities.buildings[build.building_class].size
				for (neededx, neededy) in position.tuple_iter():
					if neededx in range(build.x, build.x+sizex) and neededy in range(build.y, build.y+sizey):
						raise _NotBuildableError(BuildableErrorTypes.OTHER_BUILDING_THERE)
		return tearset

	@classmethod
	def _check_units(cls, session, position):
		for tup in position.tuple_iter():
			if tup in session.world.ground_unit_map:
				raise _NotBuildableError(BuildableErrorTypes.UNIT_THERE)

class BuildableSingle(Buildable):
	"""Buildings one can build single. """
	@classmethod
	def check_build_line(cls, session, point1, point2, rotation=45, ship=None):
		# only build 1 building at endpoint
		# correct placement for large buildings (mouse should be at center of building)
		point2 = point2.copy() # only change copy
		point2.x -= (cls.size[0] - 1) / 2
		point2.y -= (cls.size[1] - 1) / 2
		return [ cls.check_build_fuzzy(session, point2, rotation=rotation, ship=ship) ]

class BuildableSingleEverywhere(BuildableSingle):
	"""Buildings, that can be built everywhere. Usually not used for buildings placeable by humans."""
	@classmethod
	def check_build(cls, session, point, rotation=45, check_settlement=True, ship=None, issuer=None):
		# for non-quadratic buildings, we have to switch width and height depending on the rotation
		if rotation == 45 or rotation == 225:
			position = Rect.init_from_topleft_and_size(point.x, point.y, cls.size[0], cls.size[1])
		else:
			position = Rect.init_from_topleft_and_size(point.x, point.y, cls.size[1], cls.size[0])

		buildable = True
		tearset = []
		return _BuildPosition(position, rotation, tearset, buildable)


class BuildableRect(Buildable):
	"""Buildings one can build as a Rectangle, such as Trees"""
	@classmethod
	def check_build_line(cls, session, point1, point2, rotation=45, ship=None):
		if point1 == point2:
			# this is actually a masked single build
			return [cls.check_build_fuzzy(session, point1, rotation=rotation, ship=ship)]
		possible_builds = []
		area = Rect.init_from_corners(point1, point2)
		# correct placement for large buildings (mouse should be at center of building)
		area.left -= (cls.size[0] - 1) / 2
		area.right -= (cls.size[0] - 1) / 2
		area.top -= (cls.size[1] - 1) / 2
		area.bottom -= (cls.size[1] - 1) / 2

		for x in xrange(area.left, area.right+1, cls.size[0]):
			for y in xrange(area.top, area.bottom+1, cls.size[1]):
				possible_builds.append(
				  cls.check_build(session, Point(x, y), rotation=rotation, ship=ship)
				)
		return possible_builds


class BuildableLine(Buildable):
	"""Buildings one can build in a line, such as paths"""
	@classmethod
	def check_build_line(cls, session, point1, point2, rotation=45, ship=None):

		# Pathfinding currently only supports buildingsize 1x1, so don't use it in this case
		if cls.size != (1, 1):
			return [ cls.check_build_fuzzy(session, point2, rotation=rotation, ship=ship) ]

		# use pathfinding to get a path, then try to build along it
		island = session.world.get_island(point1)
		if island is None:
			return []

		path = RoadPathFinder()(island.path_nodes.nodes, point1.to_tuple(), point2.to_tuple(), rotation == 45 or rotation == 225)
		if path is None: # can't find a path between these points
			return [] # TODO: maybe implement alternative strategy

		possible_builds = []

		for i in path:
			action = ''
			for action_char, offset in \
			    sorted(BUILDINGS.ACTION.action_offset_dict.iteritems()): # order is important here
				if (offset[0]+i[0], offset[1]+i[1]) in path:
					action += action_char
			if action == '':
				action = 'single' # single trail piece with no neighbours

			build = cls.check_build(session, Point(*i))
			build.action = action
			possible_builds.append(build)

		return possible_builds


class BuildableSingleOnCoast(BuildableSingle):
	"""Buildings one can only build on coast, such as BoatBuilder, Fisher"""
	irregular_conditions = True
	@classmethod
	def _check_island(cls, session, position, island=None):
		# ground has to be either coastline or constructible, > 1 tile must be coastline
		# can't use super, since it checks all tiles for constructible

		if island is None:
			island = session.world.get_island(position.center())
			if island is None:
				raise _NotBuildableError(BuildableErrorTypes.NO_ISLAND)

		coastline_found = False
		for tup in position.tuple_iter():
			# can't use get_tile_tuples since it discards None's
			tile = island.get_tile_tuple(tup)
			if tile is None:
				raise _NotBuildableError(BuildableErrorTypes.NO_ISLAND)
			if 'coastline' in tile.classes:
				coastline_found = True
			elif 'constructible' not in tile.classes: # neither coastline, nor constructible
				raise _NotBuildableError(BuildableErrorTypes.UNFIT_TILE)
		if not coastline_found:
			raise _NotBuildableError(BuildableErrorTypes.NO_COAST)
		return island

	@classmethod
	def _check_rotation(cls, session, position, rotation):
		"""Rotate so that the building faces the seaside"""
		# array of coords (points are True if is coastline)
		coastline = {}
		x, y = position.origin.to_tuple()
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
		maximum = -1
		rotation = -1
		for rot, val in coast_line_points_per_side.iteritems():
			if val > maximum:
				maximum = val
				rotation = rot
		return rotation

class BuildableSingleOnOcean(BuildableSingleOnCoast):
	"""Requires ocean nearby as well"""

	@classmethod
	def _check_island(cls, session, position, island=None):
		# this might raise, just let it through
		super(BuildableSingleOnOcean, cls)._check_island(session, position, island)
		if island is None:
			island = session.world.get_island(position.center())
			if island is None:
				raise _NotBuildableError(BuildableErrorTypes.NO_ISLAND)
		posis = position.get_coordinates()
		for tile in posis:
			for rad in Circle(Point(*tile), 3):
				if island.get_tile(rad) is None:
					# Tile not on island -> deep water
					return island
		raise _NotBuildableError(BuildableErrorTypes.NO_OCEAN_NEARBY)



class BuildableSingleFromShip(BuildableSingleOnOcean):
	"""Buildings that can be build from a ship. Currently only Warehouse."""
	@classmethod
	def _check_settlement(cls, session, position, ship, issuer=None):
		# building from ship doesn't require settlements
		# but a ship nearby:
		if ship.position.distance(position) > BUILDINGS.BUILD.MAX_BUILDING_SHIP_DISTANCE:
			raise _NotBuildableError(BuildableErrorTypes.ONLY_NEAR_SHIP)

		for i in position:
			# and the position mustn't be owned by anyone else
			settlement = session.world.get_settlement(i)
			if settlement is not None:
				raise _NotBuildableError(BuildableErrorTypes.OTHER_PLAYERS_SETTLEMENT)

		# and player mustn't have a settlement here already
		island = session.world.get_island(position.center())
		for s in island.settlements:
			if s.owner == ship.owner:
				raise _NotBuildableError(BuildableErrorTypes.ISLAND_ALREADY_SETTLED)


class BuildableSingleOnDeposit(BuildableSingle):
	"""For mines; those buildings are only buildable upon other buildings (clay pit on clay deposit, e.g.)
	For now, mines can only be built on a single type of deposit.
	This is specified in game.sqlite in the table "mine", and saved in cls.buildable_on_deposit in
	the buildingclass.
	"""
	irregular_conditions = True
	@classmethod
	def _check_buildings(cls, session, position, island=None):
		"""Check if there are buildings blocking the build"""
		if island is None:
			island = session.world.get_island(position.center())
		deposit = None
		for tile in island.get_tiles_tuple( position.tuple_iter() ):
			if tile.object is None or \
			   tile.object.id != cls.buildable_on_deposit_type or \
			   (deposit is not None and tile.object != deposit): # only build on 1 deposit
				raise _NotBuildableError(BuildableErrorTypes.NEED_RES_SOURCE)
			deposit = tile.object
		return set([deposit.worldid])

	@classmethod
	def _check_rotation(cls, session, position, rotation):
		"""The rotation should be the same as the one of the underlying mountain"""
		tearset = cls._check_buildings(session, position) # will raise on problems
		# rotation fix code is only reached when building is buildable
		mountain = WorldObject.get_object_by_id( iter(tearset).next() )
		return mountain.rotation


decorators.bind_all(Buildable)
decorators.bind_all(BuildableSingle)
decorators.bind_all(BuildableRect)
decorators.bind_all(BuildableSingleFromShip)
decorators.bind_all(BuildableSingleOnCoast)
decorators.bind_all(BuildableSingleOnDeposit)
