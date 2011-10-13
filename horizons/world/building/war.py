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

from horizons.world.building.buildable import BuildableSingle
from horizons.world.building.building import SelectableBuilding, BasicBuilding

from horizons.world.units.weaponholder import WeaponHolder
from horizons.constants import WEAPONS

class Tower(BuildableSingle, SelectableBuilding, BasicBuilding, WeaponHolder):
	def __init__(self, *args, **kwargs):
		super(Tower, self).__init__(*args, **kwargs)
		self.add_weapon_to_storage(WEAPONS.CANNON)
		self.add_weapon_to_storage(WEAPONS.CANNON)
		self.add_weapon_to_storage(WEAPONS.CANNON)

	def fire_all_weapons(self, dest, rotate = True):
		super(Tower, self).fire_all_weapons(dest, rotate)
