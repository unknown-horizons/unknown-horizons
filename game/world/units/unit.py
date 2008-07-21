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
from game.util import WorldObject

class Unit(WorldObject, fife.InstanceActionListener):
	movement = Movement.SOLDIER_MOVEMENT

	def __init__(self, x, y):
		if self._object is None:
			self.__class__._loadObject()
		self.object_type = 1
		self.last_unit_position = Point(x, y)
		self.unit_position = self.last_unit_position
		self.move_target = self.last_unit_position
		self.next_target = self.last_unit_position
		self._instance = game.main.session.view.layers[2].createInstance(self._object, fife.ModelCoordinate(int(x), int(y), 0), game.main.session.entities.registerInstance(self))
		fife.InstanceVisual.create(self._instance)
		self.action = 'default'
		self._instance.act(self.action, self._instance.getLocation(), True)
		super(Unit, self).__init__()
		self._instance.addActionListener(self)

		self.move_callback = None

		self.path = None
		self.cur_path = None

		self.health = 60.0
		self.max_health = 100.0

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

	def check_move(self, destination):
		""" Tries to find a path to destination
		@param destination: Point or Rect. if it's a Point that's in a building, the building is used as destination.
		"""
		diagonal = False
		if self.__class__.movement == Movement.SOLDIER_MOVEMENT:
			assert(isinstance(destination, Point)) # rect not yet supported here
			self.move_directly(destination)
			return
		elif self.__class__.movement == Movement.STORAGE_CARRIAGE_MOVEMENT:
			island = game.main.session.world.get_island(self.unit_position.x, self.unit_position.y)
			path_graph = island.path_nodes
		elif self.__class__.movement == Movement.CARRIAGE_MOVEMENT:
			path_graph = self.home_building.radius_coords
			diagonal = True
		elif self.__class__.movement == Movement.SHIP_MOVEMENT:
			path_graph = game.main.session.world.water
			diagonal = True
		else:
			print self.id, 'has no Movement def'

		source = self.unit_position
		dest = destination

		island = game.main.session.world.get_island(self.unit_position.x, self.unit_position.y)
		if island is not None:
			b = island.get_building(self.unit_position.x, self.unit_position.y)
			if b is not None:
				source = Rect(Point(b.x, b.y), b.size[0], b.size[1])
			b = island.get_building(destination.x, destination.y)
			if b is not None and isinstance(destination, Point):
				dest = Rect(Point(b.x, b.y), b.size[0], b.size[1])

		return findPath(source, dest, path_graph, diagonal)

	def do_move(self, path, callback = None):
		"""Conducts a move, that was previously calculated in check_move or specified as path.
		@param callback: function to call when unit arrives
		@param path: path to take. defaults to self.path
		If you just want to move a unit without checks, use move()
		"""

		# cancel current move

		## TODO: replace this quick and really hard-core dirty fix (dusmania..)
		from game.world.units.carriage import Carriage
		if not isinstance(self, Carriage):
			print self.id, 'removing move_tick for Carriages'
			game.main.session.scheduler.rem_call(self, self.move_tick)

		self.cur_path = None
		self.next_target = None
		self.move_target = None

		# setup move
		self.path = path
		self.move_callback = callback

		print 'MOVING FROM', path[0], 'TO', path[ len(path)-1 ]
		
		self.cur_path = iter(self.path)
		self.next_target = self.cur_path.next()
		# findPath returns tuples, so we have to turn them into Point
		self.next_target = Point(self.next_target)

		# enqueue first move (move_tick takes care of the rest)
		game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target.x == self.unit_position.x or self.next_target.y == self.unit_position.y else 17)
	
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
		self.move_target = Point(path[ len(path)-1 ])

		print self.id, 'MOVING TO', path[ len(path)-1 ]

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
			print self.next_target
			location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target.x, self.next_target.y, 0))
			self._instance.move(self.action, location, 4.0/3.0)
			#setup next timer (12 ticks for horizontal or vertical move, 12*sqrt(2)==17 ticks for diagonal move)
			game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target.x == self.unit_position.x or self.next_target.y == self.unit_position.y else 17)
		else:
			self.movement_finished()

	def movement_finished(self):
		#print [callback for callback in [object for object in game.main.session.scheduler.schedule] if game.main.session.scheduler.schedule[callback].class_instance == self ]

		print self.id, 'MOVEMENT FINISHED'
		self.path = None
		self.cur_path = None
		self.next_target = self.unit_position

		# deprecated:
		self.move_target = self.unit_position
		
		#print 'EXECUTING CALLBACK FOR', self, ':', self.move_callback
		if self.move_callback is not None:
			#print 'EXECUTING CALLBACK FOR', self, ':', self.move_callback
			self.move_callback()
			#print '</CALLBACK>'

	def move_tick(self):
		"""Called by the scheduler, moves the unit one step for this tick.
		"""
		#sync unit_position
		self.last_unit_position = self.unit_position
		self.unit_position = self.next_target
		location = fife.Location(self._instance.getLocationRef().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.unit_position.x, self.unit_position.y, 0))
		self._instance.setLocation(location)

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
		location = fife.Location(self._instance.getLocation().getLayer())
		location.setExactLayerCoordinates(fife.ExactModelCoordinate(self.next_target.x, self.next_target.y, 0))
		self._instance.move(self.action, location, 4.0/3.0)
		#setup next timer
		game.main.session.scheduler.add_new_object(self.move_tick, self, 12 if self.next_target.x == self.unit_position.x or self.next_target.y == self.unit_position.y else 17)

	def draw_health(self):
		"""Draws the units current health as a healthbar over the unit."""
		renderer = game.main.session.view.renderer['GenericRenderer']
		width = 50
		height = 5
		y_pos = -30
		mid_node_up = fife.GenericRendererNode(self._instance, fife.Point(-width/2+int(((self.health/self.max_health)*width)),y_pos-height))
		mid_node_down = fife.GenericRendererNode(self._instance, fife.Point(-width/2+int(((self.health/self.max_health)*width)),y_pos))
		if self.health != 0:
			renderer.addQuad(2, fife.GenericRendererNode(self._instance, fife.Point(-width/2,y_pos-height)), mid_node_up, mid_node_down, fife.GenericRendererNode(self._instance, fife.Point(-width/2,y_pos)), 0, 255, 0);
		if self.health != self.max_health:
			renderer.addQuad(2, mid_node_up, fife.GenericRendererNode(self._instance, fife.Point(width/2,y_pos-height)), fife.GenericRendererNode(self._instance, fife.Point(width/2,y_pos)), mid_node_down, 255, 0, 0);

	def hide(self):
		"""Hides the unit."""
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(False)

	def show(self):
		vis = self._instance.get2dGfxVisual()
		vis.setVisible(True)

