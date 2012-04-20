# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

from horizons.command import Command
from horizons.component.storagecomponent import StorageComponent

"""
Commands for ingame upgrades of objects (usually buildings).
see:
http://wiki.unknown-horizons.org/index.php/Upgradeable_production_data
http://wiki.unknown-horizons.org/index.php/DD/Buildings/Building_upgrades
"""


class ObjectUpgrade(Command):
	def __init__(self):
		# TODO
		pass

	def __call__(self, issuer):
		# TODO
		pass

Command.allow_network(ObjectUpgrade)

def upgrade_production_time(obj, factor):
	"""
	"""
	assert isinstance(factor, float)
	obj.alter_production_time(factor)

def add_collector(obj, collector_class, number):
	"""
	"""
	for i in xrange(0, number):
		obj.add_collector(collector_class)

def change_runnning_costs(obj, costs_diff):
	"""

01:26 < totycro> how should the change be specified?
01:27 < totycro> as an integer, that is added/subtracted, according to is sign? ( costs := current_costs
                 + value )
01:27 < totycro> or as a float factor? ( costs := current_costs * factor )

	"""
	assert(hasattr(obj, 'running_costs'))
	obj.running_costs += costs_diff

def change_storage_space(obj, res, amount_diff):
	obj.get_component(StorageComponent).inventory.change_resource_slot_size(res, amount_diff)


# TODO:
# - building costs
# - production amount




