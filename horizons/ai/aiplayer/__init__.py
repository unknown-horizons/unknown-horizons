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

from collections import defaultdict

from mission.foundsettlement import FoundSettlement
from mission.preparefoundationship import PrepareFoundationShip
from mission.domestictrade import DomesticTrade
from mission.specialdomestictrade import SpecialDomesticTrade
from mission.internationaltrade import InternationalTrade

from personalitymanager import PersonalityManager
from landmanager import LandManager
from settlementmanager import SettlementManager
from unitbuilder import UnitBuilder
from constants import GOAL_RESULT
from builder import Builder
from specialdomestictrademanager import SpecialDomesticTradeManager
from internationaltrademanager import InternationalTradeManager
from settlementfounder import SettlementFounder

# all subclasses of AbstractBuilding have to be imported here to register the available buildings
from building import AbstractBuilding
from building.farm import AbstractFarm, FarmEvaluator
from building.field import AbstractField
from building.weaver import AbstractWeaver
from building.distillery import AbstractDistillery
from building.villagebuilding import AbstractVillageBuilding
from building.claydeposit import AbstractClayDeposit
from building.claypit import AbstractClayPit
from building.brickyard import AbstractBrickyard
from building.firestation import AbstractFireStation
from building.fishdeposit import AbstractFishDeposit
from building.fisher import AbstractFisher
from building.tree import AbstractTree
from building.lumberjack import AbstractLumberjack
from building.irondeposit import AbstractIronDeposit
from building.ironmine import AbstractIronMine
from building.charcoalburner import AbstractCharcoalBurner
from building.smeltery import AbstractSmeltery
from building.toolmaker import AbstractToolmaker
from building.boatbuilder import AbstractBoatBuilder
from building.signalfire import AbstractSignalFire
from building.tobacconist import AbstractTobacconist
from building.saltponds import AbstractSaltPonds

from goal.settlementgoal import SettlementGoal
from goal.donothing import DoNothingGoal

from horizons.scheduler import Scheduler
from horizons.util import Callback, WorldObject
from horizons.ext.enum import Enum
from horizons.ai.generic import GenericAI
from horizons.util.python import decorators
from horizons.world.component.selectablecomponent import SelectableComponent

class AIPlayer(GenericAI):
	"""This is the AI that builds settlements."""

	shipStates = Enum.get_extended(GenericAI.shipStates, 'on_a_mission')

	log = logging.getLogger("ai.aiplayer")
	tick_interval = 32

	def __init__(self, session, id, name, color, difficulty_level, **kwargs):
		super(AIPlayer, self).__init__(session, id, name, color, difficulty_level, **kwargs)
		self.need_more_ships = False
		self.need_feeder_island = False
		self.personality_manager = PersonalityManager(self)
		self.__init()
		Scheduler().add_new_object(Callback(self.finish_init), self, run_in = 0)

	def start(self):
		""" Start the AI tick process. Try to space out their ticks evenly. """
		ai_players = 0
		position = None
		for i in xrange(len(self.world.players)):
			player = self.world.players[i]
			if isinstance(player, AIPlayer):
				if player is self:
					position = ai_players
				ai_players += 1
		Scheduler().add_new_object(Callback(self.tick), self, run_in = self.tick_interval * position / ai_players + 1)

	def finish_init(self):
		# initialise the things that couldn't be initialised before because of the loading order
		self.refresh_ships()
		self.start()

	def refresh_ships(self):
		""" called when a new ship is added to the fleet """
		for ship in self.world.ships:
			if ship.owner == self and ship.has_component(SelectableComponent) and ship not in self.ships:
				self.log.info('%s Added %s to the fleet', self, ship)
				self.ships[ship] = self.shipStates.idle
		self.need_more_ships = False

	def __init(self):
		self._enabled = True # whether this player is enabled (currently disabled at the end of the game)
		self.world = self.session.world
		self.islands = {}
		self.settlement_managers = []
		self._settlement_manager_by_settlement_id = {}
		self.missions = set()
		self.fishers = []
		self.settlement_founder = SettlementFounder(self)
		self.unit_builder = UnitBuilder(self)
		self.settlement_expansions = [] # [(coords, settlement)]
		self.goals = [DoNothingGoal(self)]
		self.special_domestic_trade_manager = SpecialDomesticTradeManager(self)
		self.international_trade_manager = InternationalTradeManager(self)

	def start_mission(self, mission):
		self.ships[mission.ship] = self.shipStates.on_a_mission
		self.missions.add(mission)
		mission.start()

	def report_success(self, mission, msg):
		if not self._enabled:
			return
		self.missions.remove(mission)
		if mission.ship and mission.ship in self.ships:
			self.ships[mission.ship] = self.shipStates.idle
		if isinstance(mission, FoundSettlement):
			settlement_manager = SettlementManager(self, mission.land_manager)
			self.settlement_managers.append(settlement_manager)
			self._settlement_manager_by_settlement_id[settlement_manager.settlement.worldid] = settlement_manager
			self.add_building(settlement_manager.settlement.warehouse)
			if settlement_manager.feeder_island:
				self.need_feeder_island = False
		elif isinstance(mission, PrepareFoundationShip):
			self.settlement_founder.tick()

	def report_failure(self, mission, msg):
		if not self._enabled:
			return
		self.missions.remove(mission)
		if mission.ship and mission.ship in self.ships:
			self.ships[mission.ship] = self.shipStates.idle
		if isinstance(mission, FoundSettlement):
			del self.islands[mission.land_manager.island.worldid]

	def save(self, db):
		super(AIPlayer, self).save(db)

		# save the player
		db("UPDATE player SET client_id = 'AIPlayer' WHERE rowid = ?", self.worldid)
		current_callback = Callback(self.tick)
		calls = Scheduler().get_classinst_calls(self, current_callback)
		assert len(calls) == 1, "got %s calls for saving %s: %s" % (len(calls), current_callback, calls)
		remaining_ticks = max(calls.values()[0], 1)
		db("INSERT INTO ai_player(rowid, need_more_ships, need_feeder_island, remaining_ticks) VALUES(?, ?, ?, ?)", \
			self.worldid, self.need_more_ships, self.need_feeder_island, remaining_ticks)

		# save the ships
		for ship, state in self.ships.iteritems():
			db("INSERT INTO ai_ship(rowid, owner, state) VALUES(?, ?, ?)", ship.worldid, self.worldid, state.index)

		# save the land managers
		for land_manager in self.islands.itervalues():
			land_manager.save(db)

		# save the settlement managers
		for settlement_manager in self.settlement_managers:
			settlement_manager.save(db)

		# save the missions
		for mission in self.missions:
			mission.save(db)

		# save the personality manager
		self.personality_manager.save(db)

	def _load(self, db, worldid):
		super(AIPlayer, self)._load(db, worldid)
		self.personality_manager = PersonalityManager.load(db, self)
		self.__init()

		self.need_more_ships, self.need_feeder_island, remaining_ticks = \
			db("SELECT need_more_ships, need_feeder_island, remaining_ticks FROM ai_player WHERE rowid = ?", worldid)[0]
		Scheduler().add_new_object(Callback(self.tick), self, run_in = remaining_ticks)

	def finish_loading(self, db):
		""" This is called separately because most objects are loaded after the player. """

		# load the ships
		for ship_id, state_id in db("SELECT rowid, state FROM ai_ship WHERE owner = ?", self.worldid):
			ship = WorldObject.get_object_by_id(ship_id)
			self.ships[ship] = self.shipStates[state_id]

		# load the land managers
		for (worldid,) in db("SELECT rowid FROM ai_land_manager WHERE owner = ?", self.worldid):
			land_manager = LandManager.load(db, self, worldid)
			self.islands[land_manager.island.worldid] = land_manager

		# load the settlement managers and settlement foundation missions
		for land_manager in self.islands.itervalues():
			db_result = db("SELECT rowid FROM ai_settlement_manager WHERE land_manager = ?", land_manager.worldid)
			if db_result:
				settlement_manager = SettlementManager.load(db, self, db_result[0][0])
				self.settlement_managers.append(settlement_manager)
				self._settlement_manager_by_settlement_id[settlement_manager.settlement.worldid] = settlement_manager

				# load the foundation ship preparing missions
				db_result = db("SELECT rowid FROM ai_mission_prepare_foundation_ship WHERE settlement_manager = ?", \
					settlement_manager.worldid)
				for (mission_id,) in db_result:
					self.missions.add(PrepareFoundationShip.load(db, mission_id, self.report_success, self.report_failure))
			else:
				mission_id = db("SELECT rowid FROM ai_mission_found_settlement WHERE land_manager = ?", land_manager.worldid)[0][0]
				self.missions.add(FoundSettlement.load(db, mission_id, self.report_success, self.report_failure))

		for settlement_manager in self.settlement_managers:
			# load the domestic trade missions
			db_result = db("SELECT rowid FROM ai_mission_domestic_trade WHERE source_settlement_manager = ?", settlement_manager.worldid)
			for (mission_id,) in db_result:
				self.missions.add(DomesticTrade.load(db, mission_id, self.report_success, self.report_failure))

			# load the special domestic trade missions
			db_result = db("SELECT rowid FROM ai_mission_special_domestic_trade WHERE source_settlement_manager = ?", settlement_manager.worldid)
			for (mission_id,) in db_result:
				self.missions.add(SpecialDomesticTrade.load(db, mission_id, self.report_success, self.report_failure))

			# load the international trade missions
			db_result = db("SELECT rowid FROM ai_mission_international_trade WHERE settlement_manager = ?", settlement_manager.worldid)
			for (mission_id,) in db_result:
				self.missions.add(InternationalTrade.load(db, mission_id, self.report_success, self.report_failure))

	def tick(self):
		Scheduler().add_new_object(Callback(self.tick), self, run_in = self.tick_interval)
		self.settlement_founder.tick()
		self.handle_enemy_expansions()
		self.handle_settlements()
		self.special_domestic_trade_manager.tick()
		self.international_trade_manager.tick()

	def handle_settlements(self):
		goals = []
		for goal in self.goals:
			if goal.can_be_activated:
				goal.update()
				goals.append(goal)
		for settlement_manager in self.settlement_managers:
			settlement_manager.tick(goals)
		goals.sort(reverse = True)

		settlements_blocked = set() # set([settlement_manager_id, ...])
		for goal in goals:
			if not goal.active:
				continue
			if isinstance(goal, SettlementGoal) and goal.settlement_manager.worldid in settlements_blocked:
				continue # can't build anything in this settlement
			result = goal.execute()
			if result == GOAL_RESULT.SKIP:
				self.log.info('%s, skipped goal %s', self, goal)
			elif result == GOAL_RESULT.BLOCK_SETTLEMENT_RESOURCE_USAGE:
				self.log.info('%s blocked further settlement resource usage by goal %s', self, goal)
				settlements_blocked.add(goal.settlement_manager.worldid)
				goal.settlement_manager.need_materials = True
			else:
				self.log.info('%s all further goals during this tick blocked by goal %s', self, goal)
				break # built something; stop because otherwise the AI could look too fast

		self.log.info('%s had %d active goals', self, sum(goal.active for goal in goals))
		for goal in goals:
			if goal.active:
				self.log.info('%s %s', self, goal)

		# refresh taxes and upgrade permissions
		for settlement_manager in self.settlement_managers:
			settlement_manager.refresh_taxes_and_upgrade_permissions()

	def request_ship(self):
		self.log.info('%s received request for more ships', self)
		self.need_more_ships = True

	def add_building(self, building):
		# if the id is not present then this is a new settlement that has to be handled separately
		if building.settlement.worldid in self._settlement_manager_by_settlement_id:
			self._settlement_manager_by_settlement_id[building.settlement.worldid].add_building(building)

	def remove_building(self, building):
		if not self._enabled:
			return
		self._settlement_manager_by_settlement_id[building.settlement.worldid].remove_building(building)

	def remove_unit(self, unit):
		if not self._enabled:
			return
		if unit in self.ships:
			del self.ships[unit]

	def count_buildings(self, building_id):
		return sum(settlement_manager.settlement.count_buildings(building_id) for settlement_manager in self.settlement_managers)

	def notify_unit_path_blocked(self, unit):
		self.log.warning("%s ship blocked (%s)", self, unit)

	def notify_mine_empty(self, mine):
		"""The Mine calls this function to let the player know that the mine is empty."""
		self._settlement_manager_by_settlement_id[mine.settlement.worldid].production_builder.handle_mine_empty(mine)

	def on_settlement_expansion(self, settlement, coords):
		""" stores the ownership change in a list for later processing """
		if settlement.owner is not self:
			self.settlement_expansions.append((coords, settlement))

	def handle_enemy_expansions(self):
		if not self.settlement_expansions:
			return # no changes in land ownership

		change_lists = defaultdict(lambda: [])
		for coords, settlement in self.settlement_expansions:
			if settlement.island.worldid not in self.islands:
				continue # we don't have a settlement there and have no current plans to create one
			change_lists[settlement.island.worldid].append(coords)
		self.settlement_expansions = []
		if not change_lists:
			return # no changes in land ownership on islands we care about

		for island_id, changed_coords in change_lists.iteritems():
			affects_us = False
			land_manager = self.islands[island_id]
			for coords in changed_coords:
				if coords in land_manager.production or coords in land_manager.village:
					affects_us = True
					break
			if not affects_us:
				continue # we weren't using that land anyway

			settlement_manager = None
			for potential_settlement_manager in self.settlement_managers:
				if potential_settlement_manager.settlement.island.worldid == island_id:
					settlement_manager = potential_settlement_manager
					break

			if settlement_manager is None:
				self.handle_enemy_settling_on_our_chosen_island(island_id)
				# we are on the way to found a settlement on that island
			else:
				# we already have a settlement there
				settlement_manager.handle_lost_area(changed_coords)

	def handle_enemy_settling_on_our_chosen_island(self, island_id):
		mission = None
		for a_mission in self.missions:
			if isinstance(a_mission, FoundSettlement) and a_mission.land_manager.island.worldid == island_id:
				mission = a_mission
				break
		assert mission
		mission.cancel()
		self.settlement_founder.tick()

	@classmethod
	def load_abstract_buildings(cls, db):
		AbstractBuilding.load_all(db)

	@classmethod
	def clear_caches(cls):
		Builder.cache.clear()
		FarmEvaluator.clear_cache()

	def __str__(self):
		return 'AI(%s/%s)' % (self.name if hasattr(self, 'name') else 'unknown', self.worldid if hasattr(self, 'worldid') else 'none')

	def end(self):
		self._enabled = False
		self.personality_manager = None
		self.world = None
		self.islands = None
		self.settlement_managers = None
		self._settlement_manager_by_settlement_id = None
		self.missions = None
		self.fishers = None
		self.settlement_founder = None
		self.unit_builder = None
		self.settlement_expansions = None
		self.goals = None
		self.special_domestic_trade_manager = None
		self.international_trade_manager = None
		super(AIPlayer, self).end()

decorators.bind_all(AIPlayer)
