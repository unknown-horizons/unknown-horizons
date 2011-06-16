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

import logging
from fife import fife

import horizons.main
from horizons.scheduler import Scheduler

from horizons.world.pathfinding import PathBlockedError
from horizons.util import Point, WeakMethodList, decorators
from horizons.world.concreteobject import ConcretObject
from horizons.constants import GAME_SPEED

class MoveNotPossible(Exception):
	"""Gets thrown when the unit should move some where, but there is no possible path"""
	pass

class MovingObject(ConcretObject):
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
	movable = True

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
		self.blocked_callbacks = WeakMethodList()
		self._conditional_callbacks = {}

		self.__is_moving = False

		self.path = self.pather_class(self, session=self.session)

	def check_move(self, destination):
		"""Tries to find a path to destination
		@param destination: destination supported by pathfinding
		@return: object that can be used in boolean expressions (the path in case there is one)
		"""
		return self.path.calc_path(destination, check_only = True)

	def is_moving(self):
		"""Returns whether unit is currently moving"""
		return self.__is_moving

	def stop(self, callback = None):
		"""Stops a unit with currently no possibility to continue the movement.
		The unit actually stops moving when current move (to the next coord) is finished.
		@param callback: a parameter supported by WeakMethodList. is executed immediately if unit isn't moving
		"""
		if not self.is_moving():
			WeakMethodList(callback).execute()
			return
		self.move_callbacks = WeakMethodList(callback)
		self.path.end_move()

	def _setup_move(self, action='move'):
		"""Executes necessary steps to begin a movement. Currently only the action is set."""
		# try a number of actions and use first existent one
		for action_iter in (action, 'move', self._action):
			if self.has_action(action_iter):
				self._move_action = action_iter
				return
		# this case shouldn't happen, but no other action might be available (e.g. ships)
		self._move_action = 'idle'

	def move(self, destination, callback = None, destination_in_building = False, action='move', \
	         _path_calculated = False, blocked_callback = None, path = None):
		"""Moves unit to destination
		@param destination: Point or Rect
		@param callback: a parameter supported by WeakMethodList. Gets called when unit arrives.
		@param action: action as string to use for movement
		@param _path_calculated: only for internal use
		@param blocked_callback: a parameter supported by WeakMethodList. Gets called when unit gets blocked.
		@param path: a precalculated path (return value of FindPath()())
		"""
		if not _path_calculated and not path:
			# calculate the path
			move_possible = self.path.calc_path(destination, destination_in_building)

			self.log.debug("%s: move to %s; possible: %s; is_moving: %s", self, \
			               destination, move_possible, self.is_moving())

			if not move_possible:
				raise MoveNotPossible

		if path:
			self.path.move_on_path(path, destination_in_building=destination_in_building)

		self.move_callbacks = WeakMethodList(callback)
		self.blocked_callbacks = WeakMethodList(blocked_callback)
		self._conditional_callbacks = {}
		self._setup_move(action)

		# start moving by regular ticking (only if next tick isn't scheduled)
		if not self.is_moving():
			self.__is_moving = True
			# start moving in 1 tick
			# this assures that a movement takes at least 1 tick, which is sometimes subtly
			# assumed e.g. in the collector code
			Scheduler().add_new_object(self._move_tick, self)

	def move_back(self, callback = None, destination_in_building = False, action='move', blocked_callback = None):
		"""Return to the place where last movement started. Same path is used, but in reverse order.
		@param callback: same as callback in move()
		@param destination_in_building: bool, whether target is in a building
		@param blocked_callback: same as blocked_callback in move()
		"""
		self.log.debug("%s: Moving back to %s", self, self.get_move_target())
		self.path.revert_path(destination_in_building)
		self.move(None, callback, destination_in_building, action, _path_calculated = True, blocked_callback = blocked_callback)

	def _movement_finished(self):
		self.log.debug("%s: movement finished. calling callbacks %s", self, self.move_callbacks)
		self._next_target = self.position
		self.__is_moving = False
		self.move_callbacks.execute()

	@decorators.make_constants()
	def _move_tick(self, resume = False):
		"""Called by the scheduler, moves the unit one step for this tick.
		"""
		assert self._next_target is not None

		if resume:
			self.__is_moving = True
		else:
			#self.log.debug("%s move tick from %s to %s", self, self.last_position, self._next_target)
			self.last_position = self.position
			self.position = self._next_target
			location = fife.Location(self._instance.getLocationRef().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position.x, self.position.y, 0))
			# it's safe to use location here (thisown is 0, set by swig, and setLocation uses reference)
			self._instance.setLocation(location)
			self._changed()

		# try to get next step, handle a blocked path
		while self._next_target == self.position:
			try:
				self._next_target = self.path.get_next_step()
			except PathBlockedError:
				# if we are trying to resume and it isn't possible then we need to raise it again
				if resume:
					raise

				self.log.debug("path is blocked")
				self.log.debug("owner: %s", self.owner)
				self.__is_moving = False
				self._next_target = self.position
				if self.blocked_callbacks:
					self.log.warning('PATH FOR UNIT %s is blocked. Calling blocked_callback', self)
					self.blocked_callbacks.execute()
				elif self.owner is not None and hasattr(self.owner, "notify_unit_path_blocked"):
					self.log.warning('PATH FOR UNIT %s is blocked. Delegating to owner %s', self, self.owner)
					self.owner.notify_unit_path_blocked(self)
				else:
					# generic solution: retry in 2 secs
					self.log.warning('PATH FOR UNIT %s is blocked. Retry in 2 secs', self)
					Scheduler().add_new_object(self._move_tick, self, \
					                           GAME_SPEED.TICKS_PER_SECOND * 2)
				self.log.debug("Unit %s: path is blocked, no way around", self)
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

		# it's safe to use location here (thisown is 0, set by swig, and setLocation uses reference)
		self._instance.move(self._move_action+"_"+str(self._action_set_id), location, \
												float(self.session.timer.get_ticks(1)) / move_time[0])
		# coords per sec

		diagonal = self._next_target.x != self.position.x and self._next_target.y != self.position.y
		#self.log.debug("%s registering move tick in %s ticks", self, move_time[int(diagonal)])
		Scheduler().add_new_object(self._move_tick, self, move_time[int(diagonal)])

		# check if a conditional callback becomes true
		for cond in self._conditional_callbacks.keys(): # iterate of copy of keys to be able to delete
			if cond():
				# start callback when this function is done
				Scheduler().add_new_object(self._conditional_callbacks[cond], self)
				del self._conditional_callbacks[cond]

	def add_move_callback(self, callback):
		"""Registers callback to be executed when movement of unit finishes.
		This has no effect if the unit isn't moving."""
		if self.is_moving():
			self.move_callbacks.append(callback)

	def add_blocked_callback(self, blocked_callback):
		"""Registers callback to be executed when movement of the unit gets blocked."""
		self.blocked_callbacks.append(blocked_callback)

	def add_conditional_callback(self, condition, callback):
		"""Adds a callback, that gets called, if, at any time of the movement, the condition becomes
		True. The condition is checked every move_tick. After calling the callback, it is removed."""
		assert callable(condition)
		assert callable(callback)
		self._conditional_callbacks[condition] = callback

	def get_unit_velocity(self):
		"""Returns number of ticks that it takes to do a straight (i.e. vertical or horizontal) movement
		@return: int
		"""
		tile = self.session.world.get_tile(self.position)
		if self.id in tile.velocity:
			return tile.velocity[self.id]
		else:
			return (12, 17) # standard values

	def get_move_target(self):
		return self.path.get_move_target()

	def save(self, db):
		super(MovingObject, self).save(db)
		# NOTE: _move_action is currently not yet saved and neither is blocked_callback.
		self.path.save(db, self.worldid)

	def load(self, db, worldid):
		super(MovingObject, self).load(db, worldid)
		x, y = db("SELECT x, y FROM unit WHERE rowid = ?", worldid)[0]
		self.__init(x, y)
		path_loaded = self.path.load(db, worldid)
		if path_loaded:
			self.__is_moving = True
			self._setup_move()
			Scheduler().add_new_object(self._move_tick, self, 1)

