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
import game.main 


class Carriage(Unit):
	"""A Carriage that gets pickups for buildings
	"""
	def __init__(self, building, slots = 1, size = 6):
		"""
		@param size: the size of the storage in the carriage
		@param building: the building that the carriage works for. Has to be instance of Consumer.
		"""
		self.inventory = ArbitraryStorage(slots, size)
		self.building = building
		# this makes cariage position _in_ the building
		Unit.__init__(self, self.building.x, self.building.y)
		# target: [building, resource_id,  amount]
		self.target = []
		
		#self.start()
		game.main.session.scheduler.add_new_object(self.send, self, game.main.session.timer.ticks_per_second*3)
		# test during development:
		#assert(len(building.consumed_res) > 0 )
		
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
		building_needed_res = self.building.get_needed_resources()
		for res in building_needed_res:
			stored = self.building.inventory.get_value(res)
			# check if we already scanned for pickups for this res
			if stored < already_scanned_min:
				continue
			# if new minimum, discard every other value cause it's higher
			if stored < min:
				min = stored
				needed_res = []
				needed_res.append(res)
			elif stored == min:
				needed_res.append(res)
		
		# if none found, no pickup available
		if len(needed_res) == 0:
			#print 'CAR: NO needed res w min', min
			return False
	
		# search for available pickups for needed_res
		# values of possible_pickup: [building, resource, amount, distance, rating]
		max_amount = 0
		max_distance = 0
		possible_pickups = []
		
		for b in self.building.settlement.buildings:
			# maybe use is instead of = here
			if b == self.building:
				continue
			from game.world.building.producer import Producer
			if isinstance(b, Producer):
				# check if building produces one of the needed_res and if it has some available
				for res in needed_res:
					if res in b.prod_res:
						# check if another carriage is already on the way for same res
						for carriage in b.pickup_carriages:
							if carriage.target[1] == res:
								break
						stored = b.inventory.get_value(res)
						if stored > 0:
							distance = math.sqrt( \
								(( (b.x+b.size[0]/2) - (self.building.x+self.building.size[0]/2) )**2) + \
								(( (b.y+b.size[1]/2) - (self.building.y+self.building.size[1]/2) )**2) \
								)
							if distance > self.building.radius:
								break
							if stored > max_amount:
								max_amount = stored
							if distance > max_distance:
								max_distance = distance
							possible_pickups.append([b, res, stored, distance, 0])
							
		# if no possible pickups, retry with changed min to scan for other res
		if len(possible_pickups) == 0:
			#print 'CAR: NO POSSIBLE FOR',needed_res
			return self.search_job(min+1)
							
		# calculate relative values to max for decision making
		max_rating = [0, None]
		for pickup in possible_pickups:
			pickup[4] = pickup[2] / max_amount + pickup[3] / max_distance
			if pickup[4] > max_rating[0]:
				max_rating[0] = pickup[4]
				max_rating[1] = pickup
			
		# get pickup 
		# save target building and res to pick up, 
		self.target = [max_rating[1][0], max_rating[1][1], 0]
		self.target[2] = self.target[0].inventory.get_value(self.target[1])
		# check for carriage size overflow
		if self.target[2] > self.inventory.size:
			self.target[2] = self.inventory.size
		# check for home building storage size overflow
		if self.target[2] > (self.building.inventory.get_size(self.target[1]) - self.building.inventory.get_value(self.target[1])):
			self.target[2] = (self.building.inventory.get_size(self.target[1]) - self.building.inventory.get_value(self.target[1]))
		self.target[0].pickup_carriages.append(self)
		self.move(self.target[0].x, self.target[0].y, self.reached_pickup)
		
		## TODO: create a list in the building, that owns a carriage
		##       and ensure there, that the space for the resources,
		##       which the carriage gets, isn't filled up
		
		#print 'CAR: GETTING',self.target
		return True
			
	def reached_pickup(self):
		"""Called when the carriage reaches target building
		"""
		pickup_amount = self.target[0].pickup_resources(self.target[1], self.target[2])
		# maybe remove pickup_amount and replace it with self.target[2]
		#print "ACCTUAL PICUP", pickup_amount
		#assert(pickup_amount == self.target[2])
		self.inventory.alter_inventory(self.target[1], pickup_amount)
		self.target[0].pickup_carriages.remove(self)
		self.move(self.building.x, self.building.y, self.reached_home)
	
	def reached_home(self):
		"""Called when carriage is in the building, it was assigned to
		"""
		self.building.inventory.alter_inventory(self.target[1], self.target[2])
		self.inventory.alter_inventory(self.target[1], -self.target[2])
		assert(self.inventory.get_value(self.target[1]) == 0)
		# check if this cleanup is alright
		# this is also done this way somewhere else
		self.target = []
		self.send()
			
	def send(self):
		"""Sends carriage on it's way"""
		if not self.search_job():
			game.main.session.scheduler.add_new_object(self.send, self, game.main.session.timer.ticks_per_second*3)
			
	
