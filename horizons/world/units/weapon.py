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
	def __init__(self, session):
		#TODO add arguments
		#it will have modifiers as arguments
		#they will be loaded from database
		self.session = session
		
	def fire(self, position):
		print 'firing weapon at position', position
		units = self.session.world.get_ships(position, self.attack_radius)

		#TODO add buildings to units
		for unit in units:
			print 'dealing damage to ship:', unit
			unit.health -= self.damage
		#TODO implement all modifiers
		#get actual location from accuracy
		#get damage for position

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
		#tuple with min range, max range
		self.weapon_range = 5,15
		self.attack_radius = 4
		self.damage = 10
		#this stays here!
		self.number = 1

	def set_number(self, number):
		#set modifiers for number of resource cannons used
		self.number = number;

	def fire(self, position):
		#multiply the damage by number of resource cannons per instance
		self.damage *= self.number
		super(Cannon, self).fire(position)
		#set it back
		self.damage /= self.number
