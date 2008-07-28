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
from game.world.pathfinding import findPath, Movement
from game.util import Point, Rect
from game.util import WeakMethod
from game.util import WorldObject

class Unit(WorldObject):
	movement = Movement.SOLDIER_MOVEMENT

	def __init__(self, x, y, **kwargs):
		print self.__class__.__mro__
		super(Unit, self).__init__(x=x, y=y, **kwargs)
		class tmp(fife.InstanceActionListener): pass
		self.InstanceActionListener = tmp()
		self.InstanceActionListener.onInstanceActionFinished = WeakMethod(self.onInstanceActionFinished)
		if self._object is None:
			self.__class__._loadObject()
		self.object_type = 1
		self.last_unit_position = Point(x, y)
		self.unit_position = self.last_unit_position
		self.move_target = self.last_unit_position
		self.next_target = self.last_unit_position
		# use for changing path while moving:
		self.new_target = None
		self.new_callback = None

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

		self.path = None
		self.cur_path = None

		self.health = 60.0
		self.max_health = 100.0

		self.is_moving = False

	def __del__(self):
		self._instance.getLocationRef().getLayer().deleteInstance(self._instance)

	def start(self):
		pass

	def onInstanceActionFinished(self, instance, action):
		"""
		@param instance: fife.Instance
		@param action: string representing the action that is finished.
		"""
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.unit_position.x + self.unit_position.x - self.last_unit_position.x, self.unit_position.y + self.unit_position.y - self.last_unit_position.y, 0))
		self._instance.act(self.action, location, True)
		game.main.session.view.cam.refresh()

	def is_unit_moving(self):
		"""Returns wether unit is moving"""
		return self.is_moving

	def check_move(self, destination):
		"""Tries to find a path to destination
		@param destination: Point or Rect. if it's a Point that's in a building, the building is used as destination.
		"""
		diagonal = False
		blocked_coords = []
		if self.__class__.movement == Movement.SOLDIER_MOVEMENT:
			assert(isinstance(destination, Point)) # rect not yet supported here
			self.move_directly(destination)
			return
		elif self.__class__.movement == Movement.STORAGE_CARRIAGE_MOVEMENT:
			island = game.main.session.world.get_island(self.unit_position.x, self.unit_position.y)
			path_graph = island.path_nodes
		elif self.__class__.movement == Movement.CARRIAGE_MOVEMENT:
			path_graph = self.home_building().radius_coords
			diagonal = True
		elif self.__class__.movement == Movement.SHIP_MOVEMENT:
			path_graph = game.main.session.world.water
			blocked_coords = game.main.session.world.ship_map.keys()
			diagonal = True
		else:
			print self.id, 'has no Movement def'

		source = self.unit_position
		dest = destination

		island = game.main.session.world.get_island(self.unit_position.x, self.unit_position.y)
		if island is not None:
			b = island.get_building(self.unit_position.x, self.unit_position.y)
			if b is not None:
				source = b.building_position
			b = island.get_building(destination.x, destination.y)
			if b is not None and isinstance(destination, Point):
				dest = b.building_position

		return findPath(source, dest, path_graph, blocked_coords, diagonal)

	def do_move(self, path, callback = None):
		"""Conducts a move, that was previously calculated in check_move or specified as path.
		@param callback: function to call when unit arrives
		@param path: path to take. defaults to self.path
		If you just want to move a unit without checks, use move()
		"""

		if self.is_unit_moving():
			self.new_target = Point(path[-1])
			self.new_callback = callback
			return

		self.is_moving = True

		# setup move
		self.path = path
		self.move_callback = WeakMethod(callback)

		print 'MOVING FROM', path[0], 'TO', path[-1]

		self.cur_path = iter(self.path)
		self.next_target = self.cur_path.next()
		# findPath returns tuples, so we have to turn them into Point
		self.next_target = Point(self.next_target)

		# enqueue first move (move_tick takes care of the rest)
		game.main.session.scheduler.add_new_object(self.move_tick, self, 1)

	def move(self, destination, callback = None):
		""" Moves unit to destination
		@param destination: Point or Rect
		@param callback: function that gets called when the unit arrives
		@return: True if move is possible, else False
		"""
		path = self.check_move(destination)

		if path is None:
			return False

		self.do_move(path, callback)

		# move_target is deprecated, will be removed soon
		self.move_target = Point(path[-1])

		print self.id, 'MOVING TO', path[-1]

		return True

	def move_directly(self, destination):
		""" this is deprecated, do not use this.
		"""
		if self.next_target == self.unit_position:
			#calculate next target
			self.next_target = self.unit_position
			if self.move_target.x > self.unit_position.x:
				self.next_target = (self.unit_position.x + 1, self.next_target.y)
			elif self.move_target.x < self.unit_position.x:
				self.next_target = (self.unit_position.x - 1, self.next_target.y)
			if self.move_target.y > self.unit_position.y:
				self.next_target = (self.next_target.x, self.unit_position.y + 1)
			elif self.move_target.y < self.unit_position.y:
				self.next_target = (self.next_target.x, self.unit_position.y - 1)

			self.next_target = Point(self.next_target)

			#setup movement
			location = fife.Location(self._instance.getLocation().getLayer())
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target.x, self.next_target.y, 0))
			self._instance.move(self.action, location, 4.0/3.0)
			#setup next timer (12 ticks for horizontal or vertical move, 12*sqrt(2)==17 ticks for diagonal move)
			game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target.x == self.unit_position.x or self.next_target.y == self.unit_position.y else 17)
		else:
			self.movement_finished()

	def movement_finished(self):
		print self.id, 'MOVEMENT FINISHED'

		self.is_moving = False

		self.path = None
		self.cur_path = None
		self.next_target = self.unit_position

		# deprecated:
		self.move_target = self.unit_position

		if self.move_callback is not None:
			self.move_callback()

	def move_tick(self):
		"""Called by the scheduler, moves the unit one step for this tick.
		"""
		#sync unit_position
		self.last_unit_position = self.unit_position

		self.unit_position = self.next_target
		location = fife.Location(self._instance.getLocationRef().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.unit_position.x, self.unit_position.y, 0))
		self._instance.setLocation(location)

		if self.new_target != None:
			import time
			self.is_moving = False
			self.move(self.new_target, self.new_callback)
			self.new_target = None
			return

		# check if next_target is blocked by a unit
		## TODO: the location of this code might should be changed
		if not self.check_for_blocking_units(self.next_target):
			new_path = self.check_move(self.path[-1] )
			if new_path is None:
				# if there's no path now, just stop moving
				## TODO: if unit, that blocks us, belongs to our player, tell it to move
				return
			self.do_move(new_path, self.move_callback)
			return

		if self.unit_position != self.move_target:
			if self.__class__.movement == Movement.CARRIAGE_MOVEMENT or \
				 self.__class__.movement == Movement.STORAGE_CARRIAGE_MOVEMENT or \
				 self.__class__.movement == Movement.SHIP_MOVEMENT :
				# retrieve next target from already calculated path
				try:
					self.next_target = Point(self.cur_path.next())
				except StopIteration:
					self.movement_finished()
					return

			elif self.__class__.movement == Movement.SOLDIER_MOVEMENT:
				# this is deprecated, just like move_directly
				#calculate next target
				self.next_target = self.unit_position
				if self.move_target.x > self.unit_position.x:
					self.next_target = (self.unit_position.x + 1, self.next_target.y)
				elif self.move_target.x < self.unit_position.x:
					self.next_target = (self.unit_position.x - 1, self.next_target.y)
				if self.move_target.y > self.unit_position.y:
					self.next_target = (self.next_target.x, self.unit_position.y + 1)
				elif self.move_target.y < self.unit_position.y:
					self.next_target = (self.next_target.x, self.unit_position.y - 1)

				self.next_target = Point(self.next_target)
			#print self.id, 'MOVE_TICK TO', self.next_target

		else:
			self.movement_finished()
			return

		#setup movement

		# WORK IN PROGRESS
		#time_move_straight = self.get_unit_speed()

		# just until other bug is fixed
		time_move_straight = 12.0

		#print time_move_straight

		## IDEA:
		## add speed value to ground as float from 0.1 to 1.0 in db (ground or ground_class, ask spq)
		## add them to the class, not the instance (for speed & memory usage)
		## maybe create function in world get_speed_on(self, x, y) or query it here
		## multiply it to speed

		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target.x, self.next_target.y, 0))
		self._instance.move(self.action, location, 16.0 / time_move_straight)
		# coords pro sec

		#setup next timer
		# diagonal_move = straight_move * sqrt(2)
		ticks = int(time_move_straight) if self.next_target.x == self.unit_position.x or self.next_target.y == self.unit_position.y else int(time_move_straight*1.414)
		#print ticks

		game.main.session.scheduler.add_new_object(self.move_tick, self, ticks)

	def get_unit_speed(self):
		"""Returns number of ticks that it takes to do a vertical/horizontal movement
		@return: float
		"""
		if len(self.acceleration) > 0:
			len_path = len(path)
			pos_in_path = path.index(self.unit_position)
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
		pass
