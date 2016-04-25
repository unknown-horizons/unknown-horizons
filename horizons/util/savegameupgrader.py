# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
import os
import os.path
import json
import shutil
import tempfile

from collections import defaultdict
from sqlite3 import OperationalError
from yaml.parser import ParserError

from horizons.constants import BUILDINGS, VERSION, UNITS
from horizons.entities import Entities
from horizons.util.dbreader import DbReader
from horizons.util.python import decorators
from horizons.util.shapes import Rect
from horizons.util.yamlcache import YamlCache

class SavegameTooOld(Exception):
	def __init__(self, msg=None, revision=None):
		if msg is None:
			msg = "The savegame is too old!"
		if revision is not None:
			msg += " Revision: " + str(revision)
		super(SavegameTooOld, self).__init__(msg)

class SavegameUpgrader(object):
	"""The class that prepares saved games to be loaded by the current version."""

	log = logging.getLogger("util.savegameupgrader")

	def __init__(self, path):
		super(SavegameUpgrader, self).__init__()
		self.original_path = path
		self.using_temp = False
		self.final_path = None

	def _upgrade_to_rev49(self, db):
		db('CREATE TABLE "resource_overview_bar" (object INTEGER NOT NULL, position INTEGER NOT NULL, resource INTEGER NOT NULL)')

	def _upgrade_to_rev50(self, db):
		db('UPDATE stance set stance = "hold_ground_stance" where stance = "hold_ground"')
		db('UPDATE stance set stance = "none_stance" where stance = "none"')
		db('UPDATE stance set stance = "flee_stance" where stance = "flee_stance"')
		db('UPDATE stance set stance = "aggressive_stance" where stance = "aggressive"')

	def _upgrade_to_rev51(self, db):
		# add fire slot to settlers. Use direct numbers since only these work and they must never change.
		for (settler_id, ) in db("SELECT rowid FROM building WHERE type = ?", 3):
			db("INSERT INTO storage_slot_limit(object, slot, value) VALUES(?, ?, ?)",
			   settler_id, 42, 1)

	def _upgrade_to_rev52(self, db):
		# create empty disaster tables
		db('CREATE TABLE "disaster" ( type STRING NOT NULL, settlement INTEGER NOT NULL, remaining_ticks_expand INTEGER NOT NULL)')
		db('CREATE TABLE "fire_disaster" ( disaster INTEGER NOT NULL, building INTEGER NOT NULL, remaining_ticks_havoc INTEGER NOT NULL )')
		db('CREATE TABLE "disaster_manager" ( remaining_ticks INTEGER NOT NULL )')
		db('INSERT INTO "disaster_manager" VALUES(1)')

	def _upgrade_to_rev53(self, db):
		# convert old logbook (heading, message) tuples to new syntax, modify logbook table layout
		old_entries = db("SELECT heading, message FROM logbook")
		db('DROP TABLE logbook')
		db('CREATE TABLE logbook ( widgets STRING )')
		widgets = []
		for heading, message in old_entries:
			add = []
			add.append(['Headline', heading])
			add.append(['Image', "content/gui/images/background/hr.png"])
			add.append(['Label', message])
			widgets.append(add)
		db("INSERT INTO logbook(widgets) VALUES(?)", json.dumps(widgets))

	def _upgrade_to_rev54(self, db):
		for (settlement,) in db("SELECT DISTINCT settlement FROM settlement_level_properties WHERE level = ?", 0):
			db("INSERT INTO settlement_level_properties VALUES(?, 3, 0, 1)", settlement)

	def _upgrade_to_rev55(self, db):
		# The upgrade system has been mishandled, this upgrade tries to fix
		# as much as possible. It's partly brute force and might not work every
		# time, however the savegames are in an undefined state, so recovery is hard

		# make anything inflamable, the code should be able to handle it
		for (obj, ) in db("SELECT rowid FROM building where type != 8"):
			db("INSERT INTO storage_slot_limit (object, slot, value) VALUES (?, ?, ?)",
			   obj, 99, 1)

		# make farm be able to store grain and stuff
		for (obj, ) in db("SELECT rowid FROM building where type = 20"):
			db("INSERT INTO storage_slot_limit (object, slot, value) VALUES (?, ?, ?)",
			   obj, 43, 6)
			db("INSERT INTO storage_slot_limit (object, slot, value) VALUES (?, ?, ?)",
			   obj, 42, 6)

	def _upgrade_to_rev56(self, db):
		db('CREATE TABLE "last_active_settlement" ( type STRING NOT NULL, value INTEGER NOT NULL )')
		db("INSERT INTO last_active_settlement(type, value) VALUES(?, ?)", "LAST_NONE_FLAG", False)

	def _upgrade_to_rev57(self, db):
		"""Change storage of scenario variables from pickle to json."""
		import pickle
		db.connection.text_factory = str # need to read as str, utf-8 chokes on binary pickle

		for key, value in db("SELECT key, value FROM scenario_variables"):
			value = pickle.loads(value)
			value = json.dumps(value)
			db("UPDATE scenario_variables SET value = ? WHERE key = ?", value, key)

	def _upgrade_to_rev58(self, db):
		# multiple resources for collector jobs
		data = [ i for i in db("SELECT rowid, object, resource, amount FROM collector_job") ]
		db("DROP TABLE  collector_job")
		db("CREATE TABLE `collector_job` (`collector` INTEGER, `object` INTEGER DEFAULT NULL, `resource` INTEGER DEFAULT NULL, `amount` INTEGER DEFAULT NULL)")
		for row in data:
			db("INSERT INTO collector_job(collector, object, resource, amount) VALUES(?, ?, ?, ?)", *row)

	def _upgrade_to_rev59(self, db):
		# action set id save/load
		try:
			db("ALTER TABLE concrete_object ADD COLUMN action_set_id STRING DEFAULT NULL")
			# None is not a valid value, but it's hard to determine valid ones here,
			# so as an exception, we let the loading code handle it (in ConcreteObject.load)
		except OperationalError:
			# Some scenario maps had concrete_object updated with 8b3cb4bae1067e
			pass

	def _upgrade_to_rev60(self, db):
		# some production line id changes

		# [(object id, old prod line id, new prod line id)]
		changes = [
			(33, 42, 923331670),
			(9, 18, 1335785398),
			(42, 57, 227255506),
			(20, 8, 21429697),
			(20, 1, 1953634498),
			(20, 4, 70113509),
			(20, 47, 1236502256),
			(20, 52, 2078307024),
			(20, 23, 2092896117),
			(20, 0, 208610842),
			(20, 28, 2053891886),
			(20, 2, 1265004933),
			(20, 51, 1253640427),
			(20, 3, 1849560830),
			(20, 7, 1654557398),
			(60, 0, 532714998),
			(19, 22, 2092896117),
			(63, 2, 2097838825),
			(63, 0, 87034972),
			(63, 1, 570450416),
			(63, 3, 359183511),
			(8, 2, 256812226),
			(26, 34, 1842760585),
			(49, 1, 1953634498),
			(46, 0, 344746552),
			(28, 36, 1510556113),
			(45, 56464472, 1907712664),
			(35, 45, 854772720),
			(55, 0, 1971678669),
			(40, 57, 227255506),
			(54, 0, 1971678669),
			(29, 37, 1698523401),
			(11, 11, 923331670),
			(18, 5, 1654557398),
			(5, 13, 1056282634),
		]
		for obj_type, old_prod_line, new_prod_line in changes:
			for (obj, ) in db("SELECT rowid FROM building WHERE type = ?", obj_type):
				db("UPDATE production SET prod_line_id = ? WHERE owner = ? and prod_line_id = ?", new_prod_line, obj, old_prod_line)

	def _upgrade_to_rev61(self, db):
		from horizons.world.building.settler import SettlerUpgradeData

		# settler upgrade lines used to be the same for several levels
		for (settler, level) in db("SELECT rowid, level FROM building WHERE type = 3"):
			#if settler == 100268:import pdb ; pdb.set_trace()
			# the id used to always be 35
			db("UPDATE production SET prod_line_id = ? WHERE owner = ? and prod_line_id = 35", SettlerUpgradeData.get_production_line_id( level + 1 ), settler)

	def _upgrade_to_rev62(self, db):
		# added a message parameter to the logbook which needs to be saved
		db("CREATE TABLE IF NOT EXISTS logbook_messages ( message STRING )")

	def _upgrade_to_rev63(self, db):
		""" Due to miscommunication, the savegame revision 62 was not changed in
		savegames after updates to 63. To keep savegames functional that have a
		revision of 62 stored but where the upgrade to 63 was executed, we assume
		that this has to happen for savegames of revision <62 unless CREATEing tables
		raises an OperationalError, which indicates that they already exist and thus
		this upgrade routine should also work for savegames with odd upgrade paths:
		There may have been branches storing revision 63 in savegames after all.
		"""
		# adds a table for pirate's 'tick' callback
		try:
			db("CREATE TABLE ai_pirate (remaining_ticks INTEGER NOT NULL DEFAULT 1)")
		except OperationalError:
			return
		db("INSERT INTO ai_pirate (rowid, remaining_ticks) SELECT p.rowid, 1 FROM player p WHERE p.is_pirate")
		# added flag to aiplayer for fighting ships request
		db("ALTER TABLE ai_player ADD COLUMN need_more_combat_ships INTEGER NOT NULL DEFAULT 1")

		# update stance for every pirate player ship
		db('INSERT INTO stance (worldid, stance, state) SELECT u.rowid, "none_stance", "idle" FROM unit u, player p WHERE u.owner=p.rowid AND p.is_pirate=1')

		# update ai_player with long callback function column
		db("ALTER TABLE ai_player ADD COLUMN remaining_ticks_long INTEGER NOT NULL DEFAULT 1")

		# update ai_pirate with long callback function column
		db("ALTER TABLE ai_pirate ADD COLUMN remaining_ticks_long INTEGER NOT NULL DEFAULT 1")

		# Combat missions below:
		# Abstract FleetMission data
		db('CREATE TABLE "ai_fleet_mission" ( "owner_id" INTEGER NOT NULL , "fleet_id" INTEGER NOT NULL , "state_id" INTEGER NOT NULL, "combat_phase" BOOL NOT NULL )')
		# ScoutingMission
		db('CREATE TABLE "ai_scouting_mission" ("owner" INTEGER NOT NULL , "ship" INTEGER NOT NULL , "starting_point_x" INTEGER NOT NULL, '
		   '"starting_point_y" INTEGER NOT NULL, "target_point_x" INTEGER NOT NULL, "target_point_y" INTEGER NOT NULL, "state" INTEGER NOT NULL )')
		# SurpriseAttack
		db('CREATE TABLE "ai_mission_surprise_attack" ("enemy_player_id" INTEGER NOT NULL, "target_point_x" INTEGER NOT NULL, "target_point_y" INTEGER NOT NULL,'
		   '"target_point_radius" INTEGER NOT NULL, "return_point_x" INTEGER NOT NULL, "return_point_y" INTEGER NOT NULL )')
		# ChaseShipsAndAttack
		db('CREATE TABLE "ai_mission_chase_ships_and_attack" ("target_ship_id" INTEGER NOT NULL )')

		# BehaviorManager
		db('CREATE TABLE "ai_behavior_manager" ("owner_id" INTEGER NOT NULL, "profile_token" INTEGER NOT NULL)')

		# No previous token was present, choose anything really
		db('INSERT INTO ai_behavior_manager (owner_id, profile_token) SELECT p.rowid, 42 FROM player p')

		# Locks for Conditions being resolved by StrategyManager
		db('CREATE TABLE "ai_condition_lock" ("owner_id" INTEGER NOT NULL, "condition" TEXT NOT NULL, "mission_id" INTEGER NOT NULL)')

		# Fleets
		db('CREATE TABLE "fleet" ("fleet_id" INTEGER NOT NULL, "owner_id" INTEGER NOT NULL, "state_id" INTEGER NOT NULL, "dest_x" '
		   'INTEGER, "dest_y" INTEGER, "radius" INTEGER, "ratio" DOUBLE)')

		# ships per given fleet
		db('CREATE TABLE "fleet_ship" ("fleet_id" INTEGER NOT NULL, "ship_id" INTEGER NOT NULL, "state_id" INTEGER NOT NULL)')

		# CombatManager's ship states
		db('CREATE TABLE "ai_combat_ship" ( "owner_id" INTEGER NOT NULL, "ship_id" INTEGER NOT NULL, "state_id" INTEGER NOT NULL )')

		# Set CombatManager's state of ship to idle
		db('INSERT INTO ai_combat_ship (owner_id, ship_id, state_id) SELECT p.rowid, u.rowid, 0 FROM player p, unit u WHERE u.owner = p.rowid AND u.type=? and p.client_id="AIPlayer"', UNITS.FRIGATE)

		# Same for pirate ships
		db('INSERT INTO ai_combat_ship (owner_id, ship_id, state_id) SELECT p.rowid, u.rowid, 0 FROM ai_pirate p, unit u WHERE u.owner = p.rowid')

		# save pirate routine mission
		db('CREATE TABLE "ai_mission_pirate_routine" ("target_point_x" INTEGER NOT NULL, "target_point_y" INTEGER NOT NULL )')

	def _upgrade_to_rev64(self, db):
		db("INSERT INTO metadata VALUES (?, ?)", "max_tier_notification", False)

	def _upgrade_to_rev65(self, db):
		island_path = db("SELECT file FROM island ORDER BY file LIMIT 1")[0][0]
		map_names = {
			'content/islands/bay_and_lake.sqlite': 'development',
			'content/islands/fightForRes_island_0_169.sqlite': 'fight-for-res',
			'content/islands/full_house_island_0_25.sqlite': 'full-house',
			'content/islands/mp-dev_island_0_0.sqlite': 'mp-dev',
			'content/islands/quattro_island_0_19.sqlite': 'quattro',
			'content/islands/rouver_island_0_0.sqlite': 'rouver',
			'content/islands/singularity40_island_0_0.sqlite': 'singularity40',
			'content/islands/tiny.sqlite': 'test-map-tiny',
			'content/islands/triple_island_0_74.sqlite': 'triple'
		}
		if island_path in map_names:
			db('INSERT INTO metadata VALUES (?, ?)', 'map_name', map_names[island_path])
			return

		# random map
		island_strings = []
		for island_x, island_y, island_string in db('SELECT x, y, file FROM island ORDER BY rowid'):
			island_strings.append(island_string + ':%d:%d' % (island_x, island_y))
		db('INSERT INTO metadata VALUES (?, ?)', 'random_island_sequence', ' '.join(island_strings))

	def _upgrade_to_rev66(self, db):
		db("DELETE FROM metadata WHERE name='max_tier_notification'")
		db("ALTER TABLE player ADD COLUMN max_tier_notification INTEGER")
		db("UPDATE player SET max_tier_notification = 0")

	def _upgrade_to_rev67(self, db):
		db('CREATE TABLE "trade_slots" ("trade_post" INT NOT NULL, "slot_id" INT NOT NULL, "resource_id" INT NOT NULL, "selling" BOOL NOT NULL, "trade_limit" INT NOT NULL)')
		for trade_post, in db("SELECT DISTINCT object FROM (SELECT object FROM trade_sell UNION SELECT object FROM trade_buy) ORDER BY object"):
			slot_id = 0
			for table in ['trade_buy', 'trade_sell']:
				for resource_id, limit in db("SELECT resource, trade_limit FROM " + table + " WHERE object = ? ORDER BY object, resource", trade_post):
					db("INSERT INTO trade_slots VALUES(?, ?, ?, ?, ?)", trade_post, slot_id, resource_id, table == 'trade_sell', limit)
					slot_id += 1

	def _upgrade_to_rev68(self, db):
		settlement_founding_missions = []
		db_result = db("SELECT rowid, land_manager, ship, warehouse_builder, state FROM ai_mission_found_settlement")
		for (worldid, land_manager_id, ship_id, builder_id, state) in db_result:
			x, y = db("SELECT x, y FROM ai_builder WHERE rowid = ?", builder_id)[0]
			settlement_founding_missions.append((worldid, land_manager_id, ship_id, x, y, state))

		db("DROP TABLE ai_mission_found_settlement")
		db('CREATE TABLE "ai_mission_found_settlement" ("land_manager" INT NOT NULL, "ship" INT NOT NULL, "x" INT NOT NULL, "y" INT NOT NULL, "state" INT NOT NULL)')

		for row in settlement_founding_missions:
			db("INSERT INTO ai_mission_found_settlement(rowid, land_manager, ship, x, y, state) VALUES(?, ?, ?, ?, ?, ?)", *row)

	def _upgrade_to_rev69(self, db):
		settlement_map = {}
		for data in db("SELECT rowid, data FROM settlement_tiles"):
			settlement_id = int(data[0])
			coords_list = [tuple(raw_coords) for raw_coords in json.loads(data[1])] # json saves tuples as list
			for coords in coords_list:
				settlement_map[coords] = settlement_id
		db("DELETE FROM settlement_tiles")

		for (worldid, building_id, x, y, location_id) in db("SELECT rowid, type, x, y, location FROM building WHERE type = ? OR type = ?",
				                                            BUILDINGS.CLAY_DEPOSIT, BUILDINGS.MOUNTAIN):
			worldid = int(worldid)
			building_id = int(building_id)
			origin_coords = (int(x), int(y))
			location_id = int(location_id)

			settlement_ids = set()
			position = Rect.init_from_topleft_and_size_tuples(origin_coords, Entities.buildings[building_id].size)
			for coords in position.tuple_iter():
				if coords in settlement_map:
					settlement_ids.add(settlement_map[coords])
			if not settlement_ids:
				continue # no settlement covers any of the deposit
			else:
				# assign all of it to the earlier settlement
				settlement_id = sorted(settlement_ids)[0]
				for coords in position.tuple_iter():
					settlement_map[coords] = settlement_id
				if location_id != settlement_id:
					db("UPDATE building SET location = ? WHERE rowid = ?", settlement_id, worldid)

		# save the new settlement tiles data
		ground_map = defaultdict(list)
		for (coords, settlement_id) in settlement_map.iteritems():
			ground_map[settlement_id].append(coords)

		for (settlement_id, coords_list) in ground_map.iteritems():
			data = json.dumps(coords_list)
			db("INSERT INTO settlement_tiles(rowid, data) VALUES(?, ?)", settlement_id, data)

	def _upgrade_to_rev70(self, db):
		db('CREATE TABLE "fish_data" ("last_usage_tick" INT NOT NULL)')
		for row in db("SELECT rowid FROM building WHERE type = ?", BUILDINGS.FISH_DEPOSIT):
			db("INSERT INTO fish_data(rowid, last_usage_tick) VALUES(?, ?)", row[0], -1000000)

	def _upgrade_to_rev71(self, db):
		old = 'MAX_INCR_REACHED'
		new = 'MAX_TIER_REACHED'
		db("UPDATE message_widget_active  SET id = ? WHERE id = ?", new, old)
		db("UPDATE message_widget_archive SET id = ? WHERE id = ?", new, old)

	def _upgrade_to_rev72(self, db):
		# rename fire_disaster to building_influencing_disaster
		db("ALTER TABLE fire_disaster RENAME TO building_influencing_disaster")

	def _upgrade_to_rev73(self, db):
		# Attempt to fix up corrupt yaml dumped into scenario savegames (#2164)
		key = 'scenario_events'
		try:
			yaml_data = db("SELECT name, value FROM metadata WHERE name = ?", key)[0][1]
		except IndexError:
			# Not a scenario, nothing to repair
			return
		try:
			YamlCache.load_yaml_data(yaml_data)
		except ParserError:
			messed_up = 'events: [ { actions: [ {'
			yaml_data = yaml_data.replace(messed_up, '}, ' + messed_up)
			db("UPDATE metadata SET value = ? WHERE name = ?", yaml_data, key)

	def _upgrade_to_rev74(self, db):
		db("INSERT INTO metadata VALUES (?, ?)", "selected_tab", None)
		
	def _upgrade_to_rev75(self, db):
		# some production line id changes

		# [(object id, old prod line id, new prod line id)]
		changes = [
			(68, 1842760585, 2105680898),
		]
		for obj_type, old_prod_line, new_prod_line in changes:
			for (obj, ) in db("SELECT rowid FROM building WHERE type = ?", obj_type):
				db("UPDATE production SET prod_line_id = ? WHERE owner = ? and prod_line_id = ?", new_prod_line, obj, old_prod_line)

	def _upgrade_to_rev76(self, db):
		#needed for commint: b0471afd48a0034150580e8fa00533f9ccae2a9b (Split unit production into ship & groundunit)
		old = 'NEW_UNIT'
		new = 'NEW_SHIP'
		db("UPDATE message_widget_active  SET id = ? WHERE id = ?", new, old)
		db("UPDATE message_widget_archive SET id = ? WHERE id = ?", new, old)


	def _upgrade(self):
		# fix import loop
		from horizons.savegamemanager import SavegameManager
		metadata = SavegameManager.get_metadata(self.original_path)
		rev = metadata['savegamerev']

		if rev < VERSION.SAVEGAMEREVISION :
			if not SavegameUpgrader.can_upgrade(rev):
				raise SavegameTooOld(revision=rev)
			
			self.log.warning('Discovered old savegame file, auto-upgrading: %s -> %s' % \
						     (rev, VERSION.SAVEGAMEREVISION))
			db = DbReader(self.final_path)
			db('BEGIN TRANSACTION')

			if rev < 49:
				self._upgrade_to_rev49(db)
			if rev < 50:
				self._upgrade_to_rev50(db)
			if rev < 51:
				self._upgrade_to_rev51(db)
			if rev < 52:
				self._upgrade_to_rev52(db)
			if rev < 53:
				self._upgrade_to_rev53(db)
			if rev < 54:
				self._upgrade_to_rev54(db)
			if rev < 55:
				self._upgrade_to_rev55(db)
			if rev < 56:
				self._upgrade_to_rev56(db)
			if rev < 57:
				self._upgrade_to_rev57(db)
			if rev < 58:
				self._upgrade_to_rev58(db)
			if rev < 59:
				self._upgrade_to_rev59(db)
			if rev < 60:
				self._upgrade_to_rev60(db)
			if rev < 61:
				self._upgrade_to_rev61(db)
			if rev < 62:
				self._upgrade_to_rev62(db)
			if rev < 63:
				self._upgrade_to_rev63(db)
			if rev < 64:
				self._upgrade_to_rev64(db)
			if rev < 65:
				self._upgrade_to_rev65(db)
			if rev < 66:
				self._upgrade_to_rev66(db)
			if rev < 67:
				self._upgrade_to_rev67(db)
			if rev < 68:
				self._upgrade_to_rev68(db)
			if rev < 69:
				self._upgrade_to_rev69(db)
			if rev < 70:
				self._upgrade_to_rev70(db)
			if rev < 71:
				self._upgrade_to_rev71(db)
			if rev < 72:
				self._upgrade_to_rev72(db)
			if 70 < rev < 73:
				self._upgrade_to_rev73(db)
			if rev < 74:
				self._upgrade_to_rev74(db)
			if rev < 75:
				self._upgrade_to_rev75(db)
			if rev < 76:
				self._upgrade_to_rev76(db)

			db('COMMIT')
			db.close()

	@classmethod
	def can_upgrade(cls, from_savegame_version):
		"""Checks whether a savegame can be upgraded from the current version"""
		if from_savegame_version >= VERSION.SAVEGAME_LEAST_UPGRADABLE_REVISION:
			return True
		else:
			return False

	def get_path(self):
		"""Return the path to the up-to-date version of the saved game."""
		if self.final_path is None:
			self.using_temp = True
			handle, self.final_path = tempfile.mkstemp(prefix='uh-savegame.' + os.path.basename(os.path.splitext(self.original_path)[0]) + '.', suffix='.sqlite')
			os.close(handle)
			shutil.copyfile(self.original_path, self.final_path)			
			self._upgrade()
		return self.final_path

	def close(self):
		if self.using_temp:
			self.using_temp = False
			os.unlink(self.final_path)
		self.final_path = None

decorators.bind_all(SavegameUpgrader)
