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
from horizons.util import Annulus, Point, Callback
from horizons.world.units.movingobject import MoveNotPossible
from horizons.scheduler import Scheduler
from horizons.util.changelistener import metaChangeListenerDecorator
from weapon import Weapon, StackableWeapon, SetStackableWeaponNumberError
from horizons.constants import WEAPONS, GAME_SPEED

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
		self.attack_actions = ['attack_left_as_huker0', 'attack_right_as_huker0']

	def remove(self):
		self.remove_storage_modified_listener(self.update_range)
		for weapon in self._weapon_storage:
			weapon.remove_attack_ready_listener(Callback(self._add_to_fireable, weapon))
			weapon.remove_weapon_fired_listener(Callback(self._remove_from_fireable, weapon))
		super(WeaponHolder, self).remove()

	def create_weapon_storage(self):
		self._weapon_storage = []
		self._fireable = []

	def update_range(self, caller=None):
		self._min_range = min([w.get_minimum_range() for w in self._weapon_storage])
		self._max_range = max([w.get_maximum_range() for w in self._weapon_storage])

	def _add_to_fireable(self, weapon):
		"""
		Callback executed when weapon attack is ready
		"""
		self._fireable.append(weapon)

	def _remove_from_fireable(self, weapon):
		"""
		Callback executed when weapon is fired
		"""
		# remove in the next tick
		Scheduler().add_new_object(Callback(self._fireable.remove, weapon), self)

	def add_weapon_to_storage(self, weapon_id):
		"""
		adds weapon to storage
		@param weapon_id : id of the weapon to be added
		"""
		#if weapon is stackable, try to stack
		weapon = None
		if self.session.db.get_weapon_stackable(weapon_id):
			stackable = [w for w in self._weapon_storage if self.session.db.get_weapon_stackable(weapon_id)]
			#try to increase the number of weapons for one stackable weapon
			increased = False
			for weapon in stackable:
				try:
					weapon.increase_number_of_weapons(1)
					increased = True
					break
				except SetStackableWeaponNumberError:
					continue

			if not increased:
				weapon = StackableWeapon(self.session, weapon_id)
		else:
			weapon = Weapon(self.session, weapon_id)
		if weapon:
			self._weapon_storage.append(weapon)
			weapon.add_weapon_fired_listener(Callback(self._remove_from_fireable, weapon))
			weapon.add_attack_ready_listener(Callback(self._add_to_fireable, weapon))
			self._fireable.append(weapon)
		self.on_storage_modified()

	def remove_weapon_from_storage(self, weapon_id):
		"""
		removes weapon to storage
		@param weapon_id : id of the weapon to be removed
		"""
		weapons = [w for w in self._weapon_storage if w.weapon_id == weapon_id]
		if len(weapons) == 0:
			return
		#remove last weapon added
		weapon = weapons[-1]
		#
		remove_from_storage = False
		#if stackable weapon needs to be removed try decrease number
		if self.session.db.get_weapon_stackable(weapon_id):
			try:
				weapon.decrease_number_of_weapons(1)
			except SetStackableWeaponNumberError:
				remove_from_storage = True
		else:
			remove_from_storage = True

		if remove_from_storage:
			self._weapon_storage.remove(weapon)
			weapon.remove_weapon_fired_listener(Callback(self._remove_from_fireable, weapon))
			weapon.remove_attack_ready_listener(Callback(self._add_to_fireable, weapon))
			try:
				self._fireable.remove(weapon)
			except ValueError:
				pass

		self.on_storage_modified()

	def attack_in_range(self):
		if not self._target:
			return
		distance = self.position.distance(self._target.position.center())
		if distance >= self._min_range and distance <= self._max_range:
			return True
		return False

	def _move_and_attack(self, destination, not_possible_action = None, callback = None):
		"""
		Callback for moving to a destination, then attack
		@param destination : moving destination
		@param not_possible_action : execute if MoveNotPossible is thrown
		@param callback : execute after setting up movement
		"""
		if not_possible_action:
			assert callable(not_possible_action)
		if callback:
			assert callable(callback)

		try:
			self.move(destination, callback = self.try_attack_target,
				blocked_callback = self.try_attack_target)
			if callback:
				callback()
		except MoveNotPossible:
			if not_possible_action:
				not_possible_action()

	def try_attack_target(self):
		"""
		Attacking loop
		"""
		if self._target is None:
			return

		if hasattr(self._target, 'health'):
			print self._target,'has health:',self._target.health.health

		if not self.attack_in_range():
			if self.movable:
				destination = Annulus(self._target.position.center(), self._min_range, self._max_range)
				not_possible_action = self.stop_attack
				# if target passes near self, attack!
				callback = Callback(self.add_conditional_callback, self.attack_in_range, self.try_attack_target)
				# if executes attack action try to move in 1 seconds
				if self._instance.getCurrentAction().getId() in self.attack_actions:
					Scheduler().add_new_object(Callback(self._move_and_attack, destination, not_possible_action, callback),
						self, GAME_SPEED.TICKS_PER_SECOND)
				else:
					self._move_and_attack(destination, not_possible_action, callback)
		else:
			if self.movable and self.is_moving() and self._fireable:
				self.stop()

			distance = self.position.distance(self._target.position)
			dest = self._target.position.center()
			if self._target.movable and self._target.is_moving():
				dest = self._target._next_target

			self.fire_all_weapons(dest)

			if self.movable and distance > self._min_range:
				# get closer
				destination = Annulus(dest, self._min_range, int(self._min_range + (distance - self._min_range)/2))
				if self._instance.getCurrentAction().getId() in self.attack_actions:
					Scheduler().add_new_object(Callback(self._move_and_attack, destination),
						self, GAME_SPEED.TICKS_PER_SECOND)
				else:
					self._move_and_attack(destination)
			else:
				# try in another second (weapons shouldn't be fired more often than that)
				Scheduler().add_new_object(self.try_attack_target, self, GAME_SPEED.TICKS_PER_SECOND)

	def attack(self, target):
		"""
		Triggers attack on target
		@param target : target to be attacked
		"""
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
		"""
		Removes refference from target,
		this happens when the attack is stopped or the target is dead
		either way the refs are checked using gc module
		this is used because after unit death it's possbile that it still has refs
		"""
		if self._target is not None:
			#NOTE test code if the unit is really dead
			# weakref the target, collect the garbage, than check in 3 ticks if it was really removed
			# weakref call should return none in that case
			target_ref = weakref.ref(self._target)
			def check_target_ref(target_ref):
				if target_ref() is None:
					print "Z's dead baby, Z's dead"
					return
				import gc
				print target_ref(), 'has refs:'
				gc.collect()
				gc.collect()
				import pprint
				for ref in gc.get_referrers(target_ref()):
					pprint.pprint(ref)
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
		"""
		Fires all weapons in storage at a given position
		@param dest : Point with the given position
		"""

		if not self._fireable:
			return
		distance = self.position.distance(dest)
		for weapon in self._fireable:
			weapon.fire(dest, distance)

	def save(self, db):
		super(WeaponHolder, self).save(db)
		weapons = {}
		for weapon in self._weapon_storage:
			number = 1
			if self.session.db.get_weapon_stackable(weapon.weapon_id):
				number = weapon.number_of_weapons
			if weapon.weapon_id in weapons:
				weapons[weapon.weapon_id] += number
			else:
				weapons[weapon.weapon_id] = number

		for weapon_id in weapons:
			db("INSERT INTO weapon_storage(owner_id, weapon_id, number) VALUES(?, ?, ?)",
				self.worldid, weapon_id, weapons[weapon_id])

	def load(self, db, worldid):
		super(WeaponHolder, self).load(db, worldid)
		self.__init()
		weapons = db("SELECT weapon_id, number FROM weapon_storage WHERE owner_id = ?", worldid)
		for weapon_id, number in weapons:
			for i in xrange(number):
				self.add_weapon_to_storage(weapon_id)

