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

import logging

import horizons.main

from horizons.scheduler import Scheduler
from horizons.util import Point, Callback, WorldObject, Circle
from horizons.constants import RES, UNITS, BUILDINGS
from horizons.ext.enum import Enum
from horizons.ai.generic import AIPlayer
from horizons.world.storageholder import StorageHolder
from horizons.command.unit import CreateUnit
from horizons.world.units.ship import PirateShip, TradeShip, FisherShip
from horizons.world.units.movingobject import MoveNotPossible


class Pirate(AIPlayer):
	"""A pirate ship moving randomly around. If another ship comes into the reach
	of it, it will be followed for a short time."""

	shipStates = Enum.get_extended(AIPlayer.shipStates, 'chasing_ship', 'going_home')

	log = logging.getLogger("ai.pirate")

	caught_ship_radius = 5
	home_radius = 2
	sight_radius = 15

	def __init__(self, session, id, name, color, **kwargs):
		super(Pirate, self).__init__(session, id, name, color, **kwargs)

		# choose a random water tile on the coast and call it home
		self.home_point = self.session.world.get_random_possible_coastal_ship_position()
		self.log.debug("Pirate: home at (%d, %d), radius %d" % (self.home_point.x, self.home_point.y, self.home_radius))

		# create a ship and place it randomly (temporary hack)
		point = self.session.world.get_random_possible_ship_position()
		ship = CreateUnit(self.worldid, UNITS.PIRATE_SHIP_CLASS, point.x, point.y)(issuer=self.session.world.player)
		self.ships[ship] = self.shipStates.idle
		self.calculate_visibility_points(ship)

		for ship in self.ships.keys():
			Scheduler().add_new_object(Callback(self.send_ship, ship), self)
			Scheduler().add_new_object(Callback(self.lookout, ship), self, 8, -1)

	@staticmethod
	def get_nearest_player_ship(base_ship):
		lowest_distance = None
		nearest_ship = None
		for ship in base_ship.find_nearby_ships():
			if isinstance(ship, (PirateShip, TradeShip)):
				continue # don't attack these ships
			distance = base_ship.position.distance_to_point(ship.position)
			if lowest_distance is None or distance < lowest_distance:
				lowest_distance = distance
				nearest_ship = ship
		return nearest_ship

	def lookout(self, pirate_ship):
		if self.ships[pirate_ship] != self.shipStates.going_home:
			ship = self.get_nearest_player_ship(pirate_ship)
			if ship:
				self.log.debug("Pirate: Scout found ship: %s" % ship.name)
				self.send_ship(pirate_ship)
			else:
				self.predict_player_position(pirate_ship)

	def save(self, db):
		super(Pirate, self).save(db)
		db("UPDATE player SET is_pirate = 1 WHERE rowid = ?", self.worldid)
		db("INSERT INTO pirate_home_point(x, y) VALUES(?, ?)", self.home_point.x, self.home_point.y)

		for ship in self.ships:
			# prepare values
			ship_state = self.ships[ship]
			current_callback = Callback(self.lookout, ship)
			calls = Scheduler().get_classinst_calls(self, current_callback)
			assert len(calls) == 1, "got %s calls for saving %s: %s" %(len(calls), current_callback, calls)
			remaining_ticks = max(calls.values()[0], 1)

			db("INSERT INTO pirate_ships(rowid, state, remaining_ticks) VALUES(?, ?, ?)",
				ship.worldid, ship_state.index, remaining_ticks)

	def _load(self, db, worldid):
		super(Pirate, self)._load(db, worldid)
		home = db("SELECT x, y FROM pirate_home_point")[0]
		self.home_point = Point(home[0], home[1])
		self.log.debug("Pirate: home at (%d, %d), radius %d" % (self.home_point.x, self.home_point.y, self.home_radius))

	def load_ship_states(self, db):
		# load ships one by one from db (ship instances themselves are loaded already, but
		# we have to use them here)
		for ship_id, state_id, remaining_ticks in \
				db("SELECT rowid, state, remaining_ticks FROM pirate_ships"):
			state = self.shipStates[state_id]
			ship = WorldObject.get_object_by_id(ship_id)
			self.ships[ship] = state
			assert remaining_ticks is not None
			Scheduler().add_new_object(Callback(self.lookout, ship), self, remaining_ticks, -1, 8)
			ship.add_move_callback(Callback(self.ship_idle, ship))
			self.calculate_visibility_points(ship)

	def send_ship(self, pirate_ship):
		self.log.debug('Pirate %s: send_ship(%s) start transition: %s' % (self.worldid, pirate_ship.name, self.ships[pirate_ship]))
		done = False

		#transition the pirate ship state to 'idle' once it is inside home circumference
		if pirate_ship.position.distance_to_point(self.home_point) <= self.home_radius and \
			self.ships[pirate_ship] == self.shipStates.going_home:        
			self.ships[pirate_ship] = self.shipStates.idle
			self.log.debug('Pirate %s: send_ship(%s) new state: %s' % (self.worldid, pirate_ship.name, self.ships[pirate_ship]))

		if self.ships[pirate_ship] != self.shipStates.going_home:
			if self._chase_closest_ship(pirate_ship):
				done = True

		if not done:
			ship = self.get_nearest_player_ship(pirate_ship)
			if self.ships[pirate_ship] == self.shipStates.chasing_ship and (ship is None or \
					ship.position.distance_to_point(pirate_ship.position) <= self.caught_ship_radius):
				# caught the ship, go home
				for point in self.session.world.get_points_in_radius(self.home_point, self.home_radius, shuffle = True):
					try:
						pirate_ship.move(point, Callback(self.send_ship, pirate_ship))
					except MoveNotPossible:
						continue
					self.log.debug('Pirate %s: send_ship(%s) going home (%d, %d)' % (self.worldid, pirate_ship.name, point.x, point.y))
					self.ships[pirate_ship] = self.shipStates.going_home
					done = True
					break

		#visit those points which are most frequented by player
		if not done and self.ships[pirate_ship] != self.shipStates.going_home:
			self.predict_player_position(pirate_ship)

		self.log.debug('Pirate %s: send_ship(%s) new state: %s' % (self.worldid, pirate_ship.name, self.ships[pirate_ship]))

	def _chase_closest_ship(self, pirate_ship):
		ship = self.get_nearest_player_ship(pirate_ship)
		if ship:
			# The player is in sight here
			# Note down all the point's visibility the player belongs to
			for point in self.visibility_points:
				if ship.position.distance_to_point(point[0]) <= self.sight_radius:
					point[1] += 1	# point[1] represents the chance of seeing a player
			if ship.position.distance_to_point(pirate_ship.position) <= self.caught_ship_radius:
				self.ships[pirate_ship] = self.shipStates.chasing_ship
				return False # already caught it

			# move ship there:
			for point in self.session.world.get_points_in_radius(ship.position, self.caught_ship_radius - 1):
				try:
					pirate_ship.move(point, Callback(self.send_ship, pirate_ship))
				except MoveNotPossible:
					continue
				self.log.debug('Pirate %s: chasing %s (next point %d, %d)' % (self.worldid, pirate_ship.name, point.x, point.y))
				self.ships[pirate_ship] = self.shipStates.chasing_ship
				return True
		return False


	def predict_player_position(self, pirate_ship):
		"""Moves the pirate_ship to one of it's visibility points where 
		   the player has spent the maximum time"""

		self.ships[pirate_ship] = self.shipStates.moving_random
		self.log.debug('Pirate %s: send_ship(%s) new state: %s' % (self.worldid, pirate_ship.name, self.ships[pirate_ship]))
		# See if we have reached the destination
		if pirate_ship.position.distance_to_point(self.visibility_points[0][0]) <= self.home_radius:
			# Every unsuccessful try halves the chances of ship being on that point next time
			self.visibility_points[0][1] = self.visibility_points[0][1]/2	
		
			self.visibility_points.sort(key = self._sort_preference)	
			max_point = self.visibility_points[0]
			if max_point[1] is 0:		# choose a random location in this case
				# TODO: If this seems inefficient in larger maps, change to 'shift elements by 1'
				index = self.session.random.randint(0, len(self.visibility_points)-1)
				max_point = self.visibility_points[index]
				self.visibility_points[index] = self.visibility_points[0]
				self.visibility_points[0] = max_point
			self.visible_player = [True]*len(self.visibility_points)
			self.log.debug('Pirate %s: ship %s, Frequencies of visibility_points:' % (self.worldid, pirate_ship.name))
			for point in self.visibility_points:
				self.log.debug('(%d, %d) -> %d' %(point[0].x, point[0].y, point[1]))
		# Consider the points that are being visited while visiting the destination point, and reduce
		# the frequency values for them
		elif len(self.visible_player) is len(self.visibility_points):
			for point in self.visibility_points:
				index = self.visibility_points.index(point)
				if self.visible_player[index] and pirate_ship.position.distance_to_point\
					(self.visibility_points[index][0]) <= self.home_radius:
					self.visibility_points[index][1] = self.visibility_points[index][1]/2 
					self.visible_player[index] = False
		try:
			pirate_ship.move(self.visibility_points[0][00])
		except MoveNotPossible:
			self.notify_unit_path_blocked(pirate_ship)
			return

	def _sort_preference(self, a):
		return -a[1]

	def calculate_visibility_points(self, pirate_ship):
		"""Finds out the points from which the entire map will be accessible.
		Should be called only once either during initialization or loading"""
		rect = self.session.world.map_dimensions.get_corners()
		x_min, x_max, y_min, y_max = rect[0][0], rect[1][0], rect[0][0], rect[2][1]

		# Necessary points (with tolerable overlapping) which cover the entire map
		# Each element contains two values: it's co-ordinate, and frequency of player ship's visit
		self.visibility_points = []
		y = y_min+self.sight_radius
		while y <= y_max:
			x = x_min+self.sight_radius
			while x <= x_max:
				self.visibility_points.append([Point(x,y), 0])
				x += self.sight_radius  # should be 2*self.sight_radius for no overlap
			y += self.sight_radius
	
		self.log.debug("Pirate %s: %s, visibility points" % (self.worldid, pirate_ship.name))
		copy_points = list(self.visibility_points)
		for point in copy_points:
			if not self.session.world.get_tile(point[0]).is_water:	
				# Make a position compromise to obtain a water tile on the point
				for x in (3, -3, 2, -2, 1, -1, 0):
					for y in (3, -3, 2, -2, 1, -1, 0):
						new_point = Point(point[0].x+x, point[0].y+y)
						if self.session.world.get_tile(new_point).is_water:
							self.visibility_points.remove(point) #remove old point
							point[0] = new_point
							self.visibility_points.append([point[0], 0]) #add new point
							break
					if self.session.world.get_tile(point[0]).is_water: break
				if not self.session.world.get_tile(point[0]).is_water:
					self.visibility_points.remove(point)
					continue	
			self.log.debug("(%d, %d)" % (point[0].x, point[0].y))
		# A list needed to reduce visibility frequencies of a point if player is not sighted on that point
		self.visible_player = []
