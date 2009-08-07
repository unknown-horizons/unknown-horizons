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

import fife
import logging
import random

import horizons.main

from horizons.world.pathfinding import PathBlockedError
from horizons.util import Point, WeakMethodList, WorldObject, WeakMethod, Circle
from horizons.constants import LAYERS

class Unit(WorldObject):
	log = logging.getLogger("world.units")

	pather_class = None
	object_type = 1

	def __init__(self, x, y, owner=None, **kwargs):
		super(Unit, self).__init__(**kwargs)
		self.__init(x, y, owner)

	def __init(self, x, y, owner, health = 100.0):
		self.owner = owner
		self._action_set_id = horizons.main.db("SELECT action_set_id FROM data.action_set WHERE object_id=? order by random() LIMIT 1", self.id)[0][0]
		class tmp(fife.InstanceActionListener): pass
		self.InstanceActionListener = tmp()
		self.InstanceActionListener.onInstanceActionFinished = \
				WeakMethod(self.onInstanceActionFinished)
		if self._object is None:
			self.__class__._loadObject()
		self.position = Point(x, y)
		self.last_position = Point(x, y)
		self.next_target = Point(x, y)

		self._instance = horizons.main.session.view.layers[LAYERS.OBJECTS].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), str(self.getId()))
		fife.InstanceVisual.create(self._instance)
		self.action = 'idle'
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate( \
			self.position.x + self.position.x, \
			self.position.y + self.position.y, 0))
		self.act(self.action, location, True)
		self._instance.addActionListener(self.InstanceActionListener)

		self.move_callback = WeakMethodList()

		self.health = health
		self.max_health = 100.0

		self.__is_moving = False

		self.path = self.pather_class(self)

	def __del__(self):
		self._instance.removeActionListener(self.InstanceActionListener)
		if hasattr(self, "_instance") and \
			 self._instance.getLocationRef().getLayer() is not None:
			horizons.main.session.view.layers[LAYERS.OBJECTS].deleteInstance(self._instance)
			#self._instance.getLocationRef().getLayer().deleteInstance(self._instance)
		else:
			# only debug output here:
			if hasattr(self, "_instance"):
				self.log.warning('Unit %s has _instance without layer in __del__')

	def act(self, action, facing_loc=None, repeating=False):
		if facing_loc is None:
			facing_loc = self._instance.getFacingLocation()
		if not action in horizons.main.action_sets[self._action_set_id]:
			action = 'idle'
		self._instance.act(action+"_"+str(self._action_set_id), facing_loc, repeating)

	def start(self):
		pass

	def onInstanceActionFinished(self, instance, action):
		"""
		@param instance: fife.Instance
		@param action: string representing the action that is finished.
		"""
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate( \
			self.position.x + self.position.x - self.last_position.x, \
			self.position.y + self.position.y - self.last_position.y, 0))
		self.act(self.action, location, True)
		horizons.main.session.view.cam.refresh()

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
		The unit acctally stops moving when current move is finished.
		@param callback: a parameter supported by WeakMethodList. is executed immediately if unit isn't moving
		"""
		if not self.is_moving():
			WeakMethodList(callback).execute()
			return
		self.move_callback = WeakMethodList(callback)
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

		self.move_callback = WeakMethodList(callback)
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
			horizons.main.session.scheduler.add_new_object(self.move_tick, self)

		return True

	def move_back(self, callback = None, destination_in_building = False):
		"""Return to the place where last movement started. Same path is used, but in reverse order.
		@param callback: same as callback in move()
		@param destination_in_building: bool, wether target is in a building
		"""
		self.log.debug("Unit %s: Moving back")
		self.path.revert_path(destination_in_building)
		self.move_callback = WeakMethodList(callback)
		self.__is_moving = True
		self.move_tick()

	def movement_finished(self):
		self.log.debug("Unit %s: movement finished. calling callbacks %s", self.getId(), \
									 self.move_callback)
		self.next_target = self.position

		self.__is_moving = False

		self.move_callback.execute()

	def move_tick(self):
		"""Called by the scheduler, moves the unit one step for this tick.
		"""
		assert(self.next_target is not None)
		self.log.debug("Unit %s: move tick, moving to %s", self.getId(), self.next_target)
		self.last_position = self.position
		self.position = self.next_target
		self.log.debug('CrashMonitor: will get Layer')
		location = fife.Location(self._instance.getLocationRef().getLayer())
		self.log.debug('CrashMonitor: Location is %s', location)
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position.x, self.position.y, 0))
		self.log.debug('CrashMonitor: setting coords on location')
		self._instance.setLocation(location)
		self.log.debug('CrashMonitor: setting location')
		self._changed()

		# try to get next step, handle a blocked path
		while self.next_target == self.position:
			try:
				self.next_target = self.path.get_next_step()
			except PathBlockedError:
				self.__is_moving = False
				self.next_target = self.position
				if self.owner is not None and hasattr(self.owner, "notify_unit_path_blocked"):
					self.owner.notify_unit_path_blocked(self)
				else:
					print 'WARNING: unit %s %s has no owner and a blocked path!' % (self, self.getId())
				self.log.debug("Unit %s: path is blocked, no way around", self.getId())
				return

		if self.next_target is None:
			self.movement_finished()
			return
		else:
			self.__is_moving = True

		#setup movement

		# WORK IN PROGRESS
		move_time = self.get_unit_velocity()

		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target.x, self.next_target.y, 0))

		# FIXME: on loading, move() isn't called, and therefore _move_action isn't defined,
		#        which leads to a crash here. please fix this asap and remove following line!
		if not hasattr(self, "_move_action"): self._move_action = 'move'
		self._instance.move(self._move_action+"_"+str(self._action_set_id), location, 16.0 / move_time[0])
		# coords per sec

		diagonal = self.next_target.x != self.position.x and self.next_target.y != self.position.y
		horizons.main.session.scheduler.add_new_object(self.move_tick, self, move_time[int(diagonal)])

	def add_move_callback(self, callback):
		"""Registers callback to be executed when movement of unit finishes.
		This has no effect if the unit isn't moving."""
		if self.is_moving():
			self.move_callback.append(callback)

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

	def draw_health(self):
		"""Draws the units current health as a healthbar over the unit."""
		renderer = horizons.main.session.view.renderer['GenericRenderer']
		width = 50
		height = 5
		y_pos = -30
		mid_node_up = fife.GenericRendererNode(self._instance, \
									fife.Point(-width/2+int(((self.health/self.max_health)*width)),\
														 y_pos-height))
		mid_node_down = fife.GenericRendererNode(self._instance, \
									fife.Point(-width/2+int(((self.health/self.max_health)*width)),y_pos))
		if self.health != 0:
			renderer.addQuad("health_" + str(self.getId()), fife.GenericRendererNode(self._instance, fife.Point(-width/2, y_pos-height)), mid_node_up, mid_node_down, fife.GenericRendererNode(self._instance, fife.Point(-width/2, y_pos)), 0, 255, 0)
		if self.health != self.max_health:
			renderer.addQuad("health_" + str(self.getId()), mid_node_up, fife.GenericRendererNode(self._instance, fife.Point(width/2, y_pos-height)), fife.GenericRendererNode(self._instance, fife.Point(width/2, y_pos)), mid_node_down, 255, 0, 0)

	def hide(self):
		"""Hides the unit."""
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(False)

	def show(self):
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(True)

	def save(self, db):
		super(Unit, self).save(db)

		owner_id = 0 if self.owner is None else self.owner.getId()
		db("INSERT INTO unit (rowid, type, x, y, health, owner) VALUES(?, ?, ?, ?, ?, ?)",
			self.getId(), self.__class__.id, self.position.x, self.position.y, \
					self.health, owner_id)

		self.path.save(db, self.getId())

	def load(self, db, worldid):
		super(Unit, self).load(db, worldid)

		x, y, health, owner_id = db("SELECT x, y, health, owner FROM unit WHERE rowid = ?", worldid)[0]
		if (owner_id == 0):
			owner = None
		else:
			owner = WorldObject.get_object_by_id(owner_id)
		self.__init(x, y, owner, health)

		path_loaded = self.path.load(db, worldid)
		if path_loaded:
			self.__is_moving = True
			horizons.main.session.scheduler.add_new_object(self.move_tick, self, 1)
		return self

	def get_random_location(self, in_range):
		"""Returns a random location in walking_range, that we can find a path to
		@param in_range: int, max distance to returned point from current position
		@return: Instance of Point or None"""
		possible_walk_targets = Circle(self.position, in_range).get_coordinates()
		possible_walk_targets.remove(self.position.to_tuple())
		random.shuffle(possible_walk_targets)
		for coord in possible_walk_targets:
			target = Point(*coord)
			if self.check_move(target):
				return target
		return None

	def __str__(self): # debug
		classname = horizons.main.db("SELECT name FROM unit where id = ?", self.id)[0][0]
		# must not call getId if obj has no id, cause it changes the program
		worldid = None if not hasattr(self, '_WorldObject__id') else self.getId()
		return classname+'(id=%s;worldid=%s)' % (self.id, worldid)



