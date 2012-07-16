# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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
import logging
import math

from horizons.util import Annulus, Point, Callback
from horizons.world.units.movingobject import MoveNotPossible
from horizons.scheduler import Scheduler
from horizons.util.changelistener import metaChangeListenerDecorator
from weapon import Weapon, StackableWeapon, SetStackableWeaponNumberError
from horizons.constants import GAME_SPEED
from horizons.component.stancecomponent import HoldGroundStance, AggressiveStance, \
	NoneStance, FleeStance
from horizons.world.storage import PositiveTotalNumSlotsStorage
from horizons.world.units.ship import Ship
from horizons.component.storagecomponent import StorageComponent
from horizons.util.worldobject import WorldObject

@metaChangeListenerDecorator("storage_modified")
@metaChangeListenerDecorator("user_attack_issued")
class WeaponHolder(object):
	log = logging.getLogger("world.combat")

	def __init__(self, **kwargs):
		super(WeaponHolder, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		self.create_weapon_storage()
		self._target = None
		self.add_storage_modified_listener(self.update_range)
		self.equipped_weapon_number = 0
		Scheduler().add_new_object(self._stance_tick, self, run_in = 2, loops = -1, loop_interval = GAME_SPEED.TICKS_PER_SECOND)

	def remove(self):
		self.remove_storage_modified_listener(self.update_range)
		self.stop_attack()
		for weapon in self._weapon_storage:
			weapon.remove_attack_ready_listener(Callback(self._add_to_fireable, weapon))
			weapon.remove_weapon_fired_listener(Callback(self._remove_from_fireable, weapon))
			weapon.remove_weapon_fired_listener(self._increase_fired_weapons_number)
		super(WeaponHolder, self).remove()

	def create_weapon_storage(self):
		self._weapon_storage = []
		self._fireable = []
		#TODO make a system for making it load from db
		self.total_number_of_weapons = 30

	def update_range(self, caller=None):
		if self._weapon_storage:
			self._min_range = min([w.get_minimum_range() for w in self._weapon_storage])
			self._max_range = max([w.get_maximum_range() for w in self._weapon_storage])
		else:
			self._min_range = 0
			self._max_range = 0

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
		Scheduler().add_new_object(Callback(self._fireable.remove, weapon), self, run_in = 0)

	def _increase_fired_weapons_number(self, caller=None):
		"""
		Callback that helps keeping tack of succesful weapon fire number
		"""
		self._fired_weapons_number += 1

	def add_weapon_to_storage(self, weapon_id):
		"""
		adds weapon to storage
		@param weapon_id : id of the weapon to be added
		"""
		self.log.debug("%s add weapon %s", self, weapon_id)
		#if weapon is stackable, try to stack
		weapon = None
		if self.equipped_weapon_number == self.total_number_of_weapons:
			self.log.debug("%s weapon storage full", self)
			return False
		if self.session.db.get_weapon_stackable(weapon_id):
			stackable = [w for w in self._weapon_storage if weapon_id == w.weapon_id]
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
			weapon.add_weapon_fired_listener(self._increase_fired_weapons_number)
			self._fireable.append(weapon)
			self.equipped_weapon_number += 1
		self.on_storage_modified() # will update the range
		return True

	def remove_weapon_from_storage(self, weapon_id):
		"""
		removes weapon to storage
		@param weapon_id : id of the weapon to be removed
		"""
		self.log.debug("%s remove weapon %s", self, weapon_id)
		weapons = [w for w in self._weapon_storage if w.weapon_id == weapon_id]
		if not weapons:
			self.log.debug("%s can't remove, no weapons there", self)
			return False
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
			weapon.remove_weapon_fired_listener(self._increase_fired_weapons_number)
			try:
				self._fireable.remove(weapon)
			except ValueError:
				pass

		self.on_storage_modified()
		self.equipped_weapon_number -= 1
		return True

	def equip_from_inventory(self, weapon_id, number):
		"""Equips weapon if present in inventory
		@param weapon_id: weapon id to be equipped
		@param number: number of weapons to be equipped
		returns the number of weapons that were not equipped
		"""
		while number:
			if self.get_component(StorageComponent).inventory.alter(weapon_id, -1) == 0:
				# try to decrease number from inventory
				if not self.add_weapon_to_storage(weapon_id):
					# if not added, put back in inventory and break
					self.get_component(StorageComponent).inventory.alter(weapon_id, 1)
					break
			else:
				break
			number -= 1
		return number

	def unequip_to_inventory(self, weapon_id, number):
		"""Unequips weapon and adds it to inventory
		@param weapon_id: weapon id to be unequipped
		@param number: number of weapons to be unequipped
		returns the number of weapons that were not added to storage
		"""
		while number:
			if self.remove_weapon_from_storage(weapon_id):
				# try to remove from weapon storage
				if self.get_component(StorageComponent).inventory.alter(weapon_id, 1) == 1:
					# if not added to holder inventory move back to storage and break
					self.add_weapon_to_storage(weapon_id)
					break
			else:
				break
			number -= 1
		return number

	def get_weapon_storage(self):
		"""
		Returns storage object for self._weapon_storage
		"""
		storage = PositiveTotalNumSlotsStorage(self.total_number_of_weapons, 4)
		for weapon in self._weapon_storage:
			weapon_id = weapon.weapon_id
			if self.session.db.get_weapon_stackable(weapon_id):
				number = weapon.number_of_weapons
			else:
				number = 1
			storage.alter(weapon_id, number)
		return storage

	def attack_in_range(self):
		"""
		Returns True if the target is in range, False otherwise
		"""
		if not self._target:
			return False
		distance = self.position.distance(self._target.position.center())
		return self._min_range <= distance <= self._max_range

	def can_attack_position(self, position):
		"""
		Returns True if the holder can attack position at call time
		@param position: position of desired attack
		"""
		# if no fireable weapon return false
		if not self._fireable:
			return False
		# if position not in range return false
		return self._min_range <= self.position.distance(position.center()) <= self._max_range

	def try_attack_target(self):
		"""
		Attacking loop
		"""
		self.log.debug("%s try attack target %s", self, self._target)
		if self._target is None:
			return

		if self.attack_in_range():
			dest = self._target.position.center()
			if self._target.movable and self._target.is_moving():
				dest = self._target._next_target

			self.fire_all_weapons(dest)
			Scheduler().add_new_object(self.try_attack_target, self, GAME_SPEED.TICKS_PER_SECOND)
			self.log.debug("%s fired, fire again in %s ticks", self, GAME_SPEED.TICKS_PER_SECOND)
		else:
			self.log.debug("%s target not in range", self)

	def _stance_tick(self):
		"""
		Executes every few seconds, doing movement depending on the stance.
		Static WeaponHolders are aggressive, attacking all enemies that are in range
		"""
		enemies = [u for u in self.session.world.get_health_instances(self.position.center(), self._max_range)
			if self.session.world.diplomacy.are_enemies(u.owner, self.owner)]

		self.log.debug("%s stance tick, found enemies: %s", self, [str(i) for i in enemies])
		if not enemies:
			return

		self.attack(enemies[0])

	def attack(self, target):
		"""
		Triggers attack on target
		@param target : target to be attacked
		"""
		self.log.debug("%s attack %s", self, target)
		if self._target is not None:
			if self._target is not target:
				#if target is changed remove the listener
				if self._target.has_remove_listener(self.remove_target):
					self._target.remove_remove_listener(self.remove_target)
			else:
				#else do not update the target
				self.log.debug("%s already targeting this one", self)
				return
		if not target.has_remove_listener(self.remove_target):
			target.add_remove_listener(self.remove_target)
		self._target = target

		self.try_attack_target()

	def user_attack(self, targetid):
		"""
		Called when the user triggeres the attack, executes the user_attack_issued callbacks
		@param targetid: world id of the unit that is to be attacked
		"""
		self.attack(WorldObject.get_object_by_id(targetid))
		self.on_user_attack_issued()

	def is_attacking(self):
		"""
		Returns True if the WeaponHolder is trying to attack a target
		"""
		return True if self._target else False

	def remove_target(self):
		"""
		Removes refference from target,
		this happens when the attack is stopped or the target is dead
		either way the refs are checked using gc module
		this is used because after unit death it's possbile that it still has refs
		"""
		if self._target is not None and 3>4:
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
		self.log.debug("%s stop attack", self)
		if self._target is not None:
			if self._target.has_remove_listener(self.remove_target):
				self._target.remove_remove_listener(self.remove_target)
		self.remove_target()


	def fire_all_weapons(self, dest, rotated=False, bullet_delay=0):
		"""
		Fires all weapons in storage at a given position
		@param dest: Point with the given position
		@param rotated: If True weapons will be fired at different locations, rotated around dest
			override to True for units that need to fire at rotated coords
		"""
		self.log.debug("%s fire all weapons", self)
		self._fired_weapons_number = 0
		if not self.can_attack_position(dest):
			self.log.debug("%s can't attack this position", self)
			return

		if not rotated:
			for weapon in self._fireable:
				weapon.fire(dest, self.position.center(), bullet_delay)
		else:
			angle = (math.pi / 60) * (-len(self._fireable) / 2)
			cos = math.cos(angle)
			sin = math.sin(angle)

			x = self.position.center().x
			y = self.position.center().y

			dest_x = dest.x
			dest_y = dest.y

			dest_x = (dest_x - x) * cos - (dest_y - y) * sin + x
			dest_y = (dest_x - x) * sin + (dest_y - y) * cos + y

			angle = math.pi / 60
			cos = math.cos(angle)
			sin = math.sin(angle)

			for weapon in self._fireable:
				destination = Point(dest_x, dest_y)
				weapon.fire(destination, self.position.center(), bullet_delay)
				dest_x = (dest_x - x) * cos - (dest_y - y) * sin + x
				dest_y = (dest_x - x) * sin + (dest_y - y) * cos + y

		if self._fired_weapons_number != 0:
			self.act_attack(dest)

	def act_attack(self, dest):
		"""
		Overridde in subclasses for action code
		"""
		pass

	def get_attack_target(self):
		return self._target

	def save(self, db):
		super(WeaponHolder, self).save(db)
		# save weapon storage
		for weapon in self._weapon_storage:
			number = 1
			ticks = weapon.get_ticks_until_ready()
			if self.session.db.get_weapon_stackable(weapon.weapon_id):
				number = weapon.number_of_weapons

			db("INSERT INTO weapon_storage(owner_id, weapon_id, number, remaining_ticks) VALUES(?, ?, ?, ?)",
				self.worldid, weapon.weapon_id, number, ticks)
		# save target
		if self._target:
			db("INSERT INTO target(worldid, target_id) VALUES(?, ?)", self.worldid, self._target.worldid)

	def load_target(self, db):
		"""
		Loads target from database
		"""
		target_id = db("SELECT target_id from target WHERE worldid = ?", self.worldid)
		if target_id:
			target = self.session.world.get_object_by_id(target_id[0][0])
			self.attack(target)

	def load(self, db, worldid):
		super(WeaponHolder, self).load(db, worldid)
		self.__init()
		weapons = db("SELECT weapon_id, number, remaining_ticks FROM weapon_storage WHERE owner_id = ?", worldid)
		for weapon_id, number, ticks in weapons:
			# create weapon and add to storage manually
			if self.session.db.get_weapon_stackable(weapon_id):
				weapon = StackableWeapon(self.session, weapon_id)
				weapon.set_number_of_weapons(number)
			else:
				weapon = Weapon(self.session, weapon_id)
			self._weapon_storage.append(weapon)
			# if weapon not ready add scheduled call and remove from fireable
			if ticks:
				weapon.attack_ready = False
				Scheduler().add_new_object(weapon.make_attack_ready, weapon, ticks)
			else:
				self._fireable.append(weapon)
			weapon.add_weapon_fired_listener(Callback(self._remove_from_fireable, weapon))
			weapon.add_attack_ready_listener(Callback(self._add_to_fireable, weapon))
			weapon.add_weapon_fired_listener(self._increase_fired_weapons_number)
		self.on_storage_modified()
		# load target after all objects have been loaded
		Scheduler().add_new_object(Callback(self.load_target, db), self, run_in = 0)
		self.log.debug("%s weapon storage after load: %s", self, self._weapon_storage)

	def get_status(self):
		"""Return the current status of the ship."""
		if self.is_attacking():
			target = self.get_attack_target()
			if isinstance(target, Ship):
				#xgettext:python-format
				string = _("Attacking {target} '{name}' ({owner})")
				return (string.format(target=target.classname.lower(), name=target.name,
				                      owner=target.owner.name),
				        target.position)
			#xgettext:python-format
			return (_('Attacking {owner}').format(owner=target.owner.name),
			        target.position)
		return super(WeaponHolder, self).get_status()

@metaChangeListenerDecorator("user_move_issued")
class MovingWeaponHolder(WeaponHolder):
	def __init__(self, **kwargs):
		super(MovingWeaponHolder, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		self.add_component(HoldGroundStance())
		self.add_component(AggressiveStance())
		self.add_component(NoneStance())
		self.add_component(FleeStance())
		self.stance = HoldGroundStance

	def _stance_tick(self):
		"""
		Executes every few seconds, doing movement depending on the stance.
		"""
		self.get_component(self.stance).act()

	def stop_for(self, ticks):
		"""
		Delays movement for a number of ticks.
		Used when shooting in specialized unit code.
		"""
		if Scheduler().rem_call(self, self._move_tick):
			Scheduler().add_new_object(Callback(self._move_tick, resume=False), self, ticks)

	def _move_and_attack(self, destination, not_possible_action=None, in_range_callback=None):
		"""
		Callback for moving to a destination, then attack
		@param destination : moving destination
		@param not_possible_action : execute if MoveNotPossible is thrown
		@param in_range_callback : sets up a conditional callback that is executed if the target is in range
		"""
		if not_possible_action:
			assert callable(not_possible_action)
		if in_range_callback:
			assert callable(in_range_callback)

		try:
			self.move(destination, callback = self.try_attack_target,
				blocked_callback = self.try_attack_target)
			if in_range_callback:
				self.add_conditional_callback(self.attack_in_range, in_range_callback)

		except MoveNotPossible:
			if not_possible_action:
				not_possible_action()

	def try_attack_target(self):
		"""
		Attacking loop
		"""
		if self._target is None:
			return

		if not self.attack_in_range():
			destination = Annulus(self._target.position.center(), self._min_range, self._max_range)
			not_possible_action = self.stop_attack
			# if target passes near self, attack!
			in_range_callback = self.try_attack_target
			# if executes attack action try to move in 1 second
			self._move_and_attack(destination, not_possible_action, in_range_callback)
		else:
			if self.is_moving() and self._fireable:
				# stop to shoot
				self.stop()
				# finish the move before removing the move tick
				self._movement_finished()
				# do not execute the next move tick
				Scheduler().rem_call(self, self._move_tick)

			distance = self.position.distance(self._target.position.center())
			dest = self._target.position.center()
			if self._target.movable and self._target.is_moving():
				dest = self._target._next_target

			fireable_number = len(self._fireable)
			self.fire_all_weapons(dest)
			move_closer = False
			# if no weapon was fired, because of holder positioned in dead range, move closer
			if self._fired_weapons_number == 0 and fireable_number != 0:
				# no weapon was fired but i could have fired weapons
				# check if i have weapons that could be shot from this position
				move_closer = True
				distance = self.position.center().distance(self._target.position.center())
				for weapon in self._weapon_storage:
					if weapon.check_target_in_range(distance):
						move_closer = False
						break

			if move_closer:
				destination = Annulus(self._target.position.center(), self._min_range, self._min_range)
				self._move_and_attack(destination)
			else:
				Scheduler().add_new_object(self.try_attack_target, self, GAME_SPEED.TICKS_PER_SECOND)

	def set_stance(self, stance):
		"""
		Sets the stance to a specific one and passes the current state
		"""
		state = self.get_component(self.stance).get_state()
		self.stance = stance
		self.get_component(stance).set_state(state)

	def go(self, x, y):
		super(MovingWeaponHolder, self).go(x, y)
		self.on_user_move_issued()

	def save(self, db):
		super(MovingWeaponHolder, self).save(db)
		db("INSERT INTO stance(worldid, stance, state) VALUES(?, ?, ?)",
			self.worldid, self.stance.NAME, self.get_component(self.stance).get_state())

	def load (self, db, worldid):
		super(MovingWeaponHolder, self).load(db, worldid)
		self.__init()
		stance, state = db("SELECT stance, state FROM stance WHERE worldid = ?", worldid)[0]
		self.stance = self.get_component_by_name(stance)
		self.stance.set_state(state)

	def user_attack(self, targetid):
		super(MovingWeaponHolder, self).user_attack(targetid)
		if self.owner.is_local_player:
			self.session.ingame_gui.minimap.show_unit_path(self)

class StationaryWeaponHolder(WeaponHolder):
	"""Towers and stuff"""
	# TODO: stances (shoot on sight, don't do anything)

	def __init__(self, *args, **kwargs):
		super(StationaryWeaponHolder, self).__init__(*args, **kwargs)
		self.__init()

	def __init(self):
		self.add_component(HoldGroundStance())
		self.stance = HoldGroundStance

	def load(self, db, worldid):
		super(StationaryWeaponHolder, self).load(db, worldid)
		self.__init()

