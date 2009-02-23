# ###################################################
# Copyright (C) 2008 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
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

from game.world.storageholder import StorageHolder
from game.util import WeakList

class Provider(StorageHolder):
	"""The Provider class provides an interface for Collectors to pickup goods from a class that is
	derived from this Class. A Branchoffice is a provider for example, every producer is a provider
	, too.
	There are 3 basic classes that are used for almost every building in a way or another:
	- Provider (this class)
	- Consumer (we will be looking at that next)
	- Producer (we'll get to that later)
	By combining these three classes, you are able to 'produce' pretty much everything you will ever
	need.

	TUTORIAL:
	Check out the Consumer class now in game/world/consumer.py
	"""
	def __init__(self, **kwargs):
		super(Provider, self).__init__(**kwargs)
		self.__init()

	def __init(self):
		# save references to collectors that are on the way
		# this ensures that the resources, that it will get, won't be taken
		# by anything else but this collector
		self.__collectors = WeakList()

	def __del__(self):
		for col in self.__collectors:
			col.cancel()
		self.__collectors = None
		super(StorageHolder, self).__del__()


	def load(self, db, worldid):
		super(Provider, self).load(db, worldid)
		self.__init()

	def pickup_resources(self, res, max_amount):
		"""Return the resources of id res that are in stock and removes them from the stock.
		@param res: int ressouce id.
		@param max_amount: int maximum resources that are picked up
		@return: int number of resources."""
		picked_up = self.inventory[res]
		if picked_up > max_amount:
			picked_up = max_amount
		self.inventory.alter(res, -picked_up)
		return picked_up
