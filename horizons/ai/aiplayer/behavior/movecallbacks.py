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

import logging
from horizons.component.namedcomponent import NamedComponent
from horizons.util.python.callback import Callback
from horizons.util.shapes.annulus import Annulus
from horizons.util.shapes.circle import Circle
from horizons.world.units.movingobject import MoveNotPossible
from horizons.world.units.weaponholder import MovingWeaponHolder


class BehaviorMoveCallback:
	"""
	Container class for general purpose ship moves and move callbacks.
	"""
	log = logging.getLogger('ai.aiplayer.combat.movecallbacks')

	@classmethod
	def _get_annulus(cls, position, range, range_delta):
		return Annulus(position, max(0, range - range_delta), range + range_delta)

	@classmethod
	def _arrived(cls, ship):
		combat_manager = ship.owner.combat_manager
		combat_manager.set_ship_state(ship, combat_manager.shipStates.idle)
		cls.log.debug("%s: _arrived: Ship %s arrived at target", cls.__name__, ship.get_component(NamedComponent).name)

	@classmethod
	def maintain_distance_and_attack(cls, ship, enemy, range, range_delta=1):
		"""
		Attacks given target if possible and adjust ship position to keep given range.
		"""
		combat_manager = ship.owner.combat_manager

		distance = ship.position.distance(enemy.position)
		cls.log.debug("maintain_distance_and_attack: Ship: %s, Enemy: %s, distance: %s, range: %s, range_delta: %s", ship.get_component(NamedComponent).name,
			enemy.get_component(NamedComponent).name, distance, range, range_delta)

		if ship.can_attack_position(enemy.position):
			ship.attack(enemy) # attack ship if close enough to fire
			cls.log.debug("%s: maintain_distance_and_attack: Attack: %s -> %s", cls.__name__,
				ship.get_component(NamedComponent).name, enemy.get_component(NamedComponent).name)

		# calculate distance between each ship and adjust distance
		if abs(distance - range) > range_delta:
			try:
				target = cls._get_annulus(enemy.position, range, range_delta)
				ship.move(target, callback=Callback(cls._arrived, ship))

				# set state to moving since we don't attack during that
				combat_manager.set_ship_state(ship, combat_manager.shipStates.moving)
				cls.log.debug("%s: maintain_distance_and_attack: Moving towards the target", cls.__name__)
			except MoveNotPossible:
				cls.log.debug("%s: maintain_distance_and_attack: Move was not possible", cls.__name__)
