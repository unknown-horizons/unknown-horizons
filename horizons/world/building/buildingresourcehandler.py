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

from horizons.messaging import ResourceProduced
from horizons.world.resourcehandler import ResourceHandler
from horizons.world.production.producer import Producer

class BuildingResourceHandler(ResourceHandler):
	"""A Resourcehandler that is also a building.
	This class exists because we keep a list of all buildings, that provide something at the island.
	"""
	def __init__(self, island, **kwargs):
		super(BuildingResourceHandler, self).__init__(island=island, **kwargs)
		self.island = island

	def initialize(self):
		super(BuildingResourceHandler, self).initialize()
		self.__init()

	def __init(self):
		self.island.provider_buildings.append(self)
		if self.has_component(Producer):
			self.get_component(Producer).add_activity_changed_listener(self._set_running_costs_to_status)
			self.get_component(Producer).add_production_finished_listener(self.on_production_finished)
			self._set_running_costs_to_status(None, self.get_component(Producer).is_active())

	def load(self, db, worldid):
		super(BuildingResourceHandler, self).load(db, worldid)
		self.__init()

	def remove(self):
		super(BuildingResourceHandler, self).remove()
		self.island.provider_buildings.remove(self)
		if self.has_component(Producer):
			self.get_component(Producer).remove_activity_changed_listener(self._set_running_costs_to_status)
			self.get_component(Producer).remove_production_finished_listener(self.on_production_finished)

	def on_production_finished(self, caller, resources):
		if self.is_valid_tradable_resource(resources):
			ResourceProduced.broadcast(self, resources)

	def is_valid_tradable_resource(self, resources):
		""" Checks if the produced resource tradable (can be carried by collectors).
		"""
		if not resources or not resources.keys():
			return False

		return resources.keys()[0] in \
		       self.island.session.db.get_res(only_tradeable=True, only_inventory=True)

	def _set_running_costs_to_status(self, caller, is_active):
		current_setting_is_active = self.running_costs_active()
		if current_setting_is_active and not is_active:
			self.toggle_costs()
			self._changed()
		elif not current_setting_is_active and is_active:
			self.toggle_costs()
			self._changed()


class UnitProducerBuilding(BuildingResourceHandler):
	"""Class for building that produce units.
	Uses a BuildingResourceHandler additionally to ResourceHandler to enable
	building specific behaviour."""
	pass

