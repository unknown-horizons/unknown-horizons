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
from horizons.util import Annulus, Callback

class WeaponHolder(object):
	def __init__(self, **kwargs):
		super(WeaponHolder, self).__init__(**kwargs)
		self.__init()
	
	def __init(self):
		self.create_weapon_storage()
	
	def create_weapon_storage(self):
		self._weapon_storage = []
	
	def add_weapon_to_storage(self, weapon):
		self._weapon_storage.append(weapon)
	
	def attack_possible(self, dest):
		distance = self.position.distance_to_point(dest)
		for weapon in self._weapon_storage:
			if weapon.check_target_in_range(distance):
				return True
		return False

	def attack(self, dest):
		print 'attack issued'
		in_range = False
		distance = self.position.distance_to_point(dest)
		for weapon in self._weapon_storage:
			weapon.fire(dest, distance)
			if weapon.in_range:
				in_range = True

		if not in_range:
			if self.is_moving:
				min_range = min([w.get_minimum_range() for w in self._weapon_storage])
				max_range = max([w.get_maximum_range() for w in self._weapon_storage])
				try:
					self.move(Annulus(dest, min_range, max_range), Callback(self.attack, dest),
						blocked_callback = Callback(self.attack, dest))
				except MoveNotPossible:
					pass
