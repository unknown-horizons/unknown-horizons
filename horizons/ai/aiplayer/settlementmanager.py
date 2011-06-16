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

import logging

from collections import deque

from constants import BUILD_RESULT, PRODUCTION_PURPOSE
from villagebuilder import VillageBuilder
from productionbuilder import ProductionBuilder

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject
from horizons.util.python import decorators
from horizons.command.uioptions import SetTaxSetting, SetSettlementUpgradePermissions
from horizons.command.production import ToggleActive
from horizons.constants import BUILDINGS, RES, PRODUCTION, GAME_SPEED
from horizons.entities import Entities

class SettlementManager(WorldObject):
	"""
	An object of this class control one settlement of an AI player.
	"""

	log = logging.getLogger("ai.aiplayer")

	class buildCallType:
		village_roads = 1
		village_main_square = 2
		production_lumberjack = 3

	def __init__(self, land_manager, branch_office):
		super(SettlementManager, self).__init__()
		self.__init(land_manager, branch_office)

		self.village_builder = VillageBuilder(self)
		self.production_builder = ProductionBuilder(self)
		self.village_builder.display()
		self.production_builder.display()

		self.tents = 0
		self.num_fishers = 0
		self.num_fields = {PRODUCTION_PURPOSE.POTATO_FIELD: 0, PRODUCTION_PURPOSE.PASTURE: 0}
		self.village_built = False

		self.build_queue.append(self.buildCallType.village_roads)
		self.build_queue.append(self.buildCallType.production_lumberjack)
		self.build_queue.append(self.buildCallType.production_lumberjack)
		self.build_queue.append(self.buildCallType.village_main_square)
		Scheduler().add_new_object(Callback(self.tick), self, run_in = 31)
		self.set_taxes_and_permissions(0.5, False, False)

	def __init(self, land_manager, branch_office):
		self.owner = land_manager.owner
		self.land_manager = land_manager
		self.branch_office = branch_office

		self.build_queue = deque()

	def save(self, db):
		super(SettlementManager, self).save(db)
		current_callback = Callback(self.tick)
		calls = Scheduler().get_classinst_calls(self, current_callback)
		assert len(calls) <= 1, "got %s calls for saving %s: %s" % (len(calls), current_callback, calls)
		remaining_ticks = None if len(calls) == 0 else max(calls.values()[0], 1)
		db("INSERT INTO ai_settlement_manager(rowid, land_manager, branch_office, remaining_ticks) VALUES(?, ?, ?, ?)", \
			self.worldid, self.land_manager.worldid, self.branch_office.worldid, remaining_ticks)

		for task_type in self.build_queue:
			db("INSERT INTO ai_settlement_manager_build_queue(settlement_manager, task_type) VALUES(?, ?)", \
				self.worldid, task_type)

		self.village_builder.save(db)
		self.production_builder.save(db)

	@classmethod
	def load(cls, db, worldid):
		self = cls.__new__(cls)
		self._load(db, worldid)
		return self

	def _load(self, db, worldid):
		super(SettlementManager, self).load(db, worldid)

		# load the main part
		db_result = db("SELECT land_manager, branch_office, remaining_ticks FROM ai_settlement_manager WHERE rowid = ?", worldid)
		(land_manager_id, branch_office_id, remaining_ticks) = db_result[0]
		land_manager = WorldObject.get_object_by_id(land_manager_id)
		branch_office = WorldObject.get_object_by_id(branch_office_id)
		self.__init(land_manager, branch_office)

		# find the settlement
		for settlement in self.owner.session.world.settlements:
			if settlement.owner == self.owner and settlement.island == self.land_manager.island:
				land_manager.settlement = settlement
				break
		assert land_manager.settlement

		Scheduler().add_new_object(Callback(self.tick), self, run_in = remaining_ticks)

		# load the build queue
		for (task_type,) in db("SELECT task_type FROM ai_settlement_manager_build_queue WHERE settlement_manager = ?", worldid):
			self.build_queue.append(task_type)

		# load the master builders
		self.village_builder = VillageBuilder.load(db, self)
		self.production_builder = ProductionBuilder.load(db, self)

		self.village_builder.display()
		self.production_builder.display()

		# TODO: correctly init the following
		self.tents = self.village_builder.count_tents()
		self.num_fishers = self.production_builder.count_fishers()
		self.num_fields = self.production_builder.count_fields()
		self.village_built = self.tents == self.village_builder.tents_to_build

	def set_taxes_and_permissions(self, taxes, sailors_can_upgrade, pioneers_can_upgrade):
		self.log.info('%s tax %.1f, upgrade permissions %s, %s', self, taxes, \
			'A' if sailors_can_upgrade else 'B', 'A' if pioneers_can_upgrade else 'B')
		SetTaxSetting(self.land_manager.settlement, taxes).execute(self.land_manager.session)
		SetSettlementUpgradePermissions(self.land_manager.settlement, 0, sailors_can_upgrade).execute(self.land_manager.session)
		SetSettlementUpgradePermissions(self.land_manager.settlement, 1, pioneers_can_upgrade).execute(self.land_manager.session)

	def can_provide_resources(self):
		return self.village_built

	def enough_resource_producers(self, produced_resource, consumed_resource):
		"""Returns false if and only if we are producing less than we should and we have a place to store it."""
		have = self.get_resource_production(produced_resource)[0]
		need = self.get_resident_resource_usage(consumed_resource) * 1.02 + 0.001
		if have >= need:
			return True
		storage_size = self.land_manager.settlement.inventory.get_limit(produced_resource)
		storage_used = self.land_manager.settlement.inventory[produced_resource]
		return storage_used >= storage_size * 0.7 + 4

	def need_weavers(self):
		# TODO: do this the right way...
		weaver_time = 12.0
		pasture_time = 30.0
		return self.count_buildings(BUILDINGS.PASTURE_CLASS) / pasture_time > self.count_buildings(BUILDINGS.WEAVER_CLASS) / weaver_time + 1e-9

	def enough_textile_producers(self):
		if self.need_weavers():
			return False
		return self.enough_resource_producers(RES.WOOL_ID, RES.TEXTILE_ID)

	def get_resource_production(self, resource_id):
		providers = 0
		new_providers = 0
		amount = 0
		for builder in self.production_builder.production_buildings:
			point = builder.position.origin
			coords = (point.x, point.y)
			building = self.land_manager.settlement.ground_map[coords].object
			if building.get_history_length(resource_id) is None:
				continue
			# TODO; make this work properly for farms where fields are added incrementally
			if building.get_history_length(resource_id) < PRODUCTION.COUNTER_LIMIT:
				new_providers += 1
				amount += building.get_expected_production_level(resource_id)
			else:
				providers += 1
				amount += building.get_absolute_production_level(resource_id)
		return (amount, providers, new_providers)

	def get_resident_resource_usage(self, resource_id):
		total = 0
		for coords, (purpose, _) in self.village_builder.plan.iteritems():
			if purpose != self.village_builder.purpose.tent:
				continue
			tent = self.land_manager.settlement.ground_map[coords].object
			for production in tent._get_productions():
				production_line = production._prod_line
				if resource_id in production_line.consumed_res:
					# subtract because the amount will be negative
					total -= production_line.consumed_res[resource_id] / production_line.time / GAME_SPEED.TICKS_PER_SECOND
		return total

	def log_generic_build_result(self, result, call_again, name):
		if result == BUILD_RESULT.OK:
			self.log.info('%s built a %s', self, name)
			call_again = True
		elif result == BUILD_RESULT.NEED_RESOURCES:
			self.log.info('%s not enough materials to build a %s', self, name)
			call_again = True
		else:
			self.log.info('%s failed to build a %s', self, name)

	def count_buildings(self, building_id):
		return len(self.land_manager.settlement.get_buildings_by_id(building_id))

	def manage_production(self):
		"""Pauses and resumes production buildings when they have full inventories."""
		for building in self.production_builder.production_buildings:
			for production in building._get_productions():
				all_full = True

				# inventory full of the produced resources?
				to_check = production._prod_line.production if building.id != BUILDINGS.CLAY_PIT_CLASS else production.get_produced_res()
				for resource_id in to_check:
					if production.inventory.get_free_space_for(resource_id) > 0:
						all_full = False
						break

				if all_full:
					if not production.is_paused():
						ToggleActive(building, production).execute(self.land_manager.session)
						self.log.info('%s paused a production at %s/%d', self, building.name, building.worldid)
				else:
					if production.is_paused():
						ToggleActive(building, production).execute(self.land_manager.session)
						self.log.info('%s resumed a production at %s/%d', self, building.name, building.worldid)

	def manual_upgrade(self, level, limit):
		"""Enables upgrading residence buildings on the specified level until at least limit of them are upgrading."""
		num_upgrading = 0
		for building in self.land_manager.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS):
			if building.level == level:
				upgrade_production = building._get_upgrade_production()
				if upgrade_production is not None and not upgrade_production.is_paused():
					num_upgrading += 1
					if num_upgrading >= limit:
						return False

		upgraded_any = False
		for building in self.land_manager.settlement.get_buildings_by_id(BUILDINGS.RESIDENTIAL_CLASS):
			if building.level == level:
				upgrade_production = building._get_upgrade_production()
				if upgrade_production is not None and upgrade_production.is_paused():
					ToggleActive(building, upgrade_production).execute(self.land_manager.session)
					num_upgrading += 1
					upgraded_any = True
					if num_upgrading >= limit:
						return True
		return upgraded_any

	def tick(self):
		self.log.info('%s food production %.5f / %.5f', self, self.get_resource_production(RES.FOOD_ID)[0], \
			self.get_resident_resource_usage(RES.FOOD_ID))
		self.log.info('%s wool/textile production %.5f / %.5f', self, self.get_resource_production(RES.WOOL_ID)[0], \
			self.get_resident_resource_usage(RES.TEXTILE_ID))
		self.manage_production()
		call_again = False

		if len(self.build_queue) > 0:
			self.log.info('%s build a queue item', self)
			task_type = self.build_queue.popleft()
			if task_type == self.buildCallType.village_roads:
				self.village_builder.build_roads()
			elif task_type == self.buildCallType.village_main_square:
				self.village_builder.build_main_square()
			elif task_type == self.buildCallType.production_lumberjack:
				self.production_builder.build_lumberjack()
			else:
				assert False # this should never happen
			call_again = True
		elif not self.production_builder.enough_collectors():
			result = self.production_builder.improve_collector_coverage()
			self.log_generic_build_result(result, call_again, 'storage')
		elif not self.enough_resource_producers(RES.FOOD_ID, RES.FOOD_ID):
			result = self.production_builder.build_food_producer()
			self.log_generic_build_result(result, call_again, 'food producer')
		elif self.tents >= 10 and self.village_builder.pavilions_to_build > 0:
			result = self.village_builder.build_pavilion()
			self.log_generic_build_result(result, call_again, 'pavilion')
		elif self.tents >= 16 and self.land_manager.owner.settler_level > 0 and not self.enough_textile_producers():
			if self.need_weavers():
				result = self.production_builder.build_weaver()
				self.log_generic_build_result(result, call_again, 'weaver')
			else:
				result = self.production_builder.build_wool_producer()
				self.log_generic_build_result(result, call_again, 'wool producer')
		elif self.village_builder.tents_to_build > self.tents:
			result = self.village_builder.build_tent()
			self.log_generic_build_result(result, call_again, 'tent')
			if result == BUILD_RESULT.OK:
				self.tents += 1
		elif not self.count_buildings(BUILDINGS.CLAY_PIT_CLASS) and self.count_buildings(BUILDINGS.CLAY_DEPOSIT_CLASS):
			result = self.production_builder.build_clay_pit()
			self.log_generic_build_result(result, call_again, 'clay pit')
			self.production_builder.display()
		elif not self.count_buildings(BUILDINGS.BRICKYARD_CLASS) and self.count_buildings(BUILDINGS.CLAY_PIT_CLASS):
			result = self.production_builder.build_brickyard()
			self.log_generic_build_result(result, call_again, 'brickyard')
		elif not self.count_buildings(BUILDINGS.VILLAGE_SCHOOL_CLASS):
			result = self.village_builder.build_village_school()
			self.log_generic_build_result(result, call_again, 'village school')
			if result == BUILD_RESULT.OK:
				self.set_taxes_and_permissions(0.5, True, True)

		if self.land_manager.owner.settler_level == 0:
			# if we are on level 0 and there is a house that can be upgraded then do it.
			if self.manual_upgrade(0, 1):
				self.set_taxes_and_permissions(0.9, False, False)
		elif self.count_buildings(BUILDINGS.BRICKYARD_CLASS) and not self.count_buildings(BUILDINGS.VILLAGE_SCHOOL_CLASS):
			# if we just need the school then upgrade sailors manually
			free_boards = self.land_manager.settlement.inventory[RES.BOARDS_ID]
			free_boards -= Entities.buildings[BUILDINGS.VILLAGE_SCHOOL_CLASS].costs[RES.BOARDS_ID]
			if free_boards > 0:
				self.manual_upgrade(0, free_boards)

		Scheduler().add_new_object(Callback(self.tick), self, run_in = 32)
		if not call_again:
			self.village_built = True

	def __str__(self):
		return '%s.SM(%s/%d)' % (self.owner, self.land_manager.settlement.name, self.worldid)

decorators.bind_all(SettlementManager)
