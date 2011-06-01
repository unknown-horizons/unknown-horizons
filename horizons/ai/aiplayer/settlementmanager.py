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

from villagebuilder import VillageBuilder
from productionbuilder import ProductionBuilder

from horizons.scheduler import Scheduler
from horizons.util import Callback
from horizons.util.python import decorators

class SettlementManager(object):
	"""
	An object of this class control one settlement of an AI player.
	"""

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, owner, land_manager, branch_office):
		self.owner = owner
		self.land_manager = land_manager
		self.branch_office = branch_office

		self.village_builder = VillageBuilder(self.land_manager)
		self.village_builder.create_plan()
		self.production_builder = ProductionBuilder(self.land_manager, branch_office)
		self.village_builder.display()
		self.production_builder.display()

		self.build_queue = deque()
		self.tents = 0
		self.num_fishers = 0
		self.ticker_finished = False

		self.build_queue.append(self.village_builder.build_roads)
		self.build_queue.append(self.production_builder.build_lumberjack)
		self.build_queue.append(self.production_builder.build_lumberjack)
		self.build_queue.append(self.village_builder.build_main_square)
		Scheduler().add_new_object(Callback(self.tick), self, run_in = 31)

	def can_provide_resources(self):
		return self.ticker_finished

	def enough_fishers(self):
		return self.tents + 1 <= 3 * self.num_fishers

	def tick(self):
		call_again = False
		if len(self.build_queue) > 0:
			self.log.info('ai.settlement.tick: build a queue item')
			task = self.build_queue.popleft()
			task()
			call_again = True
		elif self.village_builder.tents_to_build > self.tents:
			if not self.enough_fishers():
				if self.production_builder.enough_collectors():
					(details, success) = self.production_builder.build_fisher()
					if success:
						self.log.info('ai.settlement.tick: built a fisher')
						self.num_fishers += 1
						call_again = True
					elif details is not None:
						self.log.info('ai.settlement.tick: not enough materials to build a fisher')
						call_again = True
					else:
						self.log.info('ai.settlement.tick: failed to build a fisher')
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
			else:
				(tent, success) = self.village_builder.build_tent()
				if success:
					self.log.info('ai.settlement.tick: built a tent')
					self.tents += 1
					call_again = True
				elif tent is not None:
					self.log.info('ai.settlement.tick: not enough materials to build a tent')
					call_again = True
				else:
					self.log.info('ai.settlement.tick: failed to build a tent')

		if call_again:
			Scheduler().add_new_object(Callback(self.tick), self, run_in = 32)
		else:
			self.log.info('ai.settlement.tick: everything is done')
			self.ticker_finished = True

decorators.bind_all(SettlementManager)
