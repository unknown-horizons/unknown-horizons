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

import weakref
from fife import fife

import horizons.main

from horizons.world.pathfinding.pather import SoldierPather
from horizons.world.pathfinding import PathBlockedError
from horizons.world.units.movingobject import MoveNotPossible
from horizons.util import Point, NamedObject, Circle, WorldObject
from unit import Unit
from horizons.constants import LAYERS, STORAGE, GAME_SPEED
from horizons.scheduler import Scheduler
from horizons.world.component.healthcomponent import HealthComponent

class GroundUnit(Unit):
	"""Class representing ground unit
	@param x: int x position
	@param y: int y position
	"""
	pather_class = SoldierPather
	tabs = ()
	enemy_tabs = ()
	health_bar_y = -70
	is_selectable = True

	def __init__(self, x, y, **kwargs):
		super(GroundUnit, self).__init__(x=x, y=y, **kwargs)
		self.session.world.ground_units.append(self)
		self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)
		self.add_component('health', HealthComponent)

	def remove(self):
		if self in self.session.selected_instances:
			self.deselect()
			self.session.selected_instances.remove(self)
		super(GroundUnit, self).remove()
		self.session.ground_units.remove(self)
		if self.session.view.has_change_listener(self.draw_health):
			self.session.view.remove_change_listener(self.draw_health)
		del self.session.world.ground_unit_map[self.position.to_tuple()]

	def _move_tick(self, resume = False):
		del self.session.world.ground_unit_map[self.position.to_tuple()]

		try:
			super(GroundUnit, self)._move_tick(resume)
		except PathBlockedError:
			# if we fail to resume movement then the ship should still be on the map but the exception has to be raised again.
			if resume:
				self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)
			raise

		self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)
		self.session.world.ground_unit_map[self._next_target.to_tuple()] = weakref.ref(self)

	def select(self, reset_cam=False):
		"""Runs necessary steps to select the unit."""
		self.session.view.renderer['InstanceRenderer'].addOutlined(self._instance, 255, 255, 255, 1)
		self.draw_health()
		if reset_cam:
			self.session.view.set_location(self.position.to_tuple())
		self.session.view.add_change_listener(self.draw_health)

	def deselect(self):
		"""Runs necessary steps to deselect the unit."""
		self.session.view.renderer['InstanceRenderer'].removeOutlined(self._instance)
		self.session.view.renderer['GenericRenderer'].removeAll("health_" + str(self.worldid))
		# this is necessary to make deselect idempotent
		if self.session.view.has_change_listener(self.draw_health):
			self.session.view.remove_change_listener(self.draw_health)

	def go(self, x, y):
		"""Moves the unit.
		This is called when a unit is selected and the right mouse button is pressed outside the ship"""
		self.stop()

		move_target = Point(int(round(x)), int(round(y)))
		try:
			self.move(move_target)
		except MoveNotPossible:
			# find a near tile to move to
			surrounding = Circle(move_target, radius=1)
			move_target = None
			# try with smaller circles, increase radius if smaller circle isn't reachable
			while surrounding.radius < 5:
				try:
					self.move(surrounding)
				except MoveNotPossible:
					surrounding.radius += 1
					continue
				# update actual target coord
				move_target = self.get_move_target()
				break

		if move_target is None: # can't move
			# TODO: give player some kind of feedback
			return

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)

		# register unit in world
		self.session.world.ground_units.append(self)
		self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)
