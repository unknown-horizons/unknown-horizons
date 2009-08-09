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

import logging
import fife

import horizons.main

from horizons.world.pathfinding import PathBlockedError
from horizons.util import Point, WeakMethodList

class MovingObject(object):
	"""This class provides moving functionality and is to be inherited by Unit.
	Its purpose is to provide a cleaner division of the code.

	It provides:
	*attributes:
	- position, last_position: Point
	- path: Pather

	*moving methods:
	- move
	- stop
	- move_back
	- add_move_callback

	*getters/checkers:
	- check_move
	- get_move_target
	- is_moving
	"""
	log = logging.getLogger("world.units")

	pather_class = None # overwrite this with a descendant of AbstractPather

	def __init__(self, x, y, **kwargs):
		super(MovingObject, self).__init__(x=x, y=y, **kwargs)
		self.__init(x, y)

	def __init(self, x, y):
		self.position = Point(x, y)
		self.last_position = Point(x, y)
		self._next_target = Point(x, y)

		self.move_callbacks = WeakMethodList()

		self.__is_moving = False

		self.path = self.pather_class(self)

	def check_move(self, destination):
		"""Tries to find a path to destination
		@param destination: destination supported by pathfinding
		@param destination_in_building: bool, wether unit should enter building
		"""
		return self.path.calc_path(destination, check_only = True)

	def is_moving(self):
		"""Returns wether unit is currently moving"""
		return self.__is_moving

	def stop(self, callback = None):
		"""Stops a unit with currently no possibility to continue the movement.
		The unit acctally stops moving when current move (to the next coord) is finished.
		@param callback: a parameter supported by WeakMethodList. is executed immediately if unit isn't moving
		"""
		if not self.is_moving():
			WeakMethodList(callback).execute()
			return
		self.move_callbacks = WeakMethodList(callback)
		self.path.end_move()

	def move(self, destination, callback = None, destination_in_building = False, action='move'):
		"""Moves unit to destination
		@param destination: Point or Rect
		@param callback: a parameter supported by WeakMethodList. Gets called when unit arrives.
		@return: True if move is possible, else False
		"""
		# calculate the path
		move_possible = self.path.calc_path(destination, destination_in_building)

		self.log.debug("Unit %s: move to %s; possible: %s", self.getId(), destination, move_possible)

		if not move_possible:
			return False

		self.move_callbacks = WeakMethodList(callback)
		if action in horizons.main.action_sets[self._action_set_id].keys():
			self._move_action = action
		elif 'move' in horizons.main.action_sets[self._action_set_id].keys():
			self._move_action = 'move'
		else:
			self._move_action = self.action

		# start moving by regular ticking (only if next tick isn't scheduled)
		if not self.is_moving():
			# start moving in 1 tick
			# this assures that a movement takes at least 1 tick, which is sometimes subtly
			# assumed e.g. in the collector code
			horizons.main.session.scheduler.add_new_object(self._move_tick, self)

		return True

	def move_back(self, callback = None, destination_in_building = False):
		"""Return to the place where last movement started. Same path is used, but in reverse order.
		@param callback: same as callback in move()
		@param destination_in_building: bool, wether target is in a building
		"""
		self.log.debug("Unit %s: Moving back")
		self.path.revert_path(destination_in_building)
		self.move_callbacks = WeakMethodList(callback)
		self.__is_moving = True
		self._move_tick()

	def _movement_finished(self):
		self.log.debug("Unit %s: movement finished. calling callbacks %s", self.getId(), \
									 self.move_callbacks)
		self._next_target = self.position

		self.__is_moving = False

		self.move_callbacks.execute()

	def _move_tick(self):
		"""Called by the scheduler, moves the unit one step for this tick.
		"""
		assert(self._next_target is not None)
		self.log.debug("Unit %s: move tick, moving to %s", self.getId(), self._next_target)
		self.last_position = self.position
		self.position = self._next_target
		self.log.debug('CrashMonitor: will get Layer')
		location = fife.Location(self._instance.getLocationRef().getLayer())
		self.log.debug('CrashMonitor: Location is %s', location)
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position.x, self.position.y, 0))
		self.log.debug('CrashMonitor: setting coords on location')
		self._instance.setLocation(location)
		self.log.debug('CrashMonitor: setting location')
		self._changed()

		# try to get next step, handle a blocked path
		while self._next_target == self.position:
			try:
				self._next_target = self.path.get_next_step()
			except PathBlockedError:
				self.__is_moving = False
				self._next_target = self.position
				if self.owner is not None and hasattr(self.owner, "notify_unit_path_blocked"):
					self.owner.notify_unit_path_blocked(self)
				else:
					print 'WARNING: unit %s %s has no owner and a blocked path!' % (self, self.getId())
				self.log.debug("Unit %s: path is blocked, no way around", self.getId())
				return

		if self._next_target is None:
			self._movement_finished()
			return
		else:
			self.__is_moving = True

		#setup movement

		# WORK IN PROGRESS
		move_time = self.get_unit_velocity()

		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self._next_target.x, self._next_target.y, 0))

		# FIXME: on loading, move() isn't called, and therefore _move_action isn't defined,
		#        which leads to a crash here. please fix this asap and remove following line!
		if not hasattr(self, "_move_action"):
			self._move_action = 'move'
		self._instance.move(self._move_action+"_"+str(self._action_set_id), location, 16.0 / move_time[0])
		# coords per sec

		diagonal = self._next_target.x != self.position.x and self._next_target.y != self.position.y
		horizons.main.session.scheduler.add_new_object(self._move_tick, self, move_time[int(diagonal)])

	def add_move_callback(self, callback):
		"""Registers callback to be executed when movement of unit finishes.
		This has no effect if the unit isn't moving."""
		if self.is_moving():
			self.move_callbacks.append(callback)

	def get_unit_velocity(self):
		"""Returns number of ticks that it takes to do a straight (i.e. vertical or horizontal) movement
		@return: int
		"""
		tile = horizons.main.session.world.get_tile(self.position)
		if self.id in tile.velocity:
			return tile.velocity[self.id]
		else:
			return (12, 17) # standard values

	def get_move_target(self):
		return self.path.get_move_target()

	def save(self, db):
		self.path.save(db, self.getId())

	def load(self, db, worldid):
		path_loaded = self.path.load(db, worldid)
		if path_loaded:
			self.__is_moving = True
			horizons.main.session.scheduler.add_new_object(self._move_tick, self, 1)

