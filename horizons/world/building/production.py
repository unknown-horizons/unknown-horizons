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


from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.world.building.building import BasicBuilding
from horizons.world.building.buildable import BuildableSingle, BuildableSingleOnCoast, BuildableSingleOnDeposit, BuildableSingleOnOcean
from horizons.world.building.nature import Field
from horizons.util import Rect
from horizons.util.shapes.radiusshape import RadiusRect
from horizons.command.building import Build
from horizons.scheduler import Scheduler
from horizons.constants import BUILDINGS, PRODUCTION
from horizons.world.production.producer import Producer
from horizons.component.storagecomponent import StorageComponent

class ProductionBuilding(BuildingResourceHandler, BuildableSingle, BasicBuilding):
	pass

class Farm(ProductionBuilding):

	def _get_providers(self):
		reach = RadiusRect(self.position, self.radius)
		providers = self.island.get_providers_in_range(reach, reslist=self.get_needed_resources())
		return [provider for provider in providers if isinstance(provider, Field)]


class CoastalProducer(BuildingResourceHandler, BuildableSingleOnOcean, BasicBuilding):
	"""E.g. salt ponds"""
	pass

class Fisher(BuildingResourceHandler, BuildableSingleOnCoast, BasicBuilding):

	"""
	Old selection workaround (only color fish) removed in b69c72aeef0174c42dec4039eed7b81f96f6dcaa.
	"""

	def get_non_paused_utilisation(self):
		total = 0
		productions = self.get_component(Producer).get_productions()
		for production in productions:
			if production.get_age() < PRODUCTION.STATISTICAL_WINDOW * 1.5:
				return 1
			state_history = production.get_state_history_times(True)
			total += state_history[PRODUCTION.STATES.producing.index]
		return total / float(len(productions))

class Mine(BuildingResourceHandler, BuildableSingleOnDeposit, BasicBuilding):
	def __init__(self, inventory, deposit_class, *args, **kwargs):
		"""
		@param inventory: inventory dump of deposit (collected by get_prebuild_data())
		@param deposit_class: class num of deposit for later reconstruction (collected by get_prebuild_data())
		"""
		# needs to be inited before super(), since that will call the _on_production_changed hook
		super(Mine, self).__init__(*args, **kwargs)
		self.__inventory = inventory
		self.__deposit_class = deposit_class

	def initialize(self, deposit_class, inventory, **kwargs):
		super(Mine, self).initialize( ** kwargs)
		self.__init(deposit_class=deposit_class)
		for res, amount in inventory.iteritems():
			# bury resources from mountain in mine
			self.get_component(StorageComponent).inventory.alter(res, amount)

	@classmethod
	def get_loading_area(cls, building_id, rotation, pos):
		if building_id == BUILDINGS.MOUNTAIN or building_id == BUILDINGS.IRON_MINE:
			if rotation == 45:
				return Rect.init_from_topleft_and_size(pos.origin.x, pos.origin.y + 1, 1, 3)
			elif rotation == 135:
				return Rect.init_from_topleft_and_size(pos.origin.x + 1, pos.origin.y + pos.height - 1, 3, 1)
			elif rotation == 225:
				return Rect.init_from_topleft_and_size(pos.origin.x + pos.width -1, pos.origin.y + 1, 1, 3)
			elif rotation == 315:
				return Rect.init_from_topleft_and_size(pos.origin.x + 1, pos.origin.y, 3, 1)
			assert False
		else:
			return pos

	def __init(self, deposit_class):
		self.__deposit_class = deposit_class

		# setup loading area
		# TODO: for now we assume that a mine building is 5x5 with a 3x1 entry on 1 side
		#       this needs to be generalised, possibly by defining the loading tiles in the db
		self.loading_area = self.get_loading_area(deposit_class, self.rotation, self.position)

	@classmethod
	def get_prebuild_data(cls, session, position):
		"""Returns dict containing inventory of deposit, which is needed for the mine build"""
		deposit = session.world.get_building(position.center())
		data = {}
		data["inventory"] = deposit.get_component(StorageComponent).inventory.get_dump()
		data["deposit_class"] = deposit.id
		return data

	def remove(self):
		# build the deposit back here after remove() is finished
		deposit_build_data = { 'inventory' : self.get_component(StorageComponent).inventory.get_dump() }
		build_cmd = Build(self.__deposit_class, self.position.origin.x, self.position.origin.y, \
		                  self.island, ownerless=True, data = deposit_build_data)
		Scheduler().add_new_object(build_cmd, build_cmd, run_in=0)

		super(Mine, self).remove()

	def save(self, db):
		super(Mine, self).save(db)
		db("INSERT INTO mine(rowid, deposit_class) VALUES(?, ?)", \
		   self.worldid, self.__deposit_class)

	def load(self, db, worldid):
		super(Mine, self).load(db, worldid)
		deposit_class = db("SELECT deposit_class FROM mine WHERE rowid = ?", worldid)[0][0]
		self.__init(deposit_class)

