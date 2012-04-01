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

from horizons.command import GenericCommand, GenericComponentCommand

class ToggleActive(GenericComponentCommand):
	"""Sets a production to active/inactive."""
	def __init__(self, producer, production=None):
		super(ToggleActive, self).__init__(producer, "toggle_active")
		self._production = None if production is None else production.prod_id

	def __call__(self, issuer):
		# NOTE: special call method, cause production must be saved as id, not as Production obj
		obj = self._get_object().get_component_by_name(self.component_name)
		return getattr(obj, self.method)( None if self._production is None else obj._get_production(self._production))

GenericComponentCommand.allow_network(ToggleActive)


class AddProduction(GenericComponentCommand):
	"""Add a production to a producer"""
	def __init__(self, producer, production_line_id):
		super(AddProduction, self).__init__(producer, "add_production_by_id", production_line_id)

GenericComponentCommand.allow_network(AddProduction)


class RemoveFromQueue(GenericComponentCommand):
	"""Remove a production line id from a queueproducer's queue"""
	def __init__(self, producer, production_line_id):
		super(RemoveFromQueue, self).__init__(producer, "remove_from_queue", production_line_id)

GenericComponentCommand.allow_network(RemoveFromQueue)


class CancelCurrentProduction(GenericComponentCommand):
	"""Cancel the current production of a queueproducer.
	Makes it proceed to the next one."""
	def __init__(self, producer):
		super(CancelCurrentProduction, self).__init__(producer, "cancel_current_production")

GenericCommand.allow_network(CancelCurrentProduction)
