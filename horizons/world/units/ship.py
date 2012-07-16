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

import weakref
from fife import fife

import horizons.main

from horizons.util.pathfinding.pather import ShipPather, FisherShipPather
from horizons.util.pathfinding import PathBlockedError
from horizons.world.units.collectors import FisherShipCollector
from unit import Unit
from horizons.constants import LAYERS
from horizons.scheduler import Scheduler
from horizons.component.namedcomponent import ShipNameComponent, NamedComponent
from horizons.component.selectablecomponent import SelectableComponent
from horizons.component.commandablecomponent import CommandableComponent
from horizons.world.traderoute import TradeRoute

class Ship(Unit):
	"""Class representing a ship
	@param x: int x position
	@param y: int y position
	"""
	pather_class = ShipPather
	health_bar_y = -150
	is_ship = True

	in_ship_map = True # (#1023)

	def __init__(self, x, y, **kwargs):
		super(Ship, self).__init__(x=x, y=y, **kwargs)
		self.__init()

	def save(self, db):
		super(Ship, self).save(db)
		if hasattr(self, 'route'):
			self.route.save(db)

	def load(self, db, worldid):
		super(Ship, self).load(db, worldid)
		self.__init()

		# if ship did not have route configured, do not add attribute
		if TradeRoute.has_route(db, worldid):
			self.create_route()
			self.route.load(db)

	def __init(self):
		# register ship in world
		self.session.world.ships.append(self)
		if self.in_ship_map:
			self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)

	def set_name(self, name):
		self.get_component(ShipNameComponent).set_name(name)

	def remove(self):
		self.session.world.ships.remove(self)
		if self.session.view.has_change_listener(self.draw_health):
			self.session.view.remove_change_listener(self.draw_health)
		if self.in_ship_map:
			del self.session.world.ship_map[self.position.to_tuple()]
			if self._next_target.to_tuple() in self.session.world.ship_map:
				del self.session.world.ship_map[self._next_target.to_tuple()]
			self.in_ship_map = False
		super(Ship, self).remove()

	def create_route(self):
		self.route = TradeRoute(self)

	def _move_tick(self, resume=False):
		"""Keeps track of the ship's position in the global ship_map"""
		if self.in_ship_map:
			del self.session.world.ship_map[self.position.to_tuple()]

		try:
			super(Ship, self)._move_tick(resume)
		except PathBlockedError:
			# if we fail to resume movement then the ship should still be on the map but the exception has to be raised again.
			if resume:
				if self.in_ship_map:
					self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
				raise

		if self.in_ship_map:
			# save current and next position for ship, since it will be between them
			self.session.world.ship_map[self.position.to_tuple()] = weakref.ref(self)
			self.session.world.ship_map[self._next_target.to_tuple()] = weakref.ref(self)

	def _movement_finished(self):
		if self.in_ship_map:
			# if the movement somehow stops, the position sticks, and the unit isn't at next_target any more
			if self._next_target is not None:
				ship = self.session.world.ship_map.get(self._next_target.to_tuple())
				if ship is not None and ship() is self:
					del self.session.world.ship_map[self._next_target.to_tuple()]
		super(Ship, self)._movement_finished()

	def go(self, x, y):
		#disable the trading route
		if hasattr(self, 'route'):
			self.route.disable()
		if self.get_component(CommandableComponent).go(x, y) is None:
			self._update_buoy()

	def move(self, *args, **kwargs):
		super(Ship, self).move(*args, **kwargs)
		if self.has_component(SelectableComponent) and \
		   self.get_component(SelectableComponent).selected and \
		   self.owner.is_local_player: # handle buoy
			# if move() is called as move_callback, tmp() from above might
			# be executed after this, so draw the new buoy after move_callbacks have finished.
			Scheduler().add_new_object(self._update_buoy, self, run_in=0)

	def _update_buoy(self, remove_only=False):
		"""Draw a buoy at the move target if the ship is moving."""
		if self.owner is None or not self.owner.is_local_player:
			return
		move_target = self.get_move_target()

		ship_id = self.worldid
		session = self.session # this has to happen here,
		# cause a reference to self in a temporary function is implemented
		# as a hard reference, which causes a memory leak
		def tmp():
			session.view.renderer['GenericRenderer'].removeAll("buoy_" + str(ship_id))
		tmp() # also remove now

		if remove_only:
			return

		if move_target != None:
			# set remove buoy callback
			self.add_move_callback(tmp)

			loc = fife.Location(self.session.view.layers[LAYERS.OBJECTS])
			loc.thisown = 0  # thisown = 0 because the genericrenderernode might delete it
			coords = fife.ModelCoordinate(move_target.x, move_target.y)
			coords.thisown = 1 # thisown = 1 because setLayerCoordinates will create a copy
			loc.setLayerCoordinates(coords)
			self.session.view.renderer['GenericRenderer'].addAnimation(
				"buoy_" + str(self.worldid), fife.RendererNode(loc),
				horizons.main.fife.animationloader.loadResource("as_buoy0+idle+45")
			)

	def find_nearby_ships(self, radius=15):
		# TODO: Replace 15 with a distance dependant on the ship type and any
		# other conditions.
		ships = self.session.world.get_ships(self.position, radius)
		if self in ships:
			ships.remove(self)
		return ships

	def get_tradeable_warehouses(self, position=None):
		"""Returns warehouses this ship can trade with w.r.t. position, which defaults to the ships ones."""
		if position is None:
			position = self.position
		return self.session.world.get_warehouses(position, self.radius, self.owner, include_tradeable=True)

	def get_location_based_status(self, position):
		warehouses = self.get_tradeable_warehouses(position)
		if warehouses:
			warehouse = warehouses[0] # TODO: don't ignore the other possibilities
			player_suffix = u''
			if warehouse.owner is not self.owner:
				player_suffix = u' ({name})'.format(name=warehouse.owner.name)
			return u'{name}{suffix}'.format(name=warehouse.settlement.get_component(NamedComponent).name,
			                                suffix=player_suffix)
		return None

	def get_status(self):
		"""Return the current status of the ship."""
		if hasattr(self, 'route') and self.route.enabled:
			return self.route.get_ship_status()
		elif self.is_moving():
			target = self.get_move_target()
			location_based_status = self.get_location_based_status(target)
			if location_based_status is not None:
				#xgettext:python-format
				return (_('Going to {location}').format(location=location_based_status), target)
			#xgettext:python-format
			return (_('Going to {x}, {y}').format(x=target.x, y=target.y), target)
		else:
			location_based_status = self.get_location_based_status(self.position)
			if location_based_status is not None:
				#xgettext:python-format
				return (_('Idle at {location}').format(location=location_based_status), self.position)
			#xgettext:python-format
			return (_('Idle at {x}, {y}').format(x=self.position.x, y=self.position.y), self.position)

class PirateShip(Ship):
	"""Represents a pirate ship."""
	pass

class TradeShip(Ship):
	"""Represents a trade ship."""
	health_bar_y = -220

	def __init__(self, x, y, **kwargs):
		super(TradeShip, self).__init__(x, y, **kwargs)

	def _possible_names(self):
		return [ _(u'Trader') ]

class FisherShip(FisherShipCollector, Ship):
	"""Represents a fisher ship."""
	pather_class = FisherShipPather
	health_bar_y = -50

	in_ship_map = False # (#1023)

	def _update_buoy(self):
		pass # no buoy for the fisher
