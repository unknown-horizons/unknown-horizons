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

import math
import logging

from collections import deque

from constants import BUILD_RESULT, BUILDING_PURPOSE
from villagebuilder import VillageBuilder
from productionbuilder import ProductionBuilder
from productionchain import ProductionChain
from resourcemanager import ResourceManager
from trademanager import TradeManager

from goal.boatbuilder import BoatBuilderGoal
from goal.claydepositcoverage import ClayDepositCoverageGoal
from goal.enlargecollectorarea import EnlargeCollectorAreaGoal
from goal.feederchaingoal import FeederFoodGoal, FeederTextileGoal, FeederLiquorGoal
from goal.foundfeederisland import FoundFeederIslandGoal
from goal.improvecollectorcoverage import ImproveCollectorCoverageGoal
from goal.mountaincoverage import MountainCoverageGoal
from goal.productionchaingoal import FaithGoal, TextileGoal, BricksGoal, EducationGoal, \
	GetTogetherGoal, ToolsGoal, BoardsGoal, FoodGoal, CommunityGoal
from goal.signalfire import SignalFireGoal
from goal.storagespace import StorageSpaceGoal
from goal.tent import TentGoal
from goal.tradingship import TradingShipGoal

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject
from horizons.util.python import decorators
from horizons.command.uioptions import SetTaxSetting, SetSettlementUpgradePermissions
from horizons.command.production import ToggleActive
from horizons.constants import BUILDINGS, RES, PRODUCTION, GAME_SPEED, SETTLER
from horizons.entities import Entities

class SettlementManager(WorldObject):
	"""
	An object of this class control one settlement of an AI player.
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

		if not self.feeder_island:
			self.set_taxes_and_permissions(self.personality.initial_sailor_taxes, self.personality.initial_pioneer_taxes, \
				self.personality.initial_settler_taxes, self.personality.initial_sailor_upgrades, self.personality.initial_pioneer_upgrades)

	def __init(self, land_manager):
		self.owner = land_manager.owner
		self.session = self.owner.session
		self.land_manager = land_manager
		self.island = self.land_manager.island
		self.settlement = self.land_manager.settlement
		self.feeder_island = land_manager.feeder_island
		self.personality = self.owner.personality_manager.get('SettlementManager')

		self.community_chain = ProductionChain.create(self, RES.COMMUNITY_ID)
		self.boards_chain = ProductionChain.create(self, RES.BOARDS_ID)
		self.food_chain = ProductionChain.create(self, RES.FOOD_ID)
		self.textile_chain = ProductionChain.create(self, RES.TEXTILE_ID)
		self.faith_chain = ProductionChain.create(self, RES.FAITH_ID)
		self.education_chain = ProductionChain.create(self, RES.EDUCATION_ID)
		self.get_together_chain = ProductionChain.create(self, RES.GET_TOGETHER_ID)
		self.bricks_chain = ProductionChain.create(self, RES.BRICKS_ID)
		self.tools_chain = ProductionChain.create(self, RES.TOOLS_ID)
		self.liquor_chain = ProductionChain.create(self, RES.LIQUOR_ID)

		self.goals = []
		self.goals.append(BoardsGoal(self))
		self.goals.append(SignalFireGoal(self))
		self.goals.append(EnlargeCollectorAreaGoal(self))
		self.goals.append(ImproveCollectorCoverageGoal(self))
		self.goals.append(BricksGoal(self))
		if self.feeder_island:
			self.goals.append(StorageSpaceGoal(self))
			self.goals.append(FeederFoodGoal(self))
			self.goals.append(FeederTextileGoal(self))
			self.goals.append(FeederLiquorGoal(self))
		else:
			self.goals.append(BoatBuilderGoal(self))
			self.goals.append(ClayDepositCoverageGoal(self))
			self.goals.append(FoundFeederIslandGoal(self))
			self.goals.append(MountainCoverageGoal(self))
			self.goals.append(FoodGoal(self))
			self.goals.append(CommunityGoal(self))
			self.goals.append(FaithGoal(self))
			self.goals.append(TextileGoal(self))
			self.goals.append(EducationGoal(self))
			self.goals.append(GetTogetherGoal(self))
			self.goals.append(ToolsGoal(self))
			self.goals.append(TentGoal(self))
			self.goals.append(TradingShipGoal(self))

		# initialise caches
		self.__resident_resource_usage_cache = {}

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

		# the add_building events happen before the settlement manager is loaded so they have to be repeated here
		for building in self.settlement.buildings:
			self.add_building(building)

	@property
	def tents(self):
		return self.count_buildings(BUILDINGS.RESIDENTIAL_CLASS)

	@property
	def branch_office(self):
		return self.settlement.branch_office

	def set_taxes_and_permissions(self, sailors_taxes, pioneers_taxes, settlers_taxes, sailors_can_upgrade, pioneers_can_upgrade):
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
		""" is this settlement allowed to provide the resources for a new settlement? """
		if self.village_builder.tent_queue:
			return False
		settler_houses = 0
		residences = self.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS)
		for building in residences:
			if building.level == SETTLER.SETTLER_LEVEL:
				settler_houses += 1
		if settler_houses > len(residences) * self.personality.new_settlement_settler_ratio:
			return True
		return False

	def get_resource_production(self, resource_id):
		# as long as there are enough collectors it is correct to calculate it this way
		if resource_id == RES.TEXTILE_ID:
			return self.textile_chain.get_final_production_level()
		elif resource_id == RES.GET_TOGETHER_ID:
			return self.get_together_chain.get_final_production_level()
		elif resource_id == RES.FOOD_ID:
			return self.food_chain.get_final_production_level()
		elif resource_id == RES.BRICKS_ID:
			return self.bricks_chain.get_final_production_level()
		elif resource_id == RES.BOARDS_ID:
			return self.boards_chain.get_final_production_level()
		elif resource_id == RES.LIQUOR_ID:
			if not self.feeder_island:
				return self.get_resource_production(RES.GET_TOGETHER_ID) * self.get_together_chain.get_ratio(RES.LIQUOR_ID)
			return self.liquor_chain.get_final_production_level()
		return None

	def get_resource_import(self, resource_id):
		return self.trade_manager.get_total_import(resource_id)

	def get_resource_export(self, resource_id):
		return self.resource_manager.get_total_export(resource_id)

	def get_resident_resource_usage(self, resource_id):
		if resource_id not in self.__resident_resource_usage_cache or self.__resident_resource_usage_cache[resource_id][0] != Scheduler().cur_tick:
			total = 0
			if resource_id == RES.BRICKS_ID:
				total = self.personality.dummy_bricks_requirement if self.owner.settler_level > 0 else 0 # dummy value to cause bricks production to be built
			elif resource_id == RES.BOARDS_ID:
				total = self.personality.dummy_boards_requirement # dummy value to cause boards production to be built
			elif resource_id == RES.TOOLS_ID:
				total = self.personality.dummy_tools_requirement if self.owner.settler_level > 1 else 0 # dummy value to cause tools production to be built
			elif resource_id == RES.LIQUOR_ID:
				total = self.get_together_chain.get_ratio(resource_id) * self.get_resident_resource_usage(RES.GET_TOGETHER_ID)
			else:
				for residence in self.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS):
					for production in residence._get_productions():
						production_line = production._prod_line
						if resource_id in production_line.consumed_res:
							# subtract because the amount will be negative
							total -= production_line.consumed_res[resource_id] / production_line.time / GAME_SPEED.TICKS_PER_SECOND

			self.__resident_resource_usage_cache[resource_id] = (Scheduler().cur_tick, total)
		return self.__resident_resource_usage_cache[resource_id][1]

	def log_generic_build_result(self, result, name):
		if result == BUILD_RESULT.OK:
			self.log.info('%s built a %s', self, name)
		elif result == BUILD_RESULT.NEED_RESOURCES:
			self.log.info('%s not enough materials to build a %s', self, name)
		elif result == BUILD_RESULT.SKIP:
			self.log.info('%s skipped building a %s', self, name)
		else:
			self.log.info('%s failed to build a %s (%d)', self, name, result)

	def count_buildings(self, building_id):
		return len(self.settlement.get_buildings_by_id(building_id))

	def manual_upgrade(self, level, limit):
		"""Enables upgrading residence buildings on the specified level until at least limit of them are upgrading."""
		num_upgrading = 0
		for building in self.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS):
			if building.level == level:
				upgrade_production = building._get_upgrade_production()
				if upgrade_production is not None and not upgrade_production.is_paused():
					num_upgrading += 1
					if num_upgrading >= limit:
						return False

		upgraded_any = False
		for building in self.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS):
			if building.level == level:
				upgrade_production = building._get_upgrade_production()
				if upgrade_production is not None and upgrade_production.is_paused():
					ToggleActive(building, upgrade_production).execute(self.land_manager.session)
					num_upgrading += 1
					upgraded_any = True
					if num_upgrading >= limit:
						return True
		return upgraded_any

	def reachable_deposit(self, building_id):
		""" returns true if there is a resource deposit outside the settlement that is not owned by another player """
		for building in self.land_manager.resource_deposits[building_id]:
			if building.settlement is None:
				return True
		return False

	def have_deposit(self, building_id):
		""" returns true if there is a resource deposit inside the settlement """
		for building in self.land_manager.resource_deposits[building_id]:
			if building.settlement is None:
				continue
			coords = building.position.origin.to_tuple()
			if coords in self.settlement.ground_map:
				return True
		return False

	def min_residential_level(self):
		result = None
		for building in self.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS):
			if result is None or result > building.level:
				result = building.level
		return result

	def get_total_missing_production(self, resource_id):
		total = 0.0
		for settlement_manager in self.owner.settlement_managers:
			usage = settlement_manager.get_resident_resource_usage(resource_id) * self.personality.production_level_multiplier
			production = settlement_manager.get_resource_production(resource_id)
			resource_import = settlement_manager.get_resource_import(resource_id)
			resource_export = settlement_manager.get_resource_export(resource_id)
			total += usage
			if settlement_manager is not self:
				total -= production + resource_export - resource_import
		return max(0.0, total)

	def need_more_storage(self):
		limit = self.settlement.inventory.get_limit(RES.FOOD_ID)
		if limit >= self.personality.max_required_storage_space:
			return False
		important_resources = [RES.FOOD_ID, RES.TEXTILE_ID, RES.LIQUOR_ID]
		for resource_id in important_resources:
			if self.settlement.inventory[resource_id] + self.personality.full_storage_threshold >= limit:
				return True
		return False

	def _start_feeder_tick(self):
		self.log.info('%s food requirement %.5f', self, self.get_total_missing_production(RES.FOOD_ID))
		self.log.info('%s textile requirement %.5f', self, self.get_total_missing_production(RES.TEXTILE_ID))
		self.log.info('%s liquor requirement %.5f', self, self.get_total_missing_production(RES.LIQUOR_ID))
		self.production_builder.manage_production()
		self.resource_manager.refresh()

	def _end_feeder_tick(self):
		self.resource_manager.replay_deep_low_priority_requests()
		self.resource_manager.record_expected_exportable_production(self.owner.tick_interval)
		self.resource_manager.manager_buysell()
		self.resource_manager.finish_tick()

	def _start_general_tick(self):
		self.log.info('%s food production         %.5f / %.5f', self, self.get_resource_production(RES.FOOD_ID), \
			self.get_resident_resource_usage(RES.FOOD_ID))
		self.log.info('%s textile production      %.5f / %.5f', self, self.get_resource_production(RES.TEXTILE_ID), \
			self.get_resident_resource_usage(RES.TEXTILE_ID))
		self.log.info('%s get-together production %.5f / %.5f', self, self.get_resource_production(RES.GET_TOGETHER_ID), \
			self.get_resident_resource_usage(RES.GET_TOGETHER_ID))
		self.production_builder.manage_production()
		self.trade_manager.refresh()
		self.resource_manager.refresh()
		self.need_materials = False
		have_bricks = self.get_resource_production(RES.BRICKS_ID) > 0

	def _end_general_tick(self):
		if self.land_manager.owner.settler_level == 0:
			# if we are on level 0 and there is a house that can be upgraded then do it.
			if self.manual_upgrade(0, 1):
				self.set_taxes_and_permissions(self.personality.early_sailor_taxes, self.personality.early_pioneer_taxes, \
					self.personality.early_settler_taxes, self.personality.early_sailor_upgrades, self.personality.early_pioneer_upgrades)
		elif self.get_resource_production(RES.BRICKS_ID) > 1e-9 and not self.count_buildings(BUILDINGS.VILLAGE_SCHOOL_CLASS):
			# if we just need the school then upgrade sailors manually
			free_boards = self.settlement.inventory[RES.BOARDS_ID]
			free_boards -= Entities.buildings[BUILDINGS.VILLAGE_SCHOOL_CLASS].costs[RES.BOARDS_ID]
			free_boards /= 2 # TODO: load this from upgrade resources
			if free_boards > 0:
				self.manual_upgrade(0, free_boards)
			self.set_taxes_and_permissions(self.personality.no_school_sailor_taxes, self.personality.no_school_pioneer_taxes, \
				self.personality.no_school_settler_taxes, self.personality.no_school_sailor_upgrades, self.personality.no_school_pioneer_upgrades)
		elif self.count_buildings(BUILDINGS.VILLAGE_SCHOOL_CLASS):
			if self.need_materials:
				self.set_taxes_and_permissions(self.personality.school_sailor_taxes, self.personality.school_pioneer_taxes, \
					self.personality.school_settler_taxes, self.personality.school_sailor_upgrades, self.personality.school_pioneer_upgrades)
			else:
				self.set_taxes_and_permissions(self.personality.final_sailor_taxes, self.personality.final_pioneer_taxes, \
					self.personality.final_settler_taxes, self.personality.final_sailor_upgrades, self.personality.final_pioneer_upgrades)

		self.trade_manager.finalize_requests()
		self.trade_manager.organize_shipping()
		self.resource_manager.record_expected_exportable_production(self.owner.tick_interval)
		self.resource_manager.manager_buysell()
		self.resource_manager.finish_tick()

	def _add_goals(self, goals):
		for goal in self.goals:
			if goal.can_be_activated:
				goal.update()
				goals.append(goal)

	def tick(self, goals):
		if self.feeder_island:
			self._start_feeder_tick()
			self._add_goals(goals)
			self._end_feeder_tick()
		else:
			self._start_general_tick()
			self._add_goals(goals)
			self._end_general_tick()

	def add_building(self, building):
		coords = building.position.origin.to_tuple()
		if coords in self.village_builder.plan:
			self.village_builder.add_building(building)
		else:
			self.production_builder.add_building(building)

	def remove_building(self, building):
		coords = building.position.origin.to_tuple()
		if coords in self.village_builder.plan:
			self.village_builder.remove_building(building)
		else:
			self.production_builder.remove_building(building)

	def handle_lost_area(self, coords_list):
		"""
		* remove the lost area from the village, production, and road areas
		* remove village sections with impossible main squares
		* remove all planned buildings that are now impossible from the village area
		* if the village area takes too much of the total area then remove / reduce the remaining sections (TODO)
		* remove planned fields that are now impossible
		"""

		self.land_manager.handle_lost_area(coords_list)
		self.village_builder.handle_lost_area(coords_list)
		self.production_builder.handle_lost_area(coords_list)
		self.production_builder.handle_new_area()
		self.village_builder.display()
		self.production_builder.display()

	def __str__(self):
		return '%s.SM(%s/%d)' % (self.owner, self.settlement.name if hasattr(self, 'settlement') else 'unknown', self.worldid)

decorators.bind_all(SettlementManager)
