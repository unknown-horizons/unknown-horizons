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

class Production(Building):
	"""Class used for production buildings
	@param x,y: int coordinates of the building.
	@param owner: Player instance that owns the building.
	@param instance: fife.Instance that is used in case a preview instance has already been created."""
	def __init__(self, x, y, owner, instance = None):
		self.x = x
		self.y = y
		self.owner = owner
		if instance == None:
			self.createInstance(x, y)
		else:
			self._instance = instance
			game.main.session.entities.updateInstance(self._instance.getId(), self)
		self.health = 100
		self.stock = Storage(1, 4)
		self.current_production = 0
		self.pickup_check = True


	def start(self):
		"""Starts the object. Overrides the standart Building.start() methode.
		"""
		game.main.session.scheduler.add_new_object(self.tick, self, (6/int(self.production_rate))*game.main.session.timer.ticks_per_second)

	def tick(self):
		"""Called by the ticker, to produce goods.
		"""
		self.current_production += 1
		if self.current_production == 10:
			self.current_production = 0
			if self.stock.get_value(int(self.production_res)) < 4:
				self.stock.alter_inventory(int(self.production_res), 1)
			if self.stock.get_value(int(self.production_res)) <= 3:
				self._instance.say('Stock: '+ str(self.stock.get_value(int(self.production_res))), 2000)
			elif self.stock.get_value(int(self.production_res)) == 4:
				self._instance.say('Full', 2000)
			if self.stock.get_value(int(self.production_res)) == 2 or not self.pickup_check:
				self.call_pickup()
		game.main.session.scheduler.add_new_object(self.tick, self, (6/int(self.production_rate))*game.main.session.timer.ticks_per_second)

	def call_pickup(self):
		"""Calls for ressource pickup at the nearest storage facility."""
		pickup = self.settlement.get_nearest_pickup(self.x, self.y)
		if pickup is None:
			self._instance.say('NO PICKUP AVAILABLE!', 3000)
			self.pickup_check = False
		else:
			pickup.add_to_queue(self, int(self.production_res))
			self.pickup_check = True

	def get_ressources(self, res):
		"""Return the ressources of id res that are in stock and removes them from the stock.
		@param res: int ressouce id.
		@return: int number of ressources."""
		ret = self.stock.get_value(res)
		self.stock.alter_inventory(res, -ret)
		return ret
