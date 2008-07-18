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


import math
from game.world.units.unit import Unit
from game.world.storage import ArbitraryStorage
from game.util import Rect, Point
from game.world.pathfinding import Movement
import game.main


class Carriage(Unit):
	searchJobInterval = 2
	movement = Movement.CARRIAGE_MOVEMENT
	"""A BuildingCarriage that gets pickups for buildings
	Can be subclassed for use in e.g. Animal
	"""
	def __init__(self, consumer, inventory = None, slots = 1, size = 6, attached_building = None, hide_when_idle = False):
		"""
		@param size: the size of the storage in the carriage
		@param consumer: the building that the carriage works for. Has to be instance of Consumer.
		@param attached_building: the building that owns the carriage (influences the possible path nodes of the carriage). Usually, this is the same as consumer. This is e.g. used by Animal, which gathers resources for itself, but can only move in the radius of its animal farm.
		@var hide_when_idle: hide the carrige, when it waits for a new producer to pick up ressources.
		carriage_consumer has to support:
		  * attribute 'inventory' or parameter 'inventory', which supports get_value(), alter_inventory() and get_size()
		carriage_attached_building has to support:
		  * x and y coords
		  * radius
		"""
		if inventory is None:
			self.inventory = ArbitraryStorage(slots, size)
		else:
			self.inventory = inventory
		self.carriage_consumer = consumer
		self.carriage_attached_building = attached_building if attached_building is not None else self.carriage_consumer
		self.radius = self.carriage_attached_building.radius
		# this makes cariage position _in_ the building

		self.home_position = Point(self.carriage_attached_building.x + self.carriage_attached_building.size[0]/2 - 1, self.carriage_attached_building.y + self.carriage_attached_building.size[1]/2 - 1)
		Unit.__init__(self, self.home_position.x, self.home_position.y)
		# target: [building, resource_id,  amount]
		self.target = []

		game.main.session.scheduler.add_new_object(self.send, self, game.main.session.timer.ticks_per_second*self.__class__.searchJobInterval)
		# test during development:
		#assert(len(building.consumed_res) > 0 )
		self.hide_when_idle = hide_when_idle
		if self.hide_when_idle:
			self.hide()

	def get_position(self):
		#return Rect(self.carriage_home.x, self.carriage_home.y, self.carriage_home.x+self.carriage_home.size[0], self.carriage_home.y+self.carriage_home.size[1])
		#return Point(self.carriage_home.x, self.carriage_home.y)
		return self.unit_position

	def search_job(self, already_scanned_min = 0):
		"""Finds out, which resource it should get from where and get it
		@param already_scanned_min: all values smaller than this are not scanned
		@return: bool wether pickup was found
		"""
		#print 'SEARCH_JOB IN',self.carriage_consumer.id,"CAR", self.id, self
		print self.id, 'SEARCH JOB w min', already_scanned_min
		min = 100000
		# scan for resources, where more then the already scanned tons are stored
		# and less then the current minimum
		needed_res = []
		consumed_res = self.get_consumed_resources()

		for res in consumed_res:
			# check if we already scanned for pickups for this res
			if res[1] < already_scanned_min:
				continue

			# check if storage is already full
			if res[1] == self.carriage_consumer.inventory.get_size(res[0]):
				continue

			# if new minimum, discard every other value cause it's higher
			if res[1] < min:
				next_to_min = min
				min = res[1]
				needed_res = []
				needed_res.append(res[0])
			elif res[1] == min:
				needed_res.append(res[0])

		# if none found, no pickup available
		if len(needed_res) == 0:
			print 'CAR',self.id,' NO needed res'
			return False

		print 'CAR', self.id,'NEEDED', needed_res

		# search for available pickups for needed_res
		# values of possible_pickup: [building, resource, amount, distance, rating]
		max_amount = 0
		max_distance = 0
		possible_pickups = []

		possible_pickup_places = self.get_possible_pickup_places()
		position = self.get_position()

		#print 'CAR', self.id, 'POS PICK', [ possible_pickup_places[i][1] for i in xrange(0, len(possible_pickup_places)) ]

		# if carriage is in it's building, it has to be able to reach
		# everything within the building-radius, not its own radius
		if position == self.home_position:
			position = Rect( Point(self.carriage_attached_building.x, self.carriage_attached_building.y), self.carriage_attached_building.size[0], self.carriage_attached_building.size[1])
			radius = self.carriage_attached_building.radius
		else:
			radius = self.radius

		for b in possible_pickup_places:
			# check if building produces one of the needed_res and if it has some available
			for res in needed_res:
				if res in b[1]:
					# check if another carriage is already on the way for same res
					for carriage in b[0].pickup_carriages:
						print carriage.target
					if len([ carriage for carriage in b[0].pickup_carriages if carriage.target[1] == res ]) > 0:
						print 'CAR', self.id, 'other carriage'
						break

					stored = b[0].inventory.get_value(res)
					if stored > 0:
						## TODO: use Rect in buildings and use their Rect here
						brect = Rect(Point(b[0].x, b[0].y), b[0].size[0], b[0].size[1])
						distance = math.floor(brect.distance( position ) )
						if distance > self.radius:
							print 'CAR', self.id, 'to far', distance, self.radius
							break
						if stored > max_amount:
							max_amount = stored
						if distance > max_distance:
							max_distance = distance
						possible_pickups.append([b[0], res, stored, distance, 0])
					else:
						print 'CAR', self.id, 'nix stored of', res

		# if no possible pickups, retry with changed min to scan for other res
		if len(possible_pickups) == 0:
			#print 'CAR: NO POSSIBLE FOR ',needed_res, 'at', self.carriage_consumer.id
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
		if self.target[2] > (self.carriage_consumer.inventory.get_size(self.target[1]) - self.carriage_consumer.inventory.get_value(self.target[1])):
			self.target[2] = (self.carriage_consumer.inventory.get_size(self.target[1]) - self.carriage_consumer.inventory.get_value(self.target[1]))

		self.target[0].pickup_carriages.append(self)

		if self.hide_when_idle:
			self.show()
		move_possible = self.move(Point(self.target[0].x, self.target[0].y), self.reached_pickup)

		if not move_possible:
			self.target = []
			return False

		print 'CAR:', self.id, 'CURRENT', self.get_position().x, self.get_position().y
		print 'CAR:', self.id, 'GETTING', self.target[0].x, self.target[0].y
		return True

	def reached_pickup(self):
		"""Called when the carriage reaches target building
		"""
		print self.id, 'REACHED PICKUP'
		self.transfer_pickup()
		self.move(Point(self.home_position.x, self.home_position.y), self.reached_home)

	def transfer_pickup(self):
		pickup_amount = self.target[0].pickup_resources(self.target[1], self.target[2])
		self.inventory.alter_inventory(self.target[1], pickup_amount)

		self.target[0].pickup_carriages.remove(self)

	def reached_home(self):
		"""Called when carriage is in the building, it was assigned to
		"""
		print self.id, 'REACHED HOME'
		self.carriage_consumer.inventory.alter_inventory(self.target[1], self.target[2])
		self.inventory.alter_inventory(self.target[1], -self.target[2])
		assert(self.inventory.get_value(self.target[1]) == 0)
		self.target = []
		if self.hide_when_idle:
			self.hide()
		self.send()

	def send(self):
		"""Sends carriage on it's way"""
		print 'SEND'
		if not self.search_job():
			game.main.session.scheduler.add_new_object(self.send, self, game.main.session.timer.ticks_per_second*self.__class__.searchJobInterval)

	def calc_best_pickup(self, possible_pickups, max_amount, max_distance):
		""" chooses a pickup according to their current storage value and distance
		"""
		max_rating = [0, None]
		for pickup in possible_pickups:
			pickup[4] = 2 + pickup[2] / max_amount - pickup[3] / max_distance # 2+ ensures positiv value
			if pickup[4] > max_rating[0]:
				max_rating[0] = pickup[4]
				max_rating[1] = pickup
		return max_rating

	# functions to be overwritten:
	def get_consumed_resources(self):
		""" Returns list of resources, that the building consumes
		@return: list [ (needed_res_id, stored), ... ]
		"""
		assert(False and pi == 3)

	def get_possible_pickup_places(self):
		""" Returns places that should be analysed for pickup
		@return: list: [ (building, [ produced_res1, produced_res2, ..  ] ) ]
		"""
		assert(False and pi == 3)


class BuildingCarriage(Carriage):
	"""Gets resources for buildings (consumer)"""
	def __init__(self, consumer, inventory = None, slots = 1, size = 6, attached_building = None):
		super(BuildingCarriage, self).__init__(consumer, inventory = inventory, slots = slots, size = size, attached_building = attached_building, hide_when_idle=True)

	def get_consumed_resources(self):
		building_needed_res = self.carriage_consumer.get_consumed_res()
		needed_res = []
		for res in building_needed_res:
			needed_res.append((res, self.carriage_consumer.inventory.get_value(res)))
		return needed_res

	def get_possible_pickup_places(self):
		# this is imported here, cause otherwise, there's some error
		# that probably is caused by circular dependencies
		from game.world.building.producer import Producer

		possible_pickup_places = []
		for b in self.carriage_attached_building.settlement.buildings:
			if b == self.carriage_attached_building:
				continue
			if isinstance(b, Producer):
				possible_pickup_places.append( (b, b.prod_res ) )
		return possible_pickup_places

class StorageCarriage(BuildingCarriage):
	""" This represents a carriage for storage tents/branch offices.
	It is exactly the same as a BuildingCarriage, except that it moves on a road
	"""
	movement = Movement.STORAGE_CARRIAGE_MOVEMENT

class AnimalCarriage(BuildingCarriage):
	searchJobInterval = 10
	""" Collects resources produced by animals (german: Tierhueter)

	More exactly: brings animals, that have produced something,
	to the building, where resources are transfaired (this is TODO)

	Has to be attached to an instance of AnimalFarm.
	"""
	def get_possible_pickup_places(self):
		ret = []
		# this could be optimised by caching the results
		# only problem: if new animals are born, they have to be added
		# solution: an animals is just born when another one gets slaughtered
		# so the old instance could be reused
		for animal in self.carriage_attached_building.animals:
			ret.append( (animal.production, animal.production.prod_res) )
		return ret

	def reached_pickup(self):
		self.move(Point(self.home_position.x, self.home_position.y), self.get_animal_pickup)
		self.get_animal(self.target[0]).move(Point(self.home_position.x, self.home_position.y))

	def get_animal_pickup(self):
		self.transfer_pickup()
		animal = self.get_animal(self.target[0])
		self.reached_home()
		animal.send()

	def get_animal(self, production):
		""" Returns the animal, whose producer == production """
		for animal in self.carriage_attached_building.animals:
			if animal.production == self.target[0]:
				return animal

