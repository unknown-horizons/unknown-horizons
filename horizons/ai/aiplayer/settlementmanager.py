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

import logging

from horizons.ai.aiplayer.villagebuilder import VillageBuilder
from horizons.ai.aiplayer.productionbuilder import ProductionBuilder
from horizons.ai.aiplayer.productionchain import ProductionChain
from horizons.ai.aiplayer.resourcemanager import ResourceManager
from horizons.ai.aiplayer.trademanager import TradeManager

from horizons.ai.aiplayer.goal.boatbuilder import BoatBuilderGoal
from horizons.ai.aiplayer.goal.depositcoverage import ClayDepositCoverageGoal, MountainCoverageGoal
from horizons.ai.aiplayer.goal.enlargecollectorarea import EnlargeCollectorAreaGoal
from horizons.ai.aiplayer.goal.feederchaingoal import FeederFoodGoal, FeederTextileGoal, FeederLiquorGoal, \
	FeederTobaccoProductsGoal, FeederSaltGoal
from horizons.ai.aiplayer.goal.firestation import FireStationGoal
from horizons.ai.aiplayer.goal.foundfeederisland import FoundFeederIslandGoal
from horizons.ai.aiplayer.goal.improvecollectorcoverage import ImproveCollectorCoverageGoal
from horizons.ai.aiplayer.goal.productionchaingoal import FaithGoal, TextileGoal, BricksGoal, \
	EducationGoal, GetTogetherGoal, ToolsGoal, BoardsGoal, FoodGoal, CommunityGoal, TobaccoProductsGoal, \
	SaltGoal
from horizons.ai.aiplayer.goal.signalfire import SignalFireGoal
from horizons.ai.aiplayer.goal.storagespace import StorageSpaceGoal
from horizons.ai.aiplayer.goal.tent import TentGoal
from horizons.ai.aiplayer.goal.tradingship import TradingShipGoal

from horizons.scheduler import Scheduler
from horizons.util import WorldObject
from horizons.util.python import decorators
from horizons.command.uioptions import SetTaxSetting, SetSettlementUpgradePermissions
from horizons.command.production import ToggleActive
from horizons.constants import BUILDINGS, RES, GAME_SPEED, SETTLER
from horizons.entities import Entities
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.component.namedcomponent import NamedComponent
from horizons.world.production.producer import Producer

class SettlementManager(WorldObject):
	"""
	This is the main settlement control class.

	Important attributes:
	* feeder_island: boolean showing whether the island is a feeder island (feeder islands have no village area)
	* island: Island instance
	* settlement: Settlement instance
	* land_manager: LandManager instance
	* production_chain: dictionary where the key is a resource id and the value is the ProductionChain instance
	* production_builder: ProductionBuilder instance
	* village_builder: VillageBuilder instance
	* resource_manager: ResourceManager instance
	* trade_manager: TradeManager instance
	"""

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, owner, land_manager):
		super(SettlementManager, self).__init__()
		self.owner = owner
		self.resource_manager = ResourceManager(self)
		self.trade_manager = TradeManager(self)
		self.__init(land_manager)

		self.village_builder = VillageBuilder(self)
		self.production_builder = ProductionBuilder(self)
		self.village_builder.display()
		self.production_builder.display()

		self.__init_goals()

		if not self.feeder_island:
			self._set_taxes_and_permissions(self.personality.initial_sailor_taxes, self.personality.initial_pioneer_taxes, \
				self.personality.initial_settler_taxes, self.personality.initial_sailor_upgrades, self.personality.initial_pioneer_upgrades)

	def __init(self, land_manager):
		self.owner = land_manager.owner
		self.session = self.owner.session
		self.land_manager = land_manager
		self.island = self.land_manager.island
		self.settlement = self.land_manager.settlement
		self.feeder_island = land_manager.feeder_island
		self.personality = self.owner.personality_manager.get('SettlementManager')

		# create a production chain for every building material, settler consumed resource, and resources that have to be imported from feeder islands
		self.production_chain = {}
		for resource_id in [RES.COMMUNITY_ID, RES.BOARDS_ID, RES.FOOD_ID, RES.TEXTILE_ID, RES.FAITH_ID, \
						RES.EDUCATION_ID, RES.GET_TOGETHER_ID, RES.BRICKS_ID, RES.TOOLS_ID, RES.LIQUOR_ID, \
						RES.TOBACCO_PRODUCTS_ID, RES.SALT_ID]:
			self.production_chain[resource_id] = ProductionChain.create(self, resource_id)

		# initialise caches
		self.__resident_resource_usage_cache = {}

	def __init_goals(self):
		"""Initialise the list of all the goals the settlement can use."""
		self._goals = [] # [SettlementGoal, ...]
		self._goals.append(BoardsGoal(self))
		self._goals.append(SignalFireGoal(self))
		self._goals.append(EnlargeCollectorAreaGoal(self))
		self._goals.append(ImproveCollectorCoverageGoal(self))
		self._goals.append(BricksGoal(self))
		if self.feeder_island:
			self._goals.append(StorageSpaceGoal(self))
			self._goals.append(FeederFoodGoal(self))
			self._goals.append(FeederTextileGoal(self))
			self._goals.append(FeederLiquorGoal(self))
			self._goals.append(FeederSaltGoal(self))
			self._goals.append(FeederTobaccoProductsGoal(self))
		else:
			self._goals.append(BoatBuilderGoal(self))
			self._goals.append(ClayDepositCoverageGoal(self))
			self._goals.append(FoundFeederIslandGoal(self))
			self._goals.append(MountainCoverageGoal(self))
			self._goals.append(FoodGoal(self))
			self._goals.append(CommunityGoal(self))
			self._goals.append(FaithGoal(self))
			self._goals.append(TextileGoal(self))
			self._goals.append(EducationGoal(self))
			self._goals.append(GetTogetherGoal(self))
			self._goals.append(SaltGoal(self))
			self._goals.append(TobaccoProductsGoal(self))
			self._goals.append(ToolsGoal(self))
			self._goals.append(TentGoal(self))
			self._goals.append(TradingShipGoal(self))
			self._goals.append(FireStationGoal(self))

	def save(self, db):
		super(SettlementManager, self).save(db)
		db("INSERT INTO ai_settlement_manager(rowid, land_manager) VALUES(?, ?)", \
			self.worldid, self.land_manager.worldid)

		self.village_builder.save(db)
		self.production_builder.save(db)
		self.resource_manager.save(db)
		self.trade_manager.save(db)

	@classmethod
	def load(cls, db, owner, worldid):
		self = cls.__new__(cls)
		self._load(db, owner, worldid)
		return self

	def _load(self, db, owner, worldid):
		self.owner = owner
		super(SettlementManager, self).load(db, worldid)

		# load the main part
		land_manager_id = db("SELECT land_manager FROM ai_settlement_manager WHERE rowid = ?", worldid)[0][0]
		land_manager = WorldObject.get_object_by_id(land_manager_id)

		# find the settlement
		for settlement in self.owner.session.world.settlements:
			if settlement.owner == self.owner and settlement.island == land_manager.island:
				land_manager.settlement = settlement
				break
		assert land_manager.settlement
		self.resource_manager = ResourceManager.load(db, self)
		self.trade_manager = TradeManager.load(db, self)
		self.__init(land_manager)

		# load the master builders
		self.village_builder = VillageBuilder.load(db, self)
		self.production_builder = ProductionBuilder.load(db, self)
		self.village_builder.display()
		self.production_builder.display()

		self.__init_goals()

		# the add_building events happen before the settlement manager is loaded so they have to be repeated here
		for building in self.settlement.buildings:
			self.add_building(building)

	def _set_taxes_and_permissions(self, sailors_taxes, pioneers_taxes, settlers_taxes, sailors_can_upgrade, pioneers_can_upgrade):
		"""Set new tax settings and building permissions."""
		if abs(self.settlement.tax_settings[SETTLER.SAILOR_LEVEL] - sailors_taxes) > 1e-9:
			self.log.info('%s set sailors\' taxes from %.1f to %.1f', self, self.settlement.tax_settings[SETTLER.SAILOR_LEVEL], sailors_taxes)
			SetTaxSetting(self.settlement, SETTLER.SAILOR_LEVEL, sailors_taxes).execute(self.land_manager.session)
		if abs(self.settlement.tax_settings[SETTLER.PIONEER_LEVEL] - pioneers_taxes) > 1e-9:
			self.log.info('%s set pioneers\' taxes from %.1f to %.1f', self, self.settlement.tax_settings[SETTLER.PIONEER_LEVEL], pioneers_taxes)
			SetTaxSetting(self.settlement, SETTLER.PIONEER_LEVEL, pioneers_taxes).execute(self.land_manager.session)
		if abs(self.settlement.tax_settings[SETTLER.SETTLER_LEVEL] - settlers_taxes) > 1e-9:
			self.log.info('%s set settlers\' taxes from %.1f to %.1f', self, self.settlement.tax_settings[SETTLER.SETTLER_LEVEL], settlers_taxes)
			SetTaxSetting(self.settlement, SETTLER.SETTLER_LEVEL, settlers_taxes).execute(self.land_manager.session)
		if self.settlement.upgrade_permissions[SETTLER.SAILOR_LEVEL] != sailors_can_upgrade:
			self.log.info('%s set sailor upgrade permissions to %s', self, sailors_can_upgrade)
			SetSettlementUpgradePermissions(self.settlement, SETTLER.SAILOR_LEVEL, sailors_can_upgrade).execute(self.land_manager.session)
		if self.settlement.upgrade_permissions[SETTLER.PIONEER_LEVEL] != pioneers_can_upgrade:
			self.log.info('%s set pioneer upgrade permissions to %s', self, pioneers_can_upgrade)
			SetSettlementUpgradePermissions(self.settlement, SETTLER.PIONEER_LEVEL, pioneers_can_upgrade).execute(self.land_manager.session)

	def can_provide_resources(self):
		"""Return a boolean showing whether this settlement is complete enough to concentrate on building a new settlement."""
		if self.village_builder.tent_queue:
			return False
		settler_houses = 0
		residences = self.settlement.buildings_by_id.get(BUILDINGS.RESIDENTIAL_CLASS, [])
		for building in residences:
			if building.level == SETTLER.SETTLER_LEVEL:
				settler_houses += 1
		if settler_houses > len(residences) * self.personality.new_settlement_settler_ratio:
			return True
		return False

	def get_resource_production(self, resource_id):
		"""Return the current production capacity (including import) per tick of the given resource."""
		# as long as there are enough collectors it is correct to calculate it this way
		if resource_id == RES.LIQUOR_ID and not self.feeder_island:
			# normal settlements go straight for get-together so their separate liquor production is zero.
			# feeder islands have to produce liquor because get-together is not tradable
			return self.get_resource_production(RES.GET_TOGETHER_ID) * self.production_chain[RES.GET_TOGETHER_ID].get_ratio(RES.LIQUOR_ID)
		else:
			return self.production_chain[resource_id].get_final_production_level()

	def get_resource_production_requirement(self, resource_id):
		"""Return the amount of resource per tick the settlement needs."""
		if resource_id not in self.__resident_resource_usage_cache or self.__resident_resource_usage_cache[resource_id][0] != Scheduler().cur_tick:
			total = 0
			if resource_id == RES.BRICKS_ID:
				total = self.personality.dummy_bricks_requirement if self.owner.settler_level > 0 else 0 # dummy value to cause bricks production to be built
			elif resource_id == RES.BOARDS_ID:
				total = self.personality.dummy_boards_requirement # dummy value to cause boards production to be built
			elif resource_id == RES.TOOLS_ID:
				total = self.personality.dummy_tools_requirement if self.owner.settler_level > 1 else 0 # dummy value to cause tools production to be built
			elif resource_id == RES.LIQUOR_ID:
				total = self.production_chain[RES.GET_TOGETHER_ID].get_ratio(RES.LIQUOR_ID) * self.get_resource_production_requirement(RES.GET_TOGETHER_ID)
			else:
				for residence in self.settlement.buildings_by_id.get(BUILDINGS.RESIDENTIAL_CLASS, []):
					for production in residence.get_component(Producer).get_productions():
						production_line = production._prod_line
						if resource_id in production_line.consumed_res:
							# subtract because the amount will be negative
							total -= float(production_line.consumed_res[resource_id]) / production_line.time / GAME_SPEED.TICKS_PER_SECOND

			self.__resident_resource_usage_cache[resource_id] = (Scheduler().cur_tick, total)
		return self.__resident_resource_usage_cache[resource_id][1]

	def _manual_upgrade(self, level, limit):
		"""
		Manually allow settlers to upgrade. If more then the set limit are already upgrading then don't stop them.

		@param level: the initial settler level from which to upgrade
		@param limit: the maximum number of residences of the specified level upgrading at the same time
		@return: boolean showing whether we gave any new residences the right to upgrade
		"""

		num_upgrading = 0
		for building in self.settlement.buildings_by_id.get(BUILDINGS.RESIDENTIAL_CLASS, []):
			if building.level == level:
				upgrade_production = building._get_upgrade_production()
				if upgrade_production is not None and not upgrade_production.is_paused():
					num_upgrading += 1
					if num_upgrading >= limit:
						return False

		upgraded_any = False
		for building in self.settlement.buildings_by_id.get(BUILDINGS.RESIDENTIAL_CLASS, []):
			if building.level == level:
				upgrade_production = building._get_upgrade_production()
				if upgrade_production is not None and upgrade_production.is_paused():
					ToggleActive(building.get_component(Producer), upgrade_production).execute(self.land_manager.session)
					num_upgrading += 1
					upgraded_any = True
					if num_upgrading >= limit:
						return True
		return upgraded_any

	def get_ideal_production_level(self, resource_id):
		"""
		Return the amount of resource per tick the settlement should produce.

		This is the amount that should be produced to satisfy the people in this settlement,
		keep up the current export rate, and fix the player's global deficit. This means
		that different (feeder) islands will have different ideal production levels.
		"""

		total = 0.0
		for settlement_manager in self.owner.settlement_managers:
			usage = settlement_manager.get_resource_production_requirement(resource_id) * self.personality.production_level_multiplier
			production = settlement_manager.get_resource_production(resource_id)
			resource_import = settlement_manager.trade_manager.get_total_import(resource_id)
			resource_export = settlement_manager.resource_manager.get_total_export(resource_id)
			total += usage
			if settlement_manager is not self:
				total -= production + resource_export - resource_import
		return max(0.0, total)

	def _start_feeder_tick(self):
		self.log.info('%s food requirement %.5f', self, self.get_ideal_production_level(RES.FOOD_ID))
		self.log.info('%s textile requirement %.5f', self, self.get_ideal_production_level(RES.TEXTILE_ID))
		self.log.info('%s liquor requirement %.5f', self, self.get_ideal_production_level(RES.LIQUOR_ID))
		self.log.info('%s salt requirement %.5f', self, self.get_ideal_production_level(RES.SALT_ID))
		self.log.info('%s tobacco products requirement %.5f', self, self.get_ideal_production_level(RES.TOBACCO_PRODUCTS_ID))
		self.production_builder.manage_production()
		self.resource_manager.refresh()

	def _end_feeder_tick(self):
		self.resource_manager.replay_deep_low_priority_requests()
		self.resource_manager.record_expected_exportable_production(self.owner.tick_interval)
		self.resource_manager.manager_buysell()
		self.resource_manager.finish_tick()

	def _start_general_tick(self):
		self.log.info('%s food production             %.5f / %.5f', self, self.get_resource_production(RES.FOOD_ID), \
			self.get_resource_production_requirement(RES.FOOD_ID))
		self.log.info('%s textile production          %.5f / %.5f', self, self.get_resource_production(RES.TEXTILE_ID), \
			self.get_resource_production_requirement(RES.TEXTILE_ID))
		self.log.info('%s get-together production     %.5f / %.5f', self, self.get_resource_production(RES.GET_TOGETHER_ID), \
			self.get_resource_production_requirement(RES.GET_TOGETHER_ID))
		self.log.info('%s salt production             %.5f / %.5f', self, self.get_resource_production(RES.SALT_ID), \
			self.get_resource_production_requirement(RES.SALT_ID))
		self.log.info('%s tobacco products production %.5f / %.5f', self, self.get_resource_production(RES.TOBACCO_PRODUCTS_ID), \
			self.get_resource_production_requirement(RES.TOBACCO_PRODUCTS_ID))
		self.production_builder.manage_production()
		self.trade_manager.refresh()
		self.resource_manager.refresh()
		self.need_materials = False

	def refresh_taxes_and_upgrade_permissions(self):
		# TODO: use a better system for managing settler upgrades and taxes
		if self.land_manager.owner.settler_level == 0:
			# if we are on level 0 and there is a house that can be upgraded then do it.
			if self._manual_upgrade(0, 1):
				self._set_taxes_and_permissions(self.personality.early_sailor_taxes, self.personality.early_pioneer_taxes, \
					self.personality.early_settler_taxes, self.personality.early_sailor_upgrades, self.personality.early_pioneer_upgrades)
		elif self.get_resource_production(RES.BRICKS_ID) > 1e-9 and not self.settlement.count_buildings(BUILDINGS.VILLAGE_SCHOOL_CLASS):
			# if we just need the school then upgrade sailors manually
			free_boards = self.settlement.get_component(StorageComponent).inventory[RES.BOARDS_ID]
			free_boards -= Entities.buildings[BUILDINGS.VILLAGE_SCHOOL_CLASS].costs[RES.BOARDS_ID]
			free_boards /= 2 # TODO: load this from upgrade resources
			if free_boards > 0:
				self._manual_upgrade(0, free_boards)
			self._set_taxes_and_permissions(self.personality.no_school_sailor_taxes, self.personality.no_school_pioneer_taxes, \
				self.personality.no_school_settler_taxes, self.personality.no_school_sailor_upgrades, self.personality.no_school_pioneer_upgrades)
		elif self.settlement.count_buildings(BUILDINGS.VILLAGE_SCHOOL_CLASS):
			if self.need_materials:
				self._set_taxes_and_permissions(self.personality.school_sailor_taxes, self.personality.school_pioneer_taxes, \
					self.personality.school_settler_taxes, self.personality.school_sailor_upgrades, self.personality.school_pioneer_upgrades)
			else:
				self._set_taxes_and_permissions(self.personality.final_sailor_taxes, self.personality.final_pioneer_taxes, \
					self.personality.final_settler_taxes, self.personality.final_sailor_upgrades, self.personality.final_pioneer_upgrades)

	def _end_general_tick(self):
		self.trade_manager.finalize_requests()
		self.trade_manager.organize_shipping()
		self.resource_manager.record_expected_exportable_production(self.owner.tick_interval)
		self.resource_manager.manager_buysell()
		self.resource_manager.finish_tick()

	def _add_goals(self, goals):
		"""Add the settlement's goals that can be activated to the goals list."""
		for goal in self._goals:
			if goal.can_be_activated:
				goal.update()
				goals.append(goal)

	def tick(self, goals):
		"""Refresh the settlement info and add its goals to the player's goal list."""
		if self.feeder_island:
			self._start_feeder_tick()
			self._add_goals(goals)
			self._end_feeder_tick()
		else:
			self._start_general_tick()
			self._add_goals(goals)
			self._end_general_tick()

	def add_building(self, building):
		"""Called when a new building is added to the settlement (the building already exists during the call)."""
		coords = building.position.origin.to_tuple()
		if coords in self.village_builder.plan:
			self.village_builder.add_building(building)
		else:
			self.production_builder.add_building(building)

	def remove_building(self, building):
		"""Called when a building is removed from the settlement (the building still exists during the call)."""
		coords = building.position.origin.to_tuple()
		if coords in self.village_builder.plan:
			self.village_builder.remove_building(building)
		else:
			self.production_builder.remove_building(building)

	def handle_lost_area(self, coords_list):
		"""
		Handle losing the potential land in the given coordinates list.

		Take the following actions:
		* remove the lost area from the village, production, and road areas
		* remove village sections with impossible main squares
		* remove all planned buildings that are now impossible from the village area
		* remove planned fields that are now impossible
		* remove fields that can no longer be serviced by a farm
		* TODO: if the village area takes too much of the total area then remove / reduce the remaining sections
		"""

		self.land_manager.handle_lost_area(coords_list)
		self.village_builder.handle_lost_area(coords_list)
		self.production_builder.handle_lost_area(coords_list)
		self.production_builder.handle_new_area() # some of the village area may have been repurposed as production area

		self.village_builder.display()
		self.production_builder.display()

	def __str__(self):
		return '%s.SM(%s/%s)' % (self.owner, self.settlement.get_component(NamedComponent).name if hasattr(self, 'settlement') else 'unknown', self.worldid if hasattr(self, 'worldid') else 'none')

decorators.bind_all(SettlementManager)
