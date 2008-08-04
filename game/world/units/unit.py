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
from game.util import Point, Rect
from game.util import WeakMethod
from game.util import WorldObject

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

		self.time_move_straight = game.main.db("SELECT time_move_straight FROM data.unit WHERE rowid = ?", self.id)[0]
		self.acceleration = {}
		res = game.main.db("SELECT step, velocity_rate from data.unit_acceleration WHERE unit = ?", self.id)
		for (step, velocity_rate) in res:
			self.acceleration[step] = velocity_rate

		self.move_callback = None

		self.path = Pather(self)

		self.health = 60.0
		self.max_health = 100.0

		self.__is_moving = False

	def __del__(self):
		self._instance.getLocationRef().getLayer().deleteInstance(self._instance)

	def start(self):
		pass

	def onInstanceActionFinished(self, instance, action):
		"""
		@param instance: fife.Instance
		@param action: string representing the action that is finished.
		"""
		print 'NPOS',self.position
		print 'lPOS',self.last_position
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position.x + self.position.x - self.last_position.x, self.position.y + self.position.y - self.last_position.y, 0))
		self._instance.act(self.action, self._instance.getLocation(), True)
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

	def move(self, destination, callback = None, destination_in_building = False):
		"""Moves unit to destination
		@param destination: Point or Rect
		@param callback: function that gets called when the unit arrives
		@return: True if move is possible, else False
		"""

		move_possible = self.path.calc_path(destination, destination_in_building)

		if not move_possible:
			return False

		print 'NEW DEST', destination
		self.move_callback = None if callback is None else WeakMethod(callback)

		if not self.is_moving():
			game.main.session.scheduler.add_new_object(self.move_tick, self, 1)

		self.__is_moving = True

		return True

	def move_back(self, callback = None, destination_in_building = False):
		self.path.revert_path(destination_in_building)
		self.move_callback = callback
		self.__is_moving = True
		game.main.session.scheduler.add_new_object(self.move_tick, self, 1)

	def movement_finished(self):
		self.next_target = self.position

		self.__is_moving = False

		if self.move_callback is not None:
			self.move_callback()

	def move_tick(self):
		"""Called by the scheduler, moves the unit one step for this tick.
		"""
		assert(self.next_target is not None)
		self.last_position = self.position
		self.position = self.next_target
		location = fife.Location(self._instance.getLocationRef().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.position.x, self.position.y, 0))
		self._instance.setLocation(location)

		try:
			self.next_target = self.path.get_next_step()
		except PathBlockedError:
			return

		if self.next_target is None:
			self.movement_finished()
			return

		#setup movement

		# WORK IN PROGRESS
		#time_move_straight = self.get_unit_speed()
		time_move_straight = 12.0

		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target.x, self.next_target.y, 0))
		self._instance.move(self.action, location, 16.0 / time_move_straight)
		# coords pro sec

		#setup next timer
		# diagonal_move = straight_move * sqrt(2)
		ticks = int(time_move_straight) if self.next_target.x == self.position.x or self.next_target.y == self.position.y else int(time_move_straight*1.414)

		game.main.session.scheduler.add_new_object(self.move_tick, self, ticks)

	def get_unit_speed(self):
		"""Returns number of ticks that it takes to do a vertical/horizontal movement
		@return: float
		"""
		if len(self.acceleration) > 0:
			len_path = len(path)
			pos_in_path = path.index(self.position)
			accelerations = [ accel  for step, accel in self.acceleration.items() if step == pos_in_path or step == pos_in_path - len_path ]
			if len(accelerations) > 0:
				return self.time_move_straight * max(accelerations)
		return self.time_move_straight

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

		# TODO: save owner
		db("INSERT INTO unit (rowid, type, x, y, health, owner) VALUES(?, ?, ?, ?, ?, ?)",
			self.getId(), self.__class__.id, self.position.x, self.position.y, self.health, 0)
		# max_health was skipped because i guess it will be read from somewhere

		# TODO (not necessarily necessary):
		# - actionlistener
		# - self._object
		# - self._instance

		# movement-code will be moved, don't save it here!

	def load(self, db, worldid):
		super(Unit, self).load(db, worldid)
		# HACK: Call bloated __init__, which is not a good idea, but saves me from copying tons of code for now
		# TODO: Implement location loading
		(x, y, health, owner) = db("SELECT x, y, health, owner FROM unit WHERE rowid = ?", worldid)[0]

		Unit.__init__(self, x, y)

		self.health = health




