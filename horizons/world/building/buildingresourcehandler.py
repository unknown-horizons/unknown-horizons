# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.world.resourcehandler import ResourceHandler

class BuildingResourceHandler(ResourceHandler):
	"""A Resourcehandler that is also a building.
	This class exists because we keep a list of all buildings, that provide something at the island.
	"""
	def __init__(self, island, **kwargs):
		super(BuildingResourceHandler, self).__init__(island=island, **kwargs)
		self.__init(island)

	def __init(self, island):
		"""
		@param island: the island where the building is located
		"""
		island.provider_buildings.append(self)

	def load(self, db, worldid):
		super(BuildingResourceHandler, self).load(db, worldid)
		# workaround, fetch island from db cause self.island might not be initialised
		location = self.load_location(db, worldid)
		island = location[0]
		self.__init(island)

	def remove(self):
		super(BuildingResourceHandler, self).remove()
		self.island.provider_buildings.remove(self)

	def set_active(self, production=None, active=True):
		super(BuildingResourceHandler, self).set_active(production, active)
		# set running costs, if activity status has changed.
		if self.running_costs_active():
			if not self.is_active():
				self.toggle_costs()
		else:
			if self.is_active():
				self.toggle_costs()
		self._changed()
