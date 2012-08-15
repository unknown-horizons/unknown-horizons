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

import weakref
import logging

from horizons.util import Point, decorators

from horizons.util.pathfinding import PathBlockedError
from horizons.util.pathfinding.pathfinding import FindPath

"""
In this file, you will find an interface to the pathfinding algorithm.
We just call this interface Pather. It is used by unit to hide implementation details
of the pathfinding algorithm.
"""

class AbstractPather(object):
	"""Abstract Interface for pathfinding for use by Unit.
	Use only subclasses!"""
	log = logging.getLogger("world.pathfinding")
	def __init__(self, unit, move_diagonal, session, make_target_walkable=True):
		"""
		@param unit: instance of unit, to which the pather belongs
		@param move_diagonal: whether the unit may walk diagonally
		@param make_target_walkable: whether we should assume, that we can walk on
		                             the tiles that make up the target
		"""
		self.session = session
		self.move_diagonal = move_diagonal
		self.make_target_walkable = make_target_walkable

		self._unit = weakref.ref(unit)

		self.destination_in_building = False
		self.source_in_building = False

		self.path = None
		self.cur = None

	@property
	def unit(self):
		return self._unit()

	def _get_path_nodes(self):
		"""Returns nodes, where unit can walk on.
		Return value type must be supported by FindPath"""
		raise NotImplementedError

	def _get_blocked_coords(self):
		"""Returns blocked coordinates
		Return value type must be supported by FindPath"""
		return []

	def _check_for_obstacles(self, point):
		"""Check if the path is unexpectedly blocked by e.g. a unit
		@param point: tuple: (x, y)
		@return: bool, true if path is blocked"""
		return (point in self._get_blocked_coords())

	def _get_position(self):
		"""Returns current position considering movement status and being in a building"""
		source = self.unit.position
		if self.unit.is_moving() and self.path:
			# we are moving, use next step as source
			source = Point(*self.path[self.cur])
		else:
			# check if we are in a building
			building = self.session.world.get_building(self.unit.position)
			if building is not None:
				source = building
		return source

	def calc_path(self, destination, destination_in_building=False, check_only=False,
	              source=None):
		"""Calculates a path to destination
		@param destination: a destination supported by pathfinding
		@param destination_in_building: bool, whether destination is in a building.
		                                this makes the unit "enter the building"
		@param check_only: if True the path isn't saved
		@param source: use this as source of movement instead of self.unit.position
		@return: True iff movement is possible or the path if check_only==True"""
		# calculate our source
		if source is None:
			source = self._get_position()

		# call algorithm
		# to use a different pathfinding code, just change the following line
		path = FindPath()(source, destination, self._get_path_nodes(),
											self._get_blocked_coords(), self.move_diagonal,
											self.make_target_walkable)

		if path is None:
			return False

		if not check_only:
			# prepare movement
			self.move_on_path(path, source, destination_in_building)
		else:
			return path

		return True

	def move_on_path(self, path, source=None, destination_in_building=False):
		"""Start moving on a precalculated path.
		@param path: return value of FindPath()()
		"""
		if source is None:
			source = self._get_position()
		self.path = path
		if self.unit.is_moving():
			self.cur = 0
			self.unit.show() # make sure unit is displayed
		else:
			self.cur = -1
		self.source_in_building = hasattr(source, 'is_building') and source.is_building
		self.destination_in_building = destination_in_building

	def get_next_step(self):
		"""Returns the next step in the current movement
		@return: Point"""
		if self.cur is None:
			return None

		self.cur += 1
		if not self.path or self.cur == len(self.path):
			# movement finished
			self.cur = None
			self.path = None
			return None

		if self._check_for_obstacles(self.path[self.cur]):
			# path is suddenly blocked, find another path
			self.cur -= 1 # reset, since move is not possible
			# try to calculate another path
			if not self.calc_path(Point(*self.path[-1]), self.destination_in_building):
				self.log.info("tile suddenly %s %s blocked for %s %s",
											self.path[self.cur][0], self.path[self.cur][1], self.unit, self.unit.worldid)
				# no other path can be found. since the problem cannot be fixed here,
				# we raise an exception
				raise PathBlockedError

		# check if we have to change visibility because of entering or leaving a building
		if self.destination_in_building and self.cur == len(self.path)-1:
			self.destination_in_building = False
			self.unit.hide()
		elif self.source_in_building and self.cur == 2:
			self.source_in_building = False
			self.unit.show()

		return Point(*self.path[self.cur])

	def get_move_source(self):
		"""Returns the source Point of the current movment.
		@return: Point or Non if no path has been calculated"""
		return None if not self.path else Point(*self.path[0])

	def get_move_target(self):
		"""Returns the point where the path leads
		@return: Point or None if no path has been calculated"""
		return None if not self.path else Point(*self.path[-1])

	def end_move(self):
		"""Pretends that the path is finished in order to make the unit stop"""
		del self.path[self.cur+1:]

	def save(self, db, unitid):
		# just save each step of the path
		# current position is calculated on loading through unit position
		if self.path:
			for step in xrange(len(self.path)):
				db("INSERT INTO unit_path(`unit`, `index`, `x`, `y`) VALUES(?, ?, ?, ?)",
					 unitid, step, self.path[step][0], self.path[step][1])

	def load(self, db, worldid):
		"""
		@return: Bool, whether a path was loaded
		"""
		path_steps = db.get_unit_path(worldid)
		if path_steps is None:
			return False
		else:
			self.path = path_steps
			cur_position = self.unit.position.to_tuple()
			if cur_position in self.path:
				self.cur = self.path.index(cur_position)
			else:
				self.cur = -1
			return True


class ShipPather(AbstractPather):
	"""Pather for ships (units that move on water tiles)"""
	def __init__(self, unit, *args, **kwargs):
		super(ShipPather, self).__init__(unit, move_diagonal=True,make_target_walkable = False,
		                                 *args, **kwargs)

	def _get_path_nodes(self):
		return self.session.world.water

	def _get_blocked_coords(self):
		return self.session.world.ship_map


class FisherShipPather(ShipPather):
	"""Can also drive through shallow water"""
	def _get_path_nodes(self):
		return self.session.world.water_and_coastline

	def _get_blocked_coords(self):
		# don't let fisher be blocked by other ships (#1023)
		return []


class BuildingCollectorPather(AbstractPather):
	"""Pather for collectors, that move freely (without depending on roads)
	within the radius of their home building such as farm animals."""
	def __init__(self, unit, *args, **kwargs):
		super(BuildingCollectorPather, self).__init__(unit, move_diagonal=True, *args, **kwargs)

	def _get_path_nodes(self):
		from horizons.component.collectingcomponent import CollectingComponent
		return self.unit.home_building.get_component(CollectingComponent).path_nodes.nodes


class RoadPather(AbstractPather):
	"""Pather for collectors, that depend on roads (e.g. the one used for the warehouse)"""
	def __init__(self, unit, *args, **kwargs):
		super(RoadPather, self).__init__(unit, move_diagonal=False, *args, **kwargs)
		self.island = self.session.world.get_island(unit.position)

	def _get_path_nodes(self):
		return self.island.path_nodes.road_nodes


class SoldierPather(AbstractPather):
	"""Pather for units, that move absolutely freely (such as soldiers)
	Their path list is maintained by IslandPathNodes"""
	def __init__(self, unit, *args, **kwargs):
		super(SoldierPather, self).__init__(unit, move_diagonal=True,
																				make_target_walkable=False, *args, **kwargs)

	def _get_path_nodes(self):
		# island might change (e.g. when transported via ship), so reload every time
		island = self.session.world.get_island(self.unit.position)
		return island.path_nodes.nodes

	def _get_blocked_coords(self):
		return self.session.world.ground_unit_map

	def _check_for_obstacles(self, point):
		# retrieve island, island of soldier may change at any time
		island = self.session.world.get_island(self.unit.position)
		path_blocked = not island.path_nodes.is_walkable(self.path[self.cur])
		if path_blocked:
			# update list in island, so that new path calculations consider this obstacle
			island.path_nodes.reset_tile_walkability(point)
			self.log.debug("tile %s %s blocked for %s %s on island", point[0], point[1],
										 self.unit, self.unit.worldid)
			return path_blocked
		else:
			# also check in super class
			return super(SoldierPather, self)._check_for_obstacles(point)


class StaticPather(object):
	"""Misc pathing routines not depending on units.
	Does not use AbstractPather Interface"""
	@classmethod
	def get_path_on_roads(cls, island, source, destination):
		"""Returns a path that runs only on roads.
		@param island: island to search path on
		@param source, destination: Point or anything supported by FindPath
		@return: list of tuples or None in case no path is found"""
		return FindPath()(source, destination, island.path_nodes.road_nodes)


decorators.bind_all(AbstractPather)
