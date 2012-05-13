# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from horizons.component import Component
from horizons.component.storagecomponent import StorageComponent

class DepositComponent(Component):
	NAME = 'resource_deposit'
	DEPENDENCIES = ['StorageComponent']

	def __init__(self, resources):
		super(DepositComponent, self).__init__()
		self.resources = resources

	def initialize(self, inventory=None):
		if inventory:
			iterator = inventory.itercontents
		else:
			iterator = self.get_random_res_amounts
		for res, amount in iterator():
			self.instance.get_component(StorageComponent).inventory.alter(res, amount)

	def get_res_ranges(self):
		for res, data in self.resources.iteritems():
			yield (res, data['min_amount'], data['max_amount'])

	def get_random_res_amounts(self):
		for res, min_amount, max_amount in self.get_res_ranges():
			yield (res, self.session.random.randint(min_amount, max_amount))
