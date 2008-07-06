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
import game.main

class Producer(object):
	"""Class used for production buildings
	
	Has to be inherited by a building
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
		
		result = game.main.db("SELECT rowid, time FROM production_line where building = ?", self.id);
		for (prod_line, time) in result:
			self.production[prod_line] = {}
			self.production[prod_line]['res'] = {}
			self.production[prod_line]['time'] = time
			
			prod_infos = game.main.db("SELECT \
			(SELECT storage.resource FROM storage WHERE storage.rowid = production.resource) as resource, \
			(SELECT storage.storage_size FROM storage WHERE storage.rowid = production.resource) as storage_size, \
			amount \
			FROM production WHERE production_line = ?", prod_line)
			for (resource, storage_size, amount) in prod_infos:
				if amount > 0: # acctually produced res
					self.prod_res.append(resource)
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
				
		# save references to carriages that are on the way
		# this ensures that the resources, that it will get, won't be taken
		# by anything else but this carriages
		self.pickup_carriages = []

		# run self.tick every second tick (NOTE: this should be discussed)
		game.main.session.scheduler.add_new_object(self.tick, self, 2, -1)
		
	def tick(self):
		"""Called by the ticker, to produce goods.
		"""
		# check if production is disabled
		if self.active_production_line == -1:
			return
		
		# check if building is in storage mode or is a storage
		if self.production[self.active_production_line]['time'] == 0:
			return
		
		self._current_production += 1
		if self.active_production_line != -1 and (self._current_production % (self.production[self.active_production_line]['time']) == 0):
			# time to produce res
			for res in self.production[self.active_production_line]['res'].items():
				# check for needed resources
				if res[1] < 0:
					if self.inventory.get_value(res[0]) + res[1] < 0:
						# missing res res[0]
						return
				
				# check for storage capacity
				else:
					if self.inventory.get_value(res[0]) == self.inventory.get_size(res[0]):
						# no space for res[0]
						return
				
			# everything ok, acctual production:
			for res in self.production[self.active_production_line]['res'].items():
				self.inventory.alter_inventory(res[0], res[1])
				
				#debug:
				if res[1] >0: print "PRODUCING", res[0], "IN", self.id
				
				
	def pickup_resources(self, res, max_amount):
		"""Return the ressources of id res that are in stock and removes them from the stock.
		@param res: int ressouce id.
		@param max_amount: int maximum resources that are picked up
		@return: int number of ressources."""
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