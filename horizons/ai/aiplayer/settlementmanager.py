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

from constants import BUILD_RESULT
from villagebuilder import VillageBuilder
from productionbuilder import ProductionBuilder

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject
from horizons.util.python import decorators
from horizons.command.uioptions import SetTaxSetting
from horizons.constants import RES, PRODUCTION, GAME_SPEED

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
		self.num_potato_fields = 0
		self.village_built = False

		self.build_queue.append(self.buildCallType.village_roads)
		self.build_queue.append(self.buildCallType.production_lumberjack)
		self.build_queue.append(self.buildCallType.production_lumberjack)
		self.build_queue.append(self.buildCallType.village_main_square)
		Scheduler().add_new_object(Callback(self.tick), self, run_in = 31)
		SetTaxSetting(self.land_manager.settlement, 0.5).execute(self.land_manager.session)
		self.log.info('ai.settlement.tick: set tax rate to 0.5')

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
		self.num_potato_fields = self.production_builder.count_potato_fields()
		self.village_built = self.tents == self.village_builder.tents_to_build

	def can_provide_resources(self):
		return self.village_built

	def enough_food_producers(self):
		# over-produce by a small amount
		return self.get_resource_production(RES.FOOD_ID)[0] > self.get_resident_resource_usage(RES.FOOD_ID) * 1.05 + 0.001

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

	def tick(self):
		self.log.info('current food production %.5f, consumption %.5f', \
			self.get_resource_production(RES.FOOD_ID)[0], self.get_resident_resource_usage(RES.FOOD_ID))
		call_again = False

		if len(self.build_queue) > 0:
			self.log.info('ai.settlement.tick: build a queue item')
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
		elif not self.enough_food_producers():
			if self.production_builder.enough_collectors():
				result = self.production_builder.build_food_producer()
				if result == BUILD_RESULT.OK:
					self.log.info('ai.settlement.tick: built a food producer')
					call_again = True
				elif result == BUILD_RESULT.NEED_RESOURCES:
					self.log.info('ai.settlement.tick: not enough materials to build a food producer')
					call_again = True
				else:
					self.log.info('ai.settlement.tick: failed to build a food producer')
			else:
				(details, success) = self.production_builder.improve_collector_coverage()
				if success:
					self.log.info('ai.settlement.tick: built a storage')
					call_again = True
				elif details is not None:
					self.log.info('ai.settlement.tick: not enough materials to build a storage')
					call_again = True
				else:
					self.log.info('ai.settlement.tick: failed to build a storage')
		elif self.village_builder.tents_to_build > self.tents:
			result = self.village_builder.build_tent()
			if result == BUILD_RESULT.OK:
				self.log.info('ai.settlement.tick: built a tent')
				self.tents += 1
				call_again = True
			elif result == BUILD_RESULT.NEED_RESOURCES:
				self.log.info('ai.settlement.tick: not enough materials to build a tent')
				call_again = True
			else:
				self.log.info('ai.settlement.tick: failed to build a tent')

		Scheduler().add_new_object(Callback(self.tick), self, run_in = 32)
		if not call_again:
			self.village_built = True

decorators.bind_all(SettlementManager)
