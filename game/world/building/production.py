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

class Production(Building):
	"""Class used for production buildings"""
	def __init__(self, x, y, owner, instance = None):
		self.current_stock = 0
		self.current_production = 0
		self.x = x
		self.y = y
		self.owner = owner
		if instance == None:
			self.createInstance(x, y)
		else:
			self._instance = instance
			game.main.session.entities.updateInstance(self._instance.getId(), self)
		self.health = 100

	def start(self):
		game.main.session.scheduler.add_new_object(self.tick, self, int(self.production_rate))

	def tick(self):
		self.current_production += 1
		if self.current_production == 10:
			self._instance.say('+1', 2000)
			self.current_stock += 1
			self.current_production = 0
			if self.current_stock == 4:
				self._instance.say('Full', 2000)
				game.main.session.scheduler.add_new_object(lambda: self.get_ressouces(4), self, 64)
		if self.current_stock < 4:
			game.main.session.scheduler.add_new_object(self.tick, self, int(self.production_rate))

	def get_ressouces(self, num):
		self.settlement.inventory.alter_inventory(int(self.production_res), num)
		self.current_stock -= num
		game.main.session.scheduler.add_new_object(self.tick, self, int(self.production_rate))
