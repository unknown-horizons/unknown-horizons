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


from game.world.units.unit import Unit
from game.world.storage import ArbitraryStorage
import game.main 


class Carriage(Unit, ArbitraryStorage):
	"""A Carriage that gets pickups for buildings
	"""
	def __init__(self, size, building):
		"""
		@param size: the size of the storage in the carriage
		@param building: the building that the carriage works for. Has to be instance of Consumer.
		"""
		self.building = building
		# this makes cariage position _in_ the building
		Unit.__init__(self, self.building.x, self.building.y)
		ArbitraryStorage.__init__(self, 1, size)
		# target: [building, resource_id,  amount]
		self.target = []
		
		self.start()
		# test during development:
		#assert(len(building.consumed_res) > 0 )
		
	def search_pickup(self, already_scanned_min = 0):
		"""Finds out, which resource it should get from where and get it
		@param already_scanned_min: all values smaller than this are not scanned
		@return: bool wether pickup was found
		"""
		import pdb
		pdb.set_trace()
		min = 10000
		# scan for resources, where more then the already scanned tons are stored
		# and less then the current minimum
		needed_res = []
		for res in self.building.consumed_res:
			stored = self.building.get_value(res)
			# check if we already scanned for pickups for this res
			if stored >= already_scanned_min:
				continue
			# if new minimum, discard every other value cause it's higher
			if stored < min:
				min = stored
				needed_res.clear()
				needed_res.append(res)
			elif stored == min:
				needed_res.append(res)
		
		# if none found, no pickup available
		if len(needed_res) == 0:
			return False
	
		# search for available pickups for needed_res
		# values of possible_pickup: [building, resource, amount, distance, rating]
		possible_pickups = []
		for b in building.settlement.buildings:
			if isinstance(b, Producer):
				# check if building produces one of the needed_res and if it has some available
				for res in needed_res:
					if res in b.prod_res.keys():
						# check if another carriage is already on the way for same res
						for carriage in b.pickup_carriages:
							if carriage.target[1] == res:
								break
						else:
							continue
						stored = b.get_value(res)
						if stored > 0:
							possible_pickups.append([b, res, stored, 0, 0])
							
		# if no possible pickups, retry with changed min to scan for other res
		if len(possible_pickups) == 0:
			return self.search_pickup(min)
							
		# calculate distance 
		max_amount = 0
		max_distance = 0
		for pickup in possible_pickups:
			pickup[3] = ((pickup[0].x - self.building.x)**2) + ((pickup[0].y - self.building.y))
			if pickup[3] > max_distance:
				max_distance = pickup[3]
			if pickup[2] > max_amount:
				max_amount = pickup[2]
			
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
		self.target[2] = self.target[0].get_value(self.target[1])
		# check for carriage size overflow
		if self.target[2] > self.size:
			self.target[2] = self.size
		# check for home building storage size overflow
		if self.target[2] > (self.building.get_size(self.target[1]) - self.building.get_value(self.target[1])):
			self.target[2] = (self.building.get_size(self.target[1]) - self.building.get_value(self.target[1]))
		self.target[0].pickup_carriages.append(self)
		self.move(self.target[0].x, self.target[0].y, self.reached_pickup)
		
		## TODO: create a list in the building, that owns a carriage
		##       and ensure there, that the space for the resources,
		##       which the carriage gets, isn't filled up
		
		return True
			
	def reached_pickup(self):
		"""Called when the carriage reaches target building
		"""
		pickup_amount = self.target[0].pickup_resources(self.target[1], self.size)
		self.alter_inventory(self.target[1], pickup_amount)
		self.target[0].pickup_carriages.remove(self)
		self.move(self.building.x, self.building.y, self.reached_home)
	
	def reached_home(self):
		"""Called when carriage is in the building, it was assigned to
		"""
		self.building.alter_inventory(self.target[1], self.target[2])
		self.alter_inventory(self.target[1], -self.target[2])
		assert(self.get_size(self.target[1]) == 0)
		self.target.clear()
		self.start()
			
	def start(self):
		"""Sends carriage on it's way"""
		if not self.search_pickup():
			game.main.session.scheduler.add_new_object(self.start, (self, game.main.session.timer.ticks_per_second / 2))
			
	
