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

from horizons.util import Circle

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
		self.attack_radius = 4
		self.damage = 10
		self.session = session

	def get_damage_modifier(self):
		return self.damage

	def fire(self, position):
		print 'firing weapon at position', position
		units = self.session.world.get_ships(position, self.attack_radius)

		#TODO add buildings to units
		for unit in units:
			print 'dealing damage to ship:', unit
			unit.health -= self.get_damage_modifier()
		#TODO implement all modifiers
		#get actual location from accuracy
		#get damage for position

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
		#TODO move modifiers up to Weapon,
		#modifiers will be loaded from database
		super(Cannon, self).__init__(session)
		self.__init()

	def __init(self):
		self.weapon_type = 'ranged'
		#this stays here!
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

