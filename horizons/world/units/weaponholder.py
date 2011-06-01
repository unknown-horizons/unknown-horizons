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
from horizons.util import Annulus, Callback
from horizons.world.units.movingobject import MoveNotPossible
from horizons.scheduler import Scheduler
from horizons.util.changelistener import metaChangeListenerDecorator

import gc

@metaChangeListenerDecorator("storage_modified")
class WeaponHolder(object):
	def __init__(self, **kwargs):
		super(WeaponHolder, self).__init__(**kwargs)
		self.__init()
	
	def __init(self):
		self.create_weapon_storage()
		self._target = None
		self.add_storage_modified_listener(self.update_range)
	
	def create_weapon_storage(self):
		self._weapon_storage = []

	def update_range(self, caller=None):
		self._min_range = min([w.get_minimum_range() for w in self._weapon_storage])
		self._max_range = max([w.get_maximum_range() for w in self._weapon_storage])

	def add_weapon_to_storage(self, weapon):
		self._weapon_storage.append(weapon)
		self.on_storage_modified()

	def attack_possible(self, dest):
		distance = self.position.distance_to_point(dest)
		for weapon in self._weapon_storage:
			if weapon.check_target_in_range(distance):
				return True
		return False

	def try_attack_target(self):
		if self._target is None:
			return

		print self._target,'has health:',self._target.health

		dest = self._target.position.center()

		self.fire_all_weapons(dest)
		#try another attack in 2 ticks
		Scheduler().add_new_object(self.try_attack_target, self, 2)

	def attack(self, target):
		if self._target is not None:
			if self._target is not target:
			#if target is changed remove the listener
				if self._target.has_remove_listener(self.remove_target):
					self._target.remove_remove_listener(self.remove_target)
			else:
			#else do not update the target
				return
		if not target.has_remove_listener(self.remove_target):
			target.add_remove_listener(self.remove_target)
		self._target = target
		self.try_attack_target()

	def remove_target(self):
		#NOTE test code if the unit is really dead
		if self._target is not None:
			target_ref = weakref.ref(self._target)
			def check_target_ref(target_ref):
				if target_ref() is None:
					print "Z's dead baby, Z's dead"
					return
				import gc
				print target_ref(), 'has refs:'
				gc.collect()
				for ref in gc.get_referrers(target_ref()):
					print ref
			Scheduler().add_new_object(Callback(check_target_ref,target_ref), self, 3)
		self._target = None

	def stop_attack(self):
		#when the ship is told to move, the target is None and the listeners in target removed
		#TODO make another listener for target_changed
		if self._target is not None:
			if self._target.has_remove_listener(self.remove_target):
				self._target.remove_remove_listener(self.remove_target)
		self.remove_target()


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
