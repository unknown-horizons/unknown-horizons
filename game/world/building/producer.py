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
from game.world.storage import Storage
import game.main

class Producer(Storage):
	"""Class used for production buildings
	
	Has to be inherited by a building
	This includes e.g. trees, lumberjack, weaver, storages
	"""
	def __init__(self):
		"""
		"""
		super(Producer, self).__init__()
		
		# produced resources: (production is enabled by default)
		self.prod_res = {}
		productions = game.main.db("SELECT resource, time, storage_size FROM production WHERE building = ?", self.id)
		for (res, time, size) in productions:
			self.prod_res[res] = (time, True)
			self.addSlot(res, size)
			
		# production ratios:
		self.prod_ratios = {}
		for res in self.prod_ratios.keys():
			prod_ratios = game.main.db("SELECT (SELECT resource FROM consumation where consumation.rowid = production_ratio.consumation) as raw_material, ratio FROM production_ratio WHERE production_ratio.production = (SELECT rowid FROM production WHERE building = ? AND resource = ?", self.id , res)
			for (raw_material, ratio) in prod_ratios:
				self.prod_ratio[res] = (raw_material, ratio)
				
		# save references to carriages that are on the way
		# this ensures that the resources, that it will get, won't be taken
		# by anything else but this carriages
		self.pickup_carriages = []

	def start(self):
		"""Starts the object. Overrides the standart Building.start() methode.
		"""
		# run self.tick every tick (NOTE: this should be discussed)
		game.main.session.scheduler.add_new_object(self.tick, self, 1, -1)
		
	def stop_production(self, res_id, stop = True):
		""" Stops or starts the production
		
		Use 'stop_production(res_id, False)' for starting
		"""
		self.prod_res[res_id] = not stop

	def tick(self):
		"""Called by the ticker, to produce goods.
		"""
		
		self.current_production += 1
		for res in self.prod_res.keys():
			if self.prod_res[res][1] and self.current_production % self.prod_res[res][0] == 0:
				# time to produce res
				
				# check for needed resources
				for raw_material, ratio in self.prod_ratios[res]:
					if self.get_value(raw_material) < 1/ratio:
						# missing raw_material
						break
				else:
					continue
				
				# check for storage capacity
				if self.get_value(res) == self.get_size(res):
					continue
				
				# produce 1 res and remove raw_material
				self.alter_inventory(res, 1)
				for raw_material, ratio in self.prod_ratios[res]:
					self.alter_inventory(raw_material, -(1/ratio))
					
	def pickup_resources(self, res):
		"""Return the ressources of id res that are in stock and removes them from the stock.
		@param res: int ressouce id.
		@return: int number of ressources."""
		pickup_amount = self.stock.get_value(res)
		self.stock.alter_inventory(res, -pickup_amount)
		return pickup_amount