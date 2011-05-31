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
from horizons.util import Annulus, Callback, Circle, Rect
from horizons.world.units.movingobject import MoveNotPossible
from horizons.scheduler import Scheduler

class WeaponHolder(object):
	def __init__(self, **kwargs):
		super(WeaponHolder, self).__init__(**kwargs)
		self.__init()
	
	def __init(self):
		self.create_weapon_storage()
		self._target = None
	
	def create_weapon_storage(self):
		self._weapon_storage = []

	def add_weapon_to_storage(self, weapon):
		self._weapon_storage.append(weapon)
		#NOTE this should be done everytime the storage is changed
		self._min_range = min([w.get_minimum_range() for w in self._weapon_storage])
		self._max_range = max([w.get_maximum_range() for w in self._weapon_storage])

	def attack_possible(self, dest):
		distance = self.position.distance_to_point(dest)
		for weapon in self._weapon_storage:
			if weapon.check_target_in_range(distance):
				return True
		return False

	def try_attack_target(self):
		if self._target:
			target = self._target()
		else:
			return
		if not target:
			self._target = None
			print 'TARGET IS NONE'
			return

		#TODO optimise that
		dest = target.position
		if isinstance(dest, Rect):
			dest = dest.center()
		elif isinstance(dest, Circle):
			dest = dest.center

		self.fire_all_weapons(dest)
		#try another attack in 2 ticks
		Scheduler().add_new_object(self.try_attack_target, self, 2)

	def attack(self, target):
		if self._target is target:
			return
		self.stop_attack()
		self._target = weakref.ref(target)
		self.try_attack_target()

	def stop_attack(self):
		self._target = None

	def fire_all_weapons(self, dest):
		#fires all weapons at a given position
		if self.is_moving:
			self.stop()
		in_range = False
		distance = self.position.distance(dest)
		if distance >= self._min_range and distance <= self._max_range:
			for weapon in self._weapon_storage:
				weapon.fire(dest, distance)
			in_range = True
			print 'firing from', self

		if not in_range:
			if self.movable:
				try:
					self.move(Annulus(dest, self._min_range, self._max_range), Callback(self.fire_all_weapons, dest),
						blocked_callback = Callback(self.fire_all_weapons, dest))
				except MoveNotPossible:
					pass
