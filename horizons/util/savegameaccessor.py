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

import hashlib
import os.path
from collections import defaultdict, deque

from horizons.util.savegameupgrader import SavegameUpgrader
from horizons.util.python import decorators
from horizons.util import DbReader

class SavegameAccessor(DbReader):
	"""
	SavegameAccessor is the class used for loading saved games.

	Frequent select queries are preloaded for faster access.
	"""

	def __init__(self, dbfile):
		self.upgrader = SavegameUpgrader(dbfile)
		super(SavegameAccessor, self).__init__(dbfile=self.upgrader.get_path())
		self._load_building()
		self._load_settlement()
		self._load_concrete_object()
		self._load_production()
		self._load_storage()
		self._load_storage_slot_limit()
		self._load_wildanimal()
		self._load_unit()
		self._load_building_collector()
		self._load_production_line()
		self._load_unit_path()
		self._load_component()
		self._load_storage_global_limit()
		self._load_health()
		self._hash = None

	def close(self):
		super(SavegameAccessor, self).close()
		self.upgrader.close()


	def _load_building(self):
		self._building = {}
		for row in self("SELECT rowid, x, y, location, rotation, level FROM building"):
			self._building[int(row[0])] = row[1:]

	def get_building_row(self, worldid):
		"""Returns (x, y, location, rotation, level)"""
		return self._building[int(worldid)]

	def get_building_location(self, worldid):
		return self._building[int(worldid)][2]


	def _load_settlement(self):
		self._settlement = {}
		for row in self("SELECT rowid, owner, island FROM settlement"):
			self._settlement[int(row[0])] = row[1:]

	def get_settlement_owner(self, worldid):
		"""Returns the id of the owner of the settlement or None otherwise"""
		worldid = int(worldid)
		return None if worldid not in self._settlement else self._settlement[worldid][0]

	def get_settlement_island(self, worldid):
		return self._settlement[int(worldid)][1]


	def _load_concrete_object(self):
		self._concrete_object = {}
		for row in self("SELECT id, action_runtime FROM concrete_object"):
			self._concrete_object[int(row[0])] = int(row[1])

	def get_concrete_object_action_runtime(self, worldid):
		return self._concrete_object[int(worldid)]


	def _load_production(self):
		self._productions_by_worldid = {}
		self._production_lines_by_owner = {}
		self._productions_by_id_and_owner = {}
		db_data = self("SELECT rowid, state, owner, prod_line_id, remaining_ticks, _pause_old_state, creation_tick FROM production")
		for row in db_data:
			rowid = int(row[0])
			data = row[1:]
			self._productions_by_worldid[rowid] = data
			owner = int(row[2])
			line = int(row[3])
			if not line in self._productions_by_id_and_owner:
				self._productions_by_id_and_owner[line] = {}
			# in the line dict, the owners are unique
			self._productions_by_id_and_owner[line][owner] = data

			if owner not in self._production_lines_by_owner:
				self._production_lines_by_owner[owner] = [line]
			else:
				self._production_lines_by_owner[owner].append(line)

			self._production_lines_by_owner[owner].append

		self._production_state_history = defaultdict(lambda: deque())
		for production_id, tick, state in self("SELECT production, tick, state FROM production_state_history ORDER BY production, tick"):
			self._production_state_history[int(production_id)].append((tick, state))

	def get_production_by_id_and_owner(self, id, ownerid):
		# owner means worldid of entity
		return self._productions_by_id_and_owner[id][ownerid]

	def get_production_line_id(self, production_worldid):
		"""Returns the prod_line_id of the given production"""
		return self._productions_by_worldid[int(production_worldid)][2]

	def get_production_lines_by_owner(self, owner):
		"""Returns the prod_line_id of the given production"""
		return self._production_lines_by_owner.get(owner, [])

	def get_production_state_history(self, worldid):
		return self._production_state_history[int(worldid)]


	def _load_storage(self):
		self._storage = {}
		for row in self("SELECT object, resource, amount FROM storage"):
			ownerid = int(row[0])
			if ownerid in self._storage:
				self._storage[ownerid].append(row[1:])
			else:
				self._storage[ownerid] = [row[1:]]

	def get_storage_rowids_by_ownerid(self, ownerid):
		"""Returns potentially empty list of worldids referencing storages"""
		ownerid = int(ownerid)
		return [] if ownerid not in self._storage else self._storage[ownerid]


	def _load_storage_slot_limit(self):
		self._storage_slot_limit = {}
		for row in self("SELECT object, slot, value FROM storage_slot_limit"):
			key = (int(row[0]), int(row[1]))
			self._storage_slot_limit[key] = int(row[2])

	def get_storage_slot_limit(self, ownerid, slot):
		return self._storage_slot_limit[(int(ownerid), int(slot))]


	def _load_wildanimal(self):
		self._wildanimal = {}
		for row in self("SELECT rowid, health, can_reproduce FROM wildanimal"):
			self._wildanimal[int(row[0])] = row[1:]

	def get_wildanimal_row(self, worldid):
		"""Returns (health, can_reproduce)"""
		return self._wildanimal[int(worldid)]


	def _load_unit(self):
		self._unit = {}
		for row in self("SELECT rowid, owner FROM unit"):
			self._unit[int(row[0])] = int(row[1])

	def get_unit_owner(self, worldid):
		return self._unit[int(worldid)]


	def _load_building_collector(self):
		self._building_collector = {}
		for row in self("SELECT rowid, home_building, creation_tick FROM building_collector"):
			self._building_collector[int(row[0])] = (int(row[1]) if row[1] is not None else None, row[2])

		self._building_collector_job_history = defaultdict(lambda: deque())
		for collector_id, tick, utilisation in self("SELECT collector, tick, utilisation FROM building_collector_job_history ORDER BY collector, tick"):
			self._building_collector_job_history[int(collector_id)].append((tick, utilisation))

	def get_building_collectors_data(self, worldid):
		"""Returns (id of the building collector's home or None otherwise, creation_tick)"""
		worldid = int(worldid)
		return None if worldid not in self._building_collector else self._building_collector[worldid]

	def get_building_collector_job_history(self, worldid):
		return self._building_collector_job_history[int(worldid)]


	def _load_production_line(self):
		self._production_line = {}
		for row in self("SELECT for_worldid, type, res, amount FROM production_line"):
			id = int(row[0])
			if id not in self._production_line:
				self._production_line[id] = []
			self._production_line[id].append(row[1:])

	def get_production_line_row(self, for_worldid):
		return self._production_line[int(for_worldid)]


	def _load_unit_path(self):
		self._unit_path = {}
		for row in self("SELECT unit, x, y FROM unit_path ORDER BY 'index'"):
			id = int(row[0])
			if id not in self._unit_path:
				self._unit_path[id] = []
			self._unit_path[id].append(row[1:])

	def get_unit_path(self, worldid):
		worldid = int(worldid)
		return self._unit_path[worldid] if worldid in self._unit_path else None


	def _load_component(self):
		self._component = {}
		for row in self("SELECT worldid, name, module, class FROM component"):
			id = int(row[0])
			if id not in self._component:
				self._component[id] = []
			self._component[id].append(row[1:])

	def get_component_row(self, worldid):
		worldid = int(worldid)
		return self._component[worldid] if worldid in self._component else []


	def _load_storage_global_limit(self):
		self._storage_global_limit = {}
		for row in self("SELECT object, value FROM storage_global_limit"):
			self._storage_global_limit[(int(row[0]))] = int(row[1])

	def get_storage_global_limit(self, worldid):
		return self._storage_global_limit[int(worldid)]


	def _load_health(self):
		self._health = dict( self("SELECT owner_id, health FROM unit_health") )

	def get_health(self, owner):
		return self._health[owner]

	# Random savegamefile related utility that i didn't know where to put

	@classmethod
	def get_players_num(cls, savegamefile):
		"""Return number of regular human and ai players"""
		return DbReader(savegamefile)("SELECT count(rowid) FROM player WHERE is_trader = 0 AND is_pirate = 0")[0][0]

	@classmethod
	def get_hash(cls, savegamefile):
		if not os.path.exists(savegamefile):
			return False
		fd = open(savegamefile, "rb")
		h = hashlib.sha1()
		h.update(fd.read())
		filehash = h.hexdigest()
		fd.close();
		return filehash

decorators.bind_all(SavegameAccessor)
