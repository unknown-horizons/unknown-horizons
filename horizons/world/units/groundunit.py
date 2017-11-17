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

import weakref

from horizons.component.selectablecomponent import SelectableComponent
from horizons.constants import GAME_SPEED, WEAPONS
from horizons.util.pathfinding import PathBlockedError
from horizons.util.pathfinding.pather import SoldierPather
from horizons.world.units.weaponholder import MovingWeaponHolder

from .unit import Unit


class GroundUnit(Unit):
	"""Class representing ground unit
	@param x: int x position
	@param y: int y position
	"""
	# TODO:
	# set these tabs in yaml as soon as there are ground units
	# tabs = (GroundUnitOverviewTab,)
	# enemy_tabs = (EnemyShipOverviewTab,)

	pather_class = SoldierPather
	health_bar_y = -70

	def __init__(self, x, y, **kwargs):
		super().__init__(x=x, y=y, **kwargs)
		self.session.world.ground_units.append(self)
		self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)

	def remove(self):
		super().remove()
		self.session.world.ground_units.remove(self)
		self.session.view.discard_change_listener(self.draw_health)
		del self.session.world.ground_unit_map[self.position.to_tuple()]

	def _move_tick(self, resume=False):
		del self.session.world.ground_unit_map[self.position.to_tuple()]

		try:
			super()._move_tick(resume)
		except PathBlockedError:
			if resume:
				self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)
			raise

		self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)
		self.session.world.ground_unit_map[self._next_target.to_tuple()] = weakref.ref(self)

	def load(self, db, worldid):
		super().load(db, worldid)

		# register unit in world
		self.session.world.ground_units.append(self)
		self.session.world.ground_unit_map[self.position.to_tuple()] = weakref.ref(self)


class FightingGroundUnit(MovingWeaponHolder, GroundUnit):
	"""Weapon Holder Ground Unit"""
	def __init__(self, x, y, **kwargs):
		super().__init__(x=x, y=y, **kwargs)
		#NOTE weapons
		self.add_weapon_to_storage(WEAPONS.SWORD)
		self.add_weapon_to_storage(WEAPONS.CANNON)
		names = self.session.db("SELECT name FROM groundunitnames")
		# We need unicode strings as the name is displayed on screen.
		self.name = [str(x[0], 'utf-8') for x in names]

	def go(self, x, y):
		self.get_component(SelectableComponent).go(x, y)
		self.stop_attack()

	def act_attack(self, dest):
		"""
		Rotates to target and acts correctly
		"""
		self.stop_for(GAME_SPEED.TICKS_PER_SECOND * 2)
		facing_location = self._instance.getFacingLocation()
		facing_coords = facing_location.getMapCoordinates()
		facing_coords.x = dest.x
		facing_coords.y = dest.y
		facing_location.setMapCoordinates(facing_coords)
		self._instance.setFacingLocation(facing_location)

		if dest.distance(self.position) <= 1:
			action = 'melee'
		else:
			action = 'ranged'

		self.act('attack_{}'.format(action), facing_location, repeating=False)
		self._action = 'idle'
