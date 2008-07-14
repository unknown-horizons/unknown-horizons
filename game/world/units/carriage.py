# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

#import math
from game.world.units.unit import Unit
from game.world.storage import ArbitraryStorage
from game.util.rect import Rect
from game.util.point import Point
import game.main

class BuildingCarriage(Unit):
	searchJobInterval = 2
	"""A BuildingCarriage that gets pickups for buildings

	building has to support:
	* attribute 'inventory', which supports get_value(res) and get_size(res)
	* x and y coords

	Can be subclassed for use in e.g. Animal
	"""
	def __init__(self, building, inventory = None, slots = 1, size = 6):
		"""
		@param size: the size of the storage in the carriage
		@param building: the building that the carriage works for. Has to be instance of Consumer.
		"""
		if inventory is None:
			self.inventory = ArbitraryStorage(slots, size)
		else:
			self.inventory = inventory
		self.building = building
		self.radius = self.building.radius
		# this makes cariage position _in_ the building
		Unit.__init__(self, self.building.x, self.building.y)
		self.hide()
		# target: [building, resource_id,  amount]
		self.target = []

		game.main.session.scheduler.add_new_object(self.send, self, game.main.session.timer.ticks_per_second*self.__class__.searchJobInterval)
		# test during development:
		#assert(len(building.consumed_res) > 0 )

	def get_consumed_resources(self):
		""" This can and should be overwritten in subclass, if needed
		@return: list [ (needed_res_id, stored), ... ]
		"""
		building_needed_res = self.building.get_consumed_res()
		needed_res = []
		for res in building_needed_res:
			needed_res.append((res, self.building.inventory.get_value(res)))
		return needed_res

	def get_possible_pickup_places(self):
		""" Returns places that should be analysed for pickup
		@return: list: [ (building, [ produced_res_id, .. ] ) ]
		"""
		# this is imported here, cause otherwise, there's some error
		# that probably is caused by circular dependencies
		from game.world.building.producer import Producer

		possible_pickup_places = []
		for b in self.building.settlement.buildings:
			if b == self.building:
				continue
			if isinstance(b, Producer):
				possible_pickup_places.append( (b, b.prod_res ) )
		return possible_pickup_places

	def get_position(self):
		#return Rect(self.building.x, self.building.y, self.building.x+self.building.size[0], self.building.y+self.building.size[1])
		return Point(self.building.x, self.building.y)

	def search_job(self, already_scanned_min = 0):
		"""Finds out, which resource it should get from where and get it
		@param already_scanned_min: all values smaller than this are not scanned
		@return: bool wether pickup was found
		"""
		#print 'SEARCH_JOB IN',self.building.id,"CAR", self.id
		min = 10000
		# scan for resources, where more then the already scanned tons are stored
		# and less then the current minimum
		needed_res = []
		consumed_res = self.get_consumed_resources()
		for res in consumed_res:
			# check if we already scanned for pickups for this res
			if res[1] < already_scanned_min:
				continue
			# if new minimum, discard every other value cause it's higher
			if res[1] < min:
				min = res[1]
				needed_res = []
				needed_res.append(res[0])
			elif res[1] == min:
				needed_res.append(res)

		# if none found, no pickup available
		if len(needed_res) == 0:
			#print 'CAR: NO needed res'
			return False

		# search for available pickups for needed_res
		# values of possible_pickup: [building, resource, amount, distance, rating]
		max_amount = 0
		max_distance = 0
		possible_pickups = []

		possible_pickup_places = self.get_possible_pickup_places()
		position = self.get_position()
		for b in possible_pickup_places:
			# check if building produces one of the needed_res and if it has some available
			for res in needed_res:
				if res in b[1]:
					# check if another carriage is already on the way for same res
					#if len(b[0].pickup_carriages) > 0:
					#	import pdb
					#	pdb.set_trace()
					if len([ carriage for carriage in b[0].pickup_carriages if carriage.target[1] == res ]) > 0:
						break

					stored = b[0].inventory.get_value(res)
					if stored > 0:
						## TODO: use Rect in buildings and use their Rect here
						#selfrect = Rect(self.unit_position[0], self.unit_position[1], self.unit_position[0]+1, self.unit_position[1]+1)
						#selfrect = Rect(self.unit_position[0], self.unit_position[1], self.unit_position[0]+1, self.unit_position[1]+1)
						brect = Rect(b[0].x, b[0].y, b[0].x+b[0].size[0], b[0].y+b[0].size[1])
						distance = brect.distance( position )
						#distance = math.sqrt( \
						#	(( (b.x+b.size[0]/2) - (self.building.x+self.building.size[0]/2) )**2) + \
						#	(( (b.y+b.size[1]/2) - (self.building.y+self.building.size[1]/2) )**2) \
						#	)
						if distance > self.radius:
							break
						if stored > max_amount:
							max_amount = stored
						if distance > max_distance:
							max_distance = distance
						possible_pickups.append([b[0], res, stored, distance, 0])

		# if no possible pickups, retry with changed min to scan for other res
		if len(possible_pickups) == 0:
			#print 'CAR: NO POSSIBLE FOR',needed_res
			return self.search_job(min+1)

		# development asserts
		assert(max_amount != 0)
		assert(max_distance != 0)

		max_rating = self.calc_best_pickup(possible_pickups, max_amount, max_distance)

		# get pickup
		# save target building and res to pick up,
		self.target = [max_rating[1][0], max_rating[1][1], 0]
		self.target[2] = self.target[0].inventory.get_value(self.target[1])
		# check for carriage size overflow
		if self.target[2] > self.inventory.get_size(self.target[1]):
			self.target[2] = self.inventory.get_size(self.target[1])
		# check for home building storage size overflow
		if self.target[2] > (self.building.inventory.get_size(self.target[1]) - self.building.inventory.get_value(self.target[1])):
			self.target[2] = (self.building.inventory.get_size(self.target[1]) - self.building.inventory.get_value(self.target[1]))
		self.target[0].pickup_carriages.append(self)
		self.show()
		self.move(self.target[0].x, self.target[0].y, self.reached_pickup)

		#print 'CAR:', self.id, 'CURRENT', self.get_position().x, self.get_position().y
		#print 'CAR:', self.id, 'GETTING', self.target[0].x, self.target[0].y
		return True

	def reached_pickup(self):
		"""Called when the carriage reaches target building
		"""
		self.transfer_pickup()
		self.move(self.building.x, self.building.y, self.reached_home)

	def transfer_pickup(self):
		pickup_amount = self.target[0].pickup_resources(self.target[1], self.target[2])
		self.inventory.alter_inventory(self.target[1], pickup_amount)
		self.target[0].pickup_carriages.remove(self)

	def reached_home(self):
		"""Called when carriage is in the building, it was assigned to
		"""
		self.building.inventory.alter_inventory(self.target[1], self.target[2])
		self.inventory.alter_inventory(self.target[1], -self.target[2])
		assert(self.inventory.get_value(self.target[1]) == 0)
		# check if this cleanup is alright
		# this is also done this way somewhere else
		self.target = []
		self.hide()
		self.send()

	def send(self):
		"""Sends carriage on it's way"""
		#print 'SENT'
		if not self.search_job():
			game.main.session.scheduler.add_new_object(self.send, self, game.main.session.timer.ticks_per_second*self.__class__.searchJobInterval)

	def calc_best_pickup(self, possible_pickups, max_amount, max_distance):
		""" chooses a pickup """
		max_rating = [0, None]
		for pickup in possible_pickups:
			pickup[4] = 2 + pickup[2] / max_amount - pickup[3] / max_distance # 2+ ensures positiv value
			if pickup[4] > max_rating[0]:
				max_rating[0] = pickup[4]
				max_rating[1] = pickup
		return max_rating
