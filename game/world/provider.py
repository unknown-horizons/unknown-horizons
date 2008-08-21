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

from game.world.storageholder import StorageHolder
from game.util import WeakList

class Provider(StorageHolder):
	def __init__(self, **kwargs):
		super(Provider, self).__init__(**kwargs)

		# save references to collectors that are on the way
		# this ensures that the resources, that it will get, won't be taken
		# by anything else but this collector
		self.__collectors = WeakList()

	def pickup_resources(self, res, max_amount):
		"""Return the resources of id res that are in stock and removes them from the stock.
		@param res: int ressouce id.
		@param max_amount: int maximum resources that are picked up
		@return: int number of resources."""
		picked_up = self.inventory.get_value(res)
		if picked_up > max_amount:
			picked_up = max_amount
		self.inventory.alter_inventory(res, -picked_up)
		return picked_up
