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
from horizons.util.shapes.circle import Circle
from horizons.world.units.movingobject import MoveNotPossible

class BehaviorMoveCallback:
	"""
	Container class for general purpose ship moves and move callbacks.
	"""
	log = logging.getLogger('ai.aiplayer.behavior.movecallbacks')

	flee_home_radius = 5

	# when sending whole fleet somewhere don't specify exact point, so ships don't block each other
	sail_point_range = 5

	pirate_caught_ship_radius = 5
	pirate_home_radius = 2

	@classmethod
	def _arrived(cls, ship):
		"""
		Callback function executed once ship arrives at the destination after certain action.
		Be it after fleeing battle, sailing randomly, scouting etc.
		Practically only changes ship state to idle.
		"""
		owner = ship.owner
		cls.log.debug('Player %s: Ship %s: arrived at destination after "%s"' % (owner.name,
		   ship.get_component(NamedComponent).name, owner.ships[ship]))
		owner.ships[ship] = owner.shipStates.idle

	@classmethod
	def _sail_near(cls, ship, point=None):
		"""
		Sends ship to a point nearby.
		"""
		owner = ship.owner
		try:
			ship.move(Circle(point, cls.sail_point_range), Callback(cls._arrived, ship))
			owner.ships[ship] = owner.shipStates.moving_random
		except MoveNotPossible:
			cls.log.debug("ScoutRandomlyNearby move was not possible -> go idle")
			owner.ships[ship] = owner.shipStates.idle

	@classmethod
	def _flee_home(cls, ship):
		owner = ship.owner
		home_position = None
		for settlement in owner.session.world.settlements:
			if settlement.owner == owner:
				home_position = settlement.warehouse.position
				break

		if not home_position:
			cls.log.info("Ship:%s couldn't flee home, home_position not found"%(ship.get_component(NamedComponent).name))
			return
		try:
			ship.move(Circle(home_position.origin, cls.flee_home_radius), Callback(cls._arrived, ship))
			owner.ships[ship] = owner.shipStates.fleeing_combat
		except MoveNotPossible:
			cls.log.info("Ship:%s couldn't flee, move was not possible -> going idle"%(ship.get_component(NamedComponent).name))
			owner.ships[ship] = owner.shipStates.idle

	# Pirate moves and callbacks used for pirate routine
	@classmethod
	def _chase_closest_ship(cls, pirate_ship):
		owner = pirate_ship.owner
		ship = owner.get_nearest_player_ship(pirate_ship)
		if ship:
			owner.ships[pirate_ship] = owner.shipStates.chasing_ship

			# if ship was caught
			if ship.position.distance(pirate_ship.position) <= cls.pirate_caught_ship_radius:
				cls.log.debug('Pirate %s: Ship %s(%s) caught %s' % (owner.worldid,
					pirate_ship.get_component(NamedComponent).name, owner.ships[pirate_ship], ship))
				cls._sail_home(pirate_ship)
			else:
				try:
					pirate_ship.move(Circle(ship.position, cls.pirate_caught_ship_radius - 1), Callback(cls._sail_home, pirate_ship))
					owner.ships[pirate_ship] = owner.shipStates.chasing_ship
					cls.log.debug('Pirate %s: Ship %s(%s) chasing %s' % (owner.worldid,
						pirate_ship.get_component(NamedComponent).name, owner.ships[pirate_ship], ship.get_component(NamedComponent).name))
				except MoveNotPossible:
					cls.log.debug('Pirate %s: Ship %s(%s) unable to chase the closest ship %s' % (owner.worldid,
						pirate_ship.get_component(NamedComponent).name, owner.ships[pirate_ship], ship.get_component(NamedComponent).name))
					owner.ships[pirate_ship] = owner.shipStates.idle

	@classmethod
	def _sail_home(cls, pirate_ship):
		owner = pirate_ship.owner
		try:
			pirate_ship.move(Circle(owner.home_point, cls.pirate_home_radius), Callback(cls._arrived, pirate_ship))
			owner.ships[pirate_ship] = owner.shipStates.going_home
			cls.log.debug('Pirate %s: Ship %s(%s): sailing home at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name,
				owner.ships[pirate_ship], owner.home_point))
		except MoveNotPossible:
			owner.ships[pirate_ship] = owner.shipStates.idle
			cls.log.debug('Pirate %s: Ship %s: unable to move home at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name, owner.home_point))

	@classmethod
	def _sail_random(cls, pirate_ship):

		owner = pirate_ship.owner
		session = owner.session
		point = session.world.get_random_possible_ship_position()
		try:
			pirate_ship.move(point, Callback(cls._arrived, pirate_ship))
			owner.ships[pirate_ship] = owner.shipStates.moving_random
			cls.log.debug('Pirate %s: Ship %s(%s): moving random at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name,
				owner.ships[pirate_ship], point))
		except MoveNotPossible:
			owner.ships[pirate_ship] = owner.shipStates.idle
			cls.log.debug('Pirate %s: Ship %s: unable to move random at %s' % (owner.worldid, pirate_ship.get_component(NamedComponent).name, point))

