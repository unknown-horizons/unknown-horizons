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

from horizons.util import Circle, Callback
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.scheduler import Scheduler
from horizons.constants import GAME_SPEED

@metaChangeListenerDecorator("damage_dealt")
class Weapon(object):
	"""
	Generic Weapon class
	"""
	def __init__(self, session):
		#TODO add arguments
		#it will have modifiers as arguments
		#they will be loaded from database

		#tuple with min range, max range
		self.weapon_range = 5,15
		#area affected by attack
		self.attack_radius = 4
		#weapon damage
		self.damage = 10
		#bullet speed in tiles per second
		#used to deal damage when bullet has reached the target
		self.attack_speed = 2
		#time until attack is ready again
		#will have one attack per 10 seconds
		self.cooldown_time = 3
		self.attack_ready = True
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
			#TODO call deal damage from unit code, remove from unit code
			unit.health -= self.get_damage_modifier()
			print unit.id
			if unit.health <= 0:
				unit.remove()

	def make_attack_ready(self):
		self.attack_ready = True

	def fire(self, position, distance):
		"""
		Fires the weapon at a certain position
		@param position : position where weapon will be fired
		@param distance : distance between weapon and target
		"""

		if not self.check_target_in_range(distance):
			return

		if not self.attack_ready:
			print 'attack not ready!'
			return

		print 'firing weapon at position', position
		#calculate the ticks until impact
		ticks = int(GAME_SPEED.TICKS_PER_SECOND * distance / self.attack_speed)
		#deal damage when attack reaches target
		Scheduler().add_new_object(Callback(self.on_impact, position), self, ticks)

		#calculate the ticks until attack is ready again
		ticks = int(GAME_SPEED.TICKS_PER_SECOND * self.cooldown_time)
		Scheduler().add_new_object(self.make_attack_ready, self, ticks)
		self.attack_ready = False

	def check_target_in_range(self, distance):
		"""
		Checks if the distance between the weapon and target is in weapon range
		@param distance : distance between weapon and target
		"""
		if distance >= self.weapon_range[0] and distance <= self.weapon_range[1]:
			return True
		return False

class Cannon(Weapon):
	"""
	Cannon class
	"""
	def __init__(self, session):
		#modifiers will be loaded from database
		super(Cannon, self).__init__(session)
		self.__init()

	def __init(self):
		self.weapon_type = 'ranged'
		#number of cannons as resource binded to a Cannon object
		self.number_of_weapons = 1

	def set_number_of_weapons(self, number):
		"""
		Sets number of cannons as resource binded to a Cannon object
		@param number : number of cannons
		"""
		self.number = number

	def get_damage_modifier(self):
		return self.number_of_weapons * super(Cannon, self).get_damage_modifier()

