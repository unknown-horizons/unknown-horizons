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

from building import Building
from game.world.units.unit import Unit
import game.main

class Producer(object):
	check_production_interval = 2
	# run self.tick every second tick (NOTE: this should be discussed)
	# running every tick currently requires all production times to be
	# a multiple of 2
	"""Class used for production buildings

	# Has to be inherited by a class that provides:
	* inventory

	This includes e.g. trees, lumberjack, weaver, storages
	"""
	def __init__(self):
		"""
		"""
		# list of produced resource
		# this is rather a shortcut, this info is also stored
		# indirectly in self.prodcution
		self.prod_res = []
		# infos about production
		self.production = {}

	
		if self.object_type == 0:
			print self.id, "Producer: IS A BUILDING"
		
		elif self.object_type == 1:
			print self.id, "Producer: IS A UNIT"
		else:
			print self.id, "Producer: UNKNOWN TYPE"
			assert(False)	
					
			
		result = game.main.db("SELECT rowid, time FROM production_line where object = ? and type = ?", self.id, self.object_type);
		for (prod_line, time) in result:
			self.production[prod_line] = {}
			self.production[prod_line]['res'] = {}
			self.production[prod_line]['time'] = time

			prod_infos = game.main.db("SELECT \
			(SELECT storage.resource FROM storage WHERE storage.rowid = production.storage) as resource, \
			(SELECT storage.storage_size FROM storage WHERE storage.rowid = production.storage) as storage_size, \
			amount \
			FROM production WHERE production_line = ?", prod_line)
			for (resource, storage_size, amount) in prod_infos:
				if amount > 0: # actually produced res
					self.prod_res.append(resource)
					if not self.inventory.hasSlot(resource):
						self.inventory.addSlot(resource, storage_size)
					if not resource in self.prod_res:
						self.prod_res.append(resource)
				if amount != 0: # produced or consumed res
					self.production[prod_line]['res'][resource] = amount

		## TODO: GUI-interface for changing active production line
		if len(self.production) == 0:
			self.active_production_line = -1
		else:
			self.active_production_line = min(self.production.keys())

		self._current_production = 0

		# save references to collectors that are on the way
		# this ensures that the resources, that it will get, won't be taken
		# by anything else but this collector
		self.__registered_collectors = []

		game.main.session.scheduler.add_new_object(self.tick, self, self.__class__.check_production_interval, -1)

	def tick(self):
		"""Called by the ticker, to produce goods.
		"""
		# check if production is disabled
		if self.active_production_line == -1:
			return

		# check if building is in storage mode or is a storage
		if self.production[self.active_production_line]['time'] == 0:
			return

		self._current_production += self.__class__.check_production_interval
		if self.active_production_line != -1 and (self._current_production % (self.production[self.active_production_line]['time']) == 0):
			# time to produce res
			for res in self.production[self.active_production_line]['res'].items():
				# check for needed resources
				if res[1] < 0:
					if self.inventory.get_value(res[0]) + res[1] < 0:
						# missing res res[0]
						#print 'PROD', self.id,'missing', res[0]
						return

				# check for storage capacity
				else:
					if self.inventory.get_value(res[0]) == self.inventory.get_size(res[0]):
						# no space for res[0]
						#print 'PROD', self.id,'no space for', res[0]
						return

			# everything ok, acctual production:
			for res in self.production[self.active_production_line]['res'].items():
				self.inventory.alter_inventory(res[0], res[1])
				#debug:
				#print "PROD", self.id, 'res', res[0], 'amount', res[1]

			self.next_animation()

	def pickup_resources(self, res, max_amount):
		"""Return the resources of id res that are in stock and removes them from the stock.
		@param res: int ressouce id.
		@param max_amount: int maximum resources that are picked up
		@return: int number of resources."""
		picked_up = self.inventory.get_value(res)
		if picked_up > max_amount:
			picked_up = max_amount
		self.inventory.alter_inventory(res, -picked_up)
		self.restart_animation()
		return picked_up

	def restart_animation(self):
		"""This is overwritten by buildings, that have an animation
		"""
		pass

	def next_animation(self):
		""" see above
		"""
		pass

	def get_growing_info(self):
		"""
		@return (all values are average) tuple: (cur_production, cur_production_res_amount, cur_production_res_size, cur_production_time) OR -1 if no cur production
		"""
		if self.active_production_line == -1:
			return -1
		data = (\
			[ self.production[self.active_production_line]['res'][res] for res in self.production[self.active_production_line]['res'] if self.production[self.active_production_line]['res'][res] > 0 ], \
			[ self.inventory.get_value(res) for res in self.production[self.active_production_line]['res'] if self.production[self.active_production_line]['res'][res] > 0 ], \
			[ self.inventory.get_size(res) for res in self.production[self.active_production_line]['res'] if self.production[self.active_production_line]['res'][res] > 0 ],\
			self.production[self.active_production_line]['time'] )

		return (sum(data[0])/len(data[0]), sum(data[1])/len(data[1]), sum(data[2])/len(data[2]), data[3])
