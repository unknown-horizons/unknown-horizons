# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import logging

from horizons.util import Point, Callback
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.world.units.bullet import Bullet
from horizons.component.healthcomponent import HealthComponent

@metaChangeListenerDecorator("attack_ready")
@metaChangeListenerDecorator("weapon_fired")
class Weapon(object):
	"""
	Generic Weapon class
	it has the modifiers:
		damage - damage dealt in hp
		weapon_range - tuple with minimum and maximum attack range
		cooldown_time - number of seconds until the attack is ready again
		attack_speed - speed that calculates the time until attack reaches target
		attack_radius - radius affected by attack
		bullet_image - path to file with the bullet image,
			if no string is provided, then no animation will be played

		attack_ready callbacks are executed when the attack is made ready
	"""
	log = logging.getLogger("world.combat")

	def __init__(self, session, id):
		"""
		@param session: game session
		@param id: weapon id to be initialized
		"""
		data = session.db("SELECT id, type, damage,\
		                          min_range, max_range,\
		                          cooldown_time, attack_speed,\
		                          attack_radius, bullet_image \
		                  FROM weapon WHERE id = ?", id)
		data = data[0]
		self.weapon_id = data[0]
		self.weapon_type = data[1]
		self.damage = data[2]
		self.weapon_range = data[3], data[4]
		self.cooldown_time = data[5]
		self.attack_speed = data[6]
		self.attack_radius = data[7]
		self.bullet_image = data[8]
		self.attack_ready = True
		self.session = session

	def get_damage_modifier(self):
		return self.damage

	def get_minimum_range(self):
		return self.weapon_range[0]

	def get_maximum_range(self):
		return self.weapon_range[1]

	@classmethod
	def on_impact(cls, session, weapon_id, damage, position):
		"""
		Classmethod that deals damage to units at position, depending on weapon_id
		Damage is done independent of the weapon instance, which may not exist at the time damage is done
		@param session : UH session
		@param weapon_id : id of the weapon
		@param damage : damage to be done
		@param position : Point with position where damage needs to be done
		"""
		cls.log.debug("%s impact", cls)
		# deal damage to units in position callback
		attack_radius = session.db.get_weapon_attack_radius(weapon_id)

		units = session.world.get_health_instances(position, attack_radius)

		for unit in units:
			cls.log.debug("dealing damage to %s", unit)
			unit.get_component(HealthComponent).deal_damage(weapon_id, damage)

	def make_attack_ready(self):
		self.attack_ready = True
		self.on_attack_ready()

	def fire(self, destination, position, bullet_delay=0):
		"""
		Fires the weapon at a certain destination
		@param destination: Point with position where weapon will be fired
		@param position: position where the weapon is fired from
		@param bullet_delay:
		"""
		self.log.debug("%s fire; ready: %s", self, self.attack_ready)
		if not self.attack_ready:
			return

		distance = round(position.distance(destination.center()))
		if not self.check_target_in_range(distance):
			self.log.debug("%s target not in range", self)
			return

		#calculate the ticks until impact
		impact_ticks = int(GAME_SPEED.TICKS_PER_SECOND * distance / self.attack_speed)
		#deal damage when attack reaches target
		Scheduler().add_new_object(Callback(Weapon.on_impact,
			self.session, self.weapon_id, self.get_damage_modifier(), destination),
			Weapon, impact_ticks)

		#calculate the ticks until attack is ready again
		ready_ticks = int(GAME_SPEED.TICKS_PER_SECOND * self.cooldown_time)
		Scheduler().add_new_object(self.make_attack_ready, self, ready_ticks)

		if self.bullet_image:
			Scheduler().add_new_object(
				Callback(Bullet, self.bullet_image, position, destination, impact_ticks - bullet_delay, self.session),
				self,
				run_in=bullet_delay)
		self.log.debug("fired %s at %s, impact in %s", self, destination, impact_ticks - bullet_delay)

		self.attack_ready = False
		self.on_weapon_fired()

	def check_target_in_range(self, distance):
		"""
		Checks if the distance between the weapon and target is in weapon range
		@param distance : distance between weapon and target
		"""
		return self.weapon_range[0] <= distance <= self.weapon_range[1]

	def get_ticks_until_ready(self):
		"""
		Returns the number of ticks until the attack is ready
		If attack is ready return 0
		"""
		return 0 if self.attack_ready else Scheduler().get_remaining_ticks(self, self.make_attack_ready)


	@classmethod
	def load_attacks(cls, session, db):
		"""
		Loads ongoing attacks from savegame database
		Creates scheduled calls for on_impact
		"""
		for (ticks, weapon_id, damage, dx, dy) in db("SELECT remaining_ticks, weapon_id, damage, dest_x, dest_y FROM attacks"):
			Scheduler().add_new_object(Callback(Weapon.on_impact,
				session, weapon_id, damage, Point(dx, dy)), Weapon, ticks)

	@classmethod
	def save_attacks(cls, db):
		"""
		Saves ongoing attacks
		"""
		calls = Scheduler().get_classinst_calls(Weapon)
		for call in calls:
			callback = call.callback
			weapon_id = callback.args[1]
			damage = callback.args[2]
			dest_x = callback.args[3].x
			dest_y = callback.args[3].y
			ticks = calls[call]
			db("INSERT INTO attacks(remaining_ticks, weapon_id, damage, dest_x, dest_y) VALUES (?, ?, ?, ?, ?)",
				ticks, weapon_id, damage, dest_x, dest_y)

	def __str__(self):
		return "Weapon(id:%s;type:%s;rang:%s)" % (self.weapon_id, self.weapon_type, self.weapon_range)

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
		self.max_number_of_weapons = 1

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

