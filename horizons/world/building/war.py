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

from horizons.world.building.buildable import BuildableSingle
from horizons.world.building.building import BasicBuilding

from horizons.world.units.weaponholder import StationaryWeaponHolder
from horizons.constants import WEAPONS

class Tower(BuildableSingle, StationaryWeaponHolder, BasicBuilding):

	POSSIBLE_WEAPONS = [ WEAPONS.CANNON ]

	def __init__(self, *args, **kwargs):
		super(Tower, self).__init__(*args, **kwargs)
		# apply cannons already payed for
		for weapon_type in self.__class__.POSSIBLE_WEAPONS:
			for i in xrange(self.costs.get(weapon_type, 0)):
				self.add_weapon_to_storage(weapon_type)

	def fire_all_weapons(self, dest, rotate=True):
		super(Tower, self).fire_all_weapons(dest, rotate)

	def update_range(self, caller=None):
		self._fix_weapon_range()
		super(Tower, self).update_range(caller=caller)

	def _fix_weapon_range(self):
		"""Set all min weapon ranges to 0.
		Since the tower can't move, melee units could just approach it and
		destroy the tower"""
		for weapon in self._weapon_storage:
			weapon.weapon_range = (0, weapon.weapon_range[1])