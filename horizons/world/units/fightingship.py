# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from horizons.component.commandablecomponent import CommandableComponent
from horizons.constants import GAME_SPEED, WEAPONS
from horizons.world.units.ship import Ship
from horizons.world.units.weaponholder import MovingWeaponHolder


class FightingShip(MovingWeaponHolder, Ship):
	"""Class representing a fighting ship
	@param x: int x position
	@param y: int y position
	"""
	health_bar_y = -190

	def __init__(self, x, y, **kwargs):
		super().__init__(x=x, y=y, **kwargs)
		# add default weapons
		for i in range(WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM):
			self.add_weapon_to_storage(WEAPONS.CANNON)
		print("Ship created and weapons loaded.")

	def go(self, x, y):
		self.get_component(CommandableComponent).go(x, y)
		print("Ship moved to coordinates: ({}, {})".format(x, y))
		self.stop_attack()
		print("Moving ship to ({},{}).".format(x, y))

	def fire_all_weapons(self, dest, rotate=True):
		"""
		Fire weapons at rotated coordinates
		"""
		super().fire_all_weapons(dest, rotate)
		print("Weapons fired!")

	def act_attack(self, dest):
		"""
		Rotates the ship and triggers correct animation
		"""
		# rotate the ship so it faces dest
		# for this rotate facing location coordinates around position coordinates
		self.stop_for(GAME_SPEED.TICKS_PER_SECOND * 2)
		self_location = self._instance.getLocation()
		facing_location = self._instance.getFacingLocation()

		# ship coords
		x1 = self_location.getMapCoordinates().x
		y1 = self_location.getMapCoordinates().y
		# target coords
		x2 = dest.x
		y2 = dest.y
		# facing coords
		x3 = facing_location.getMapCoordinates().x
		y3 = facing_location.getMapCoordinates().y
		facing_coords = facing_location.getMapCoordinates()
		# calculate the side of the ship - target line facing location is on
		# side > 0 left, side <= 0 right
		side = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
		# calculate x4 y4 the new facing location coords
		# they are calculated by rotating 90' the target location
		#if side > 0: check if it should be: if side > 0: or if (side or 0) > 0:
		if (side or 0) > 0:
			x4 = y1 - y2 + x1
			y4 = x2 - x1 + y1
			direction = 'left'
		else:
			x4 = y2 - y1 + x1
			y4 = x1 - x2 + y1
			direction = 'right'

		facing_coords.x = x4
		facing_coords.y = y4

		facing_location.setMapCoordinates(facing_coords)
		self._instance.setFacingLocation(facing_location)
		self.act('fire_{}'.format(direction), facing_location, repeating=False)
		self._action = 'idle'
		print("Ship rotated and ready for combat.")
