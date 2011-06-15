# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.

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

from horizons.util import Circle, Callback
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED

@metaChangeListenerDecorator("damage_dealt")
class Weapon(object):
	"""
	Generic Weapon class
	it has the modifiers:
		damage - damage dealt in hp
		weapon_range - tuple with minimum and maximum attack range
		cooldown_time - number of seconds until the attack is ready again
		attack_speed - speed that calculates the time until attack reaches target
		attack_radius - radius affected by attack

	remaining_ticks attribute is updated with the ramaining ticks until the attack is ready again
		it is 0 if the attack is ready
	"""
	def __init__(self, session, id):
		"""
		@param session: game session
		@param id: weapon id to be initialized
		"""
		data = session.db("SELECT id, type, damage,\
		                          min_range, max_range,\
		                          cooldown_time, attack_speed,\
		                          attack_radius \
		                  FROM weapon WHERE id = ?", id)
		data = data[0]
		self.weapon_id = data[0]
		self.weapon_type = data[1]
		self.damage = data[2]
		self.weapon_range = data[3], data[4]
		self.cooldown_time = data[5]
		self.attack_speed = data[6]
		self.attack_radius = data[7]
		self.attack_ready = True
		self.remaining_ticks = 0
		self.session = session

	def get_damage_modifier(self):
		return self.damage

	def get_minimum_range(self):
		return self.weapon_range[0]

	def get_maximum_range(self):
		return self.weapon_range[1]

	def on_impact(self, position):
		#deal damage to units in position callback
		#TODO use damage_dealt listener

		units = self.session.world.get_ships(position, self.attack_radius)
		for point in Circle(position, self.attack_radius):
			unit = self.session.world.get_building(point)
			if unit not in units and unit is not None:
				units.append(unit)

		for unit in units:
			print 'dealing damage to ship:', unit
			#TODO remove the if when health attribute will only be HealthComponent
			if hasattr(unit.health, 'deal_damage'):
				unit.health.deal_damage(self.weapon_id, self.get_damage_modifier())

	def make_attack_ready(self):
		self.attack_ready = True

	def fire(self, position, distance):
		"""
		Fires the weapon at a certain position
		@param position : position where weapon will be fired
		@param distance : distance between weapon and target
		"""
		#update remaining ticks
		#if the attack isn't ready check the remaining ticks
		#else the attack is ready and the remaining ticks are 0

		if not self.attack_ready:
			print 'attack not ready!'
			self.remaining_ticks = Scheduler().get_remaining_ticks(self, self.make_attack_ready)
			return
		else:
			self.remaining_ticks = 0

		if not self.check_target_in_range(distance):
			return

		#calculate the ticks until impact
		ticks = int(GAME_SPEED.TICKS_PER_SECOND * distance / self.attack_speed)
		#deal damage when attack reaches target
		Scheduler().add_new_object(Callback(self.on_impact, position), self, ticks)

		#calculate the ticks until attack is ready again
		ticks = int(GAME_SPEED.TICKS_PER_SECOND * self.cooldown_time)
		Scheduler().add_new_object(self.make_attack_ready, self, ticks)

		#if weapon was fired update remaining ticks
		self.remaining_ticks = ticks
		self.attack_ready = False

	def check_target_in_range(self, distance):
		"""
		Checks if the distance between the weapon and target is in weapon range
		@param distance : distance between weapon and target
		"""
		if distance >= self.weapon_range[0] and distance <= self.weapon_range[1]:
			return True
		return False

class SetStackableWeaponNumberError(Exception):
	"""
	Raised when setting the number of weapons for a stackable weapon fails
	"""
	pass

class StackableWeapon(Weapon):
	"""
	Stackable Weapon class
	A generic Weapon that can have a number of weapons binded per instance
	It deals the number of weapons times weapon's default damage
	This is used for cannons, reducing the number of instances and bullets fired
	"""
	def __init__(self, session, id):
		super(StackableWeapon, self).__init__(session, id)
		self.__init()

	def __init(self):
		self.number_of_weapons = 1
		self.max_number_of_weapons = 3

	def set_number_of_weapons(self, number):
		"""
		Sets number of cannons as resource binded to a StackableWeapon object
		the number of cannons increases the damage dealt by one StackableWeapon instance
		@param number : number of cannons
		"""
		if number > self.max_number_of_weapons:
			raise SetStackableWeaponNumberError
		else:
			self.number_of_weapons = number

	def increase_number_of_weapons(self, number):
		"""
		Increases number of cannons as resource binded to a StackableWeapon object
		@param number : number of cannons
		"""
		if number + self.number_of_weapons > self.max_number_of_weapons:
			raise SetStackableWeaponNumberError
		else:
			self.number_of_weapons += number

	def decrease_number_of_weapons(self, number):
		"""
		Decreases number of cannons as resource binded to a StackableWeapon object
		@param number : number of cannons
		"""
		if self.number_of_weapons - number <= 0:
			raise SetStackableWeaponNumberError
		else:
			self.number_of_weapons -= number

	def get_damage_modifier(self):
		return self.number_of_weapons * super(StackableWeapon, self).get_damage_modifier()

