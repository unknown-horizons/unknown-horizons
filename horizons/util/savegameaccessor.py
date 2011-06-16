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

from horizons.util import DbReader

########################################################################
class SavegameAccessor(DbReader):
	"""SavegameAccessor is the class used for loading saved games.
	Frequent select queries are preloaded for faster access."""

	def __init__(self, dbfile):
		super(SavegameAccessor, self).__init__(dbfile=dbfile)
		self._load_building()
		self._load_settlement()
		self._load_concrete_object()
		self._load_production()
		self._load_storage()
		self._load_storage_slot_limit()
		self._load_wildanimal()
		self._load_unit()
		self._load_building_collector()


	def _load_building(self):
		self._building = {}
		for row in self("SELECT rowid, x, y, location, rotation, level FROM building"):
			self._building[int(row[0])] = row[1:]
	
	def get_building_row(self, worldid):
		"""Returns (x, y, location, rotation, level)"""
		return self._building[int(worldid)]

	def get_building_location(self, worldid):
		return self._building[int(worldid)][3]


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
		self._production = {}
		self._production_ids = {}
		for row in self("SELECT rowid, state, owner, prod_line_id, remaining_ticks, _pause_old_state FROM production"):
			rowid = int(row[0])
			self._production[rowid] = row[1:]
			owner = int(row[2])
			if owner in self._production_ids:
				self._production_ids[owner].append(rowid)
			else:
				self._production_ids[owner] = [rowid]

	def get_production_row(self, worldid):
		"""Returns (state, owner, prod_line_id, remaining_ticks, _pause_old_state)"""
		return self._production[int(worldid)]

	def get_production_ids_by_owner(self, ownerid):
		"""Returns potentially empty list of worldids referencing productions"""
		ownerid = int(ownerid)
		return [] if ownerid not in self._production_ids else self._production_ids[ownerid]


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
		for row in self("SELECT rowid, home_building FROM building_collector"):
			self._building_collector[int(row[0])] = int(row[1])

	def get_building_collectors_home(self, worldid):
		"""Returns the id of the building collector's home or None otherwise"""
		worldid = int(worldid)
		return None if worldid not in self._building_collector else self._building_collector[worldid]
