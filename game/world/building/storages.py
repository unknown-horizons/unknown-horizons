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

class Pickup(Building):
	"""Class used for storage buildings that pic up ressources for the settlement.
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
		self.queue = []
		self.pickups_active = 0
		self.pickups = 2

	def start(self):
		"""Starts the object. Overrides the standart Building.start() methode.
		"""
		self.tick()

	def tick(self):
		"""Method that is called by the scheduler to check for new pickups.
		"""
		if self.pickups_active < self.pickups and len(self.queue) > 0:
			info = self.queue.pop(0) # Needs to be set, otherwise the item will not pop until the lambda function is called.
			game.main.session.scheduler.add_new_object(lambda: self.pickup(info), self, int(game.main.session.timer.ticks_per_second*6))
			self.pickups_active += 1
		game.main.session.scheduler.add_new_object(self.tick, self, int(game.main.session.timer.ticks_per_second))

	def pickup(self, info):
		""" Gets ressources from the building specified in info and adds them to the settlements inventory.
		@param info: tuple (building, ressource_id)"""
		self.pickups_active -= 1
		load = info[0].get_ressources(info[1])
		self.settlement.inventory.alter_inventory(info[1], load)

	def add_to_queue(self, buiding, res_id):
		"""Adds a building to the picup queue.
		@param building: buildingclass instanz that calls for a pickup.
		@param res_id: ressource id that is to be picked up.
		"""
		self.queue.append((buiding, res_id))

class Storagetent(Pickup):
	pass
