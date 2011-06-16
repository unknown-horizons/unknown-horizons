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
from weapon import Weapon, StackableWeapon, SetStackableWeaponNumberError
from horizons.constants import WEAPONS

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

	def remove(self):
		self.remove_storage_modified_listener(self.update_range)
		super(WeaponHolder, self).remove()

	def create_weapon_storage(self):
		self._weapon_storage = []

	def update_range(self, caller=None):
		self._min_range = min([w.get_minimum_range() for w in self._weapon_storage])
		self._max_range = max([w.get_maximum_range() for w in self._weapon_storage])

	def add_weapon_to_storage(self, weapon_id):
		"""
		adds weapon to storage
		@param weapon_id : id of the weapon to be added
		"""
		#if weapon is stackable, try to stack
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
				self._weapon_storage.append(StackableWeapon(self.session, weapon_id))
		else:
			self._weapon_storage.append(Weapon(self.session, weapon_id))
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
		#if cannon needs to be removed try decrease number
		if self.session.db.get_weapon_stackable(weapon_id):
			try:
				weapon.decrease_number_of_weapons(1)
			except SetStackableWeaponNumberError:
				self._weapon_storage.remove(weapon)
		else:
			self._weapon_storage.remove(weapon)

		self.on_storage_modified()

	def attack_possible(self, dest):
		distance = self.position.distance_to_point(dest)
		for weapon in self._weapon_storage:
			if weapon.check_target_in_range(distance):
				return True
		return False

	def get_ticks_until_next_attack(self):
		"""returns minimum number of ticks until a weapon that can hit the target can be fired again"""
		distance = self.position.distance(self._target.position)
		return min([w.remaining_ticks for w in self._weapon_storage if w.check_target_in_range(distance)])

	def try_attack_target(self):
		if self._target is None:
			return

		if hasattr(self._target, health):
			print self._target,'has health:',self._target.health.health
			print self._target.health.max_health

		if self.is_moving:
			self.stop()

		dest = self._target.position.center()
		in_range = False
		distance = self.position.distance(dest)

		if distance >= self._min_range and distance <= self._max_range:
			self.fire_all_weapons(dest)
			in_range = True

		if not in_range:
			if self.movable:
				try:
					self.move(Annulus(dest, self._min_range, self._max_range), Callback(self.fire_all_weapons, dest),
						blocked_callback = Callback(self.fire_all_weapons, dest))
				except MoveNotPossible:
					pass

		if in_range:
			#if tried to fire weapons get the next amount of ticks until another weapon can be fired again
			ticks = self.get_ticks_until_next_attack()
		else:
			#else wait 10 ticks and try to fire again
			ticks = 10

		Scheduler().add_new_object(self.try_attack_target, self, ticks)

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
		#fires all weapons at a given position
		distance = self.position.distance(dest)
		for weapon in self._weapon_storage:
			weapon.fire(dest, distance)

	def save(self, db):
		super(WeaponHolder, self).save(db)
		weapons = {}
		for weapon in self._weapon_storage:
			number = 1
			if weapon.weapon_id == WEAPONS.CANNON:
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

