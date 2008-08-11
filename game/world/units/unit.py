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
import fife
from game.world.pathfinding import Pather, PathBlockedError, Movement
from game.util import Point, Rect, WeakMethodList, WorldObject, WeakMethod

class Unit(WorldObject):
	movement = Movement.SOLDIER_MOVEMENT

	def __init__(self, x, y, **kwargs):
		super(Unit, self).__init__(**kwargs)
		class tmp(fife.InstanceActionListener): pass
		self.InstanceActionListener = tmp()
		self.InstanceActionListener.onInstanceActionFinished = WeakMethod(self.onInstanceActionFinished)
		if self._object is None:
			self.__class__._loadObject()
		self.object_type = 1
		self.position = Point(x, y)
		self.last_position = Point(x, y)
		self.next_target = Point(x, y)

		self._instance = game.main.session.view.layers[2].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), str(self.getId()))
		fife.InstanceVisual.create(self._instance)
		self.action = 'default'
		self._instance.act(self.action, self._instance.getLocation(), True)
		self._instance.addActionListener(self.InstanceActionListener)

		self.move_callback = WeakMethodList()

		self.path = Pather(self)

		self.health = 60.0
		self.max_health = 100.0

		self.__is_moving = False

	def __del__(self):
		# the layer is sometimes deleted before the unit, therefore this check
		if self._instance.getLocationRef().getLayer() is not None:
			self._instance.getLocationRef().getLayer().deleteInstance(self._instance)

	def start(self):
		pass

	def onInstanceActionFinished(self, instance, action):
		"""
		@param instance: fife.Instance
		@param action: string representing the action that is finished.
		"""
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position.x + self.position.x - self.last_position.x, self.position.y + self.position.y - self.last_position.y, 0))
		self._instance.act(self.action, location, True)
		game.main.session.view.cam.refresh()

	def check_move(self, destination):
		"""Tries to find a path to destination
		@param destination: destination supported by findPath
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

	def move(self, destination, callback = None, destination_in_building = False):
		"""Moves unit to destination
		@param destination: Point or Rect
		@param callback: a parameter supported by WeakMethodList. Gets called when unit arrives.
		@return: True if move is possible, else False
		"""
		move_possible = self.path.calc_path(destination, destination_in_building)

		if not move_possible:
			return False

		print 'NEW DEST', destination
		self.move_callback = WeakMethodList(callback)

		if not self.is_moving():
			self.move_tick()

		return True

	def move_back(self, callback = None, destination_in_building = False):
		"""Return to the place where last movement started. Same path is used, but in reverse order.
		@param callback: same as callback in move()
		@param destination_in_building: bool, wether target is in a building
		"""
		self.path.revert_path(destination_in_building)
		self.move_callback = WeakMethodList(callback)
		self.__is_moving = True
		self.move_tick()

	def movement_finished(self):
		self.next_target = self.position

		self.__is_moving = False

		self.move_callback.execute()

	def move_tick(self):
		"""Called by the scheduler, moves the unit one step for this tick.
		"""
		assert(self.next_target is not None)
		self.last_position = self.position
		self.position = self.next_target
		location = fife.Location(self._instance.getLocationRef().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position.x, self.position.y, 0))
		self._instance.setLocation(location)

		while self.next_target == self.position:
			try:
				self.next_target = self.path.get_next_step()
			except PathBlockedError:
				self.__is_moving = False
				self.next_target = self.position
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
		self._instance.move(self.action, location, 16.0 / move_time[0])
		# coords pro sec

		diagonal = self.next_target.x != self.position.x and self.next_target.y != self.position.y
		game.main.session.scheduler.add_new_object(self.move_tick, self, move_time[int(diagonal)])

	def get_unit_velocity(self):
		"""Returns number of ticks that it takes to do a straight (i.e. vertical or horizontal) movement
		@return: int
		"""
		tile = game.main.session.world.get_tile(self.position)
		if tile.object is None:
			return tile.velocity[self.id]
		else:
			return tile.object.velocity[self.id]

	def check_for_blocking_units(self, position):
		"""Returns wether position is blocked by a unit
		@param position: instance of Point
		@return: True if position is clear, False if blocked
		"""
		return True
	
	def get_move_target(self):
		return self.path.get_move_target()
	
	def draw_health(self):
		"""Draws the units current health as a healthbar over the unit."""
		renderer = game.main.session.view.renderer['GenericRenderer']
		width = 50
		height = 5
		y_pos = -30
		mid_node_up = fife.GenericRendererNode(self._instance, fife.Point(-width/2+int(((self.health/self.max_health)*width)),y_pos-height))
		mid_node_down = fife.GenericRendererNode(self._instance, fife.Point(-width/2+int(((self.health/self.max_health)*width)),y_pos))
		if self.health != 0:
			renderer.addQuad("health_" + str(self.getId()), fife.GenericRendererNode(self._instance, fife.Point(-width/2,y_pos-height)), mid_node_up, mid_node_down, fife.GenericRendererNode(self._instance, fife.Point(-width/2,y_pos)), 0, 255, 0)
		if self.health != self.max_health:
			renderer.addQuad("health_" + str(self.getId()), mid_node_up, fife.GenericRendererNode(self._instance, fife.Point(width/2,y_pos-height)), fife.GenericRendererNode(self._instance, fife.Point(width/2,y_pos)), mid_node_down, 255, 0, 0)

	def hide(self):
		"""Hides the unit."""
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(False)

	def show(self):
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(True)

	def save(self, db):
		super(Unit, self).save(db)
		
		db("INSERT INTO unit (rowid, type, x, y, health, owner) VALUES(?, ?, ?, ?, ?, ?)",
			self.getId(), self.__class__.id, self.position.x, self.position.y, self.health, 0)
		
		self.path.save(db, self.getId())
		
		# TODO: owner


	def load(self, db, worldid):
		super(Unit, self).load(db, worldid)
		# HACK: Call bloated __init__, which is not a good idea, but saves me from copying tons of code for now
		# TODO: Implement location loading
		(x, y, health, owner) = db("SELECT x, y, health, owner FROM unit WHERE rowid = ?", worldid)[0]

		Unit.__init__(self, x, y)

		self.health = health


