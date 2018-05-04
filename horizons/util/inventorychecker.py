# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.

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

from copy import deepcopy

from horizons.scheduler import Scheduler


class InventoryChecker:

	def __init__(self, message_class, storage_component, check_interval):
		"""Message class is a subclass of message that this checker will broadcast when the storage_component given has change in its inventory.
		This check is done every check_interval ticks."""
		self.__message_class = message_class
		self.__storage_component = storage_component
		self.__inventory_copy = deepcopy(storage_component.inventory._storage)

		self.__check_interval = check_interval

		# Check for updates every few ticks
		Scheduler().add_new_object(self.check_inventory_changed, self, loops=-1, loop_interval=self.__check_interval)

	def check_inventory_changed(self):
		"""Function that checks whether the settlements inventory has changed from the last time checked"""
		inventory = self.__storage_component.inventory._storage
		if inventory != self.__inventory_copy:
			self.__message_class.broadcast(self)
			self.__inventory_copy = deepcopy(inventory)

	def remove(self):
		"""Clean up"""
		Scheduler().rem_all_classinst_calls(self)
		self.__inventory_copy = None
		self.__storage_component = None
		self.__message_class = None
