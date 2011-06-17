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

from random import randint

from dbreader import DbReader

from horizons.util import decorators

########################################################################
class UhDbAccessor(DbReader):
	"""UhDbAccessor is the class that contains the sql code. It is meant
	to keep all the sql code in a central place, to make it reusable and
	maintainable.

	It should be used as a utility to remove data access code from places where
	it doesn't belong, such as game logic.

	Due to historic reasons, sql code is spread over the game code; for now, it is left at
	places, that are data access routines (e.g. unit/building class)."""

	def __init__(self, dbfile):
		super(UhDbAccessor, self).__init__(dbfile=dbfile)


	# ------------------------------------------------------------------
	# Db Access Functions start here
	# ------------------------------------------------------------------

	# Resource table

	def get_res_name(self, id, only_if_tradeable=False, only_if_inventory=False):
		"""
		Returns the name to a specific resource id.
		@param id: int resource's id, of which the name is returned
		"""
		sql = "SELECT name FROM resource WHERE id = ?"
		if not (only_if_tradeable or only_if_inventory):
			return self.cached_query(sql, id)[0][0]
		if only_if_tradeable:
			sql += " AND tradeable = 1"
		if only_if_inventory:
			sql += " AND shown_in_inventory = 1"
		try:
			return self.cached_query(sql, id)[0][0]
		except IndexError:
			return None

	def get_res_icon(self, res):
		"""Returns icons of a resource
		@param res: resource id
		@return: tuple: (icon_path, icon_disabled_path, icon_small_path)"""
		return self.cached_query('SELECT icon, \
			    CASE WHEN (icon_disabled is null) THEN icon ELSE icon_disabled END, \
			    CASE WHEN (icon_small is null) THEN icon ELSE icon_small END \
			    FROM data.resource WHERE id = ?', res)[0]

	def get_res_value(self, id):
		"""Returns the resource's value
		@param id: resource id
		@return: float value"""
		return self.cached_query("SELECT value FROM resource WHERE id=?", id)[0][0]

	def get_res(self, only_tradeable=False):
		"""Returns a list of all resources.
		@param only_tradeable: return only those you can trade.
		@return: list of resource ids"""
		sql = "SELECT id FROM resource "
		if only_tradeable:
			sql += " WHERE tradeable = 1"
		db_data = self.cached_query(sql)
		return map(lambda x: x[0], db_data)

	def get_res_id_and_icon(self, only_tradeable=False):
		"""Returns a list of all resources and the matching icons.
		@param only_tradeable: return only those you can trade.
		@return: list of tuples: (resource ids, resource icon)"""
		sql = "SELECT id, icon FROM resource "
		if only_tradeable:
			sql += " WHERE tradeable = 1"
		return self.cached_query(sql)

	# Sound table

	def get_sound_file(self, soundname):
		"""
		Returns the soundfile to the related sound name.
		@param sound: string, key in table sounds_special
		"""
		return self.cached_query("SELECT file FROM sounds INNER JOIN sounds_special ON \
			    sounds.id = sounds_special.sound AND sounds_special.type = ?", soundname)[0][0]


	def get_random_action_set(self, object_id, level=0, exact_level=False):
		"""Returns an action set for an object of type object_id in a level <= the specified level.
		The highest level number is preferred.
		@param db: UhDbAccessor
		@param object_id: type id of building
		@param level: level to prefer. a lower level might be chosen
		@param exact_level: choose only action sets from this level. return val might be None here.
		@return: tuple: (action_set_id, preview_action_set_id)"""
		assert level >= 0
		sql = "SELECT action_set_id, preview_action_set_id FROM action_set \
		      WHERE object_id = ? and level = ?"

		if exact_level:
			db_data = self.cached_query(sql, object_id, level)
			if db_data:
				return db_data[ randint(0, len(db_data)-1) ]
			else:
				return None

		else: # search all levels for an action set, starting with highest one
			for possible_level in reversed(xrange(level+1)):
				db_data = self.cached_query(sql, object_id, possible_level)
				if db_data: # break if we found sth in this lvl
					return db_data[ randint(0, len(db_data)-1) ]
			assert False, "Couldn't find action set for obj %s in lvl %s" % (object_id, level)


	# Building table

	def get_building_class_data(self, building_class_id):
		"""Returns data for class of a building class.
		@param building_class_id: class of building, int
		@return: tuple: (class_package, class_name)"""
		sql = "SELECT class_package, class_type FROM data.building WHERE id = ?"
		return self.cached_query(sql, building_class_id)[0]


	def get_building_id_buttonname_settlerlvl(self):
		"""Returns a list of id, button_name and settler_level"""
		return self.cached_query("SELECT id, button_name, settler_level FROM \
		                          building WHERE button_name IS NOT NULL")

	#
	#
	# Settler DATABASE
	#
	#

	# production_line table

	def get_settler_production_lines(self, level):
		"""Returns a list of settler's production lines for a specific level
		@param level: int level for which to return the production lines
		@return: list of production lines"""
		return self.cached_query("SELECT production_line \
		                          FROM settler.settler_production_line \
		                          WHERE level = ?", level)

	def get_settler_name(self, level):
		"""Returns the name for a specific settler level
		@param level: int settler's level
		@return: string settler's level name"""
		return self.cached_query("SELECT name FROM settler_level WHERE level = ?",
		                         level)[0][0]

	def get_settler_house_name(self, level):
		"""Returns name of the residential building for a specific increment
		@param level: int settler's level
		@return: string settler's housing name"""
		return self.cached_query("SELECT residential_name FROM settler_level \
		                          WHERE level = ?", level)[0][0]

	def get_settler_tax_income(self, level):
		return self.cached_query("SELECT tax_income FROM settler.settler_level \
		                          WHERE level=?", level)[0][0]

	def get_settler_inhabitants_max(self, level):
		return self.cached_query("SELECT inhabitants_max FROM settler.settler_level \
		                          WHERE level=?", level)[0][0]

	def get_settler_inhabitants(self, building_id):
		return self.cached_query("SELECT inhabitants FROM settler WHERE rowid=?",
		                         building_id)[0][0]

	def get_settler_upgrade_material_prodline(self, level):
		db_result = self.cached_query("SELECT production_line FROM upgrade_material \
		                          WHERE level = ?", level)
		return db_result[0][0] if db_result else None

	@decorators.cachedmethod
	def get_provided_resources(self, object_class):
		"""Returns resources that are provided by a building- or unitclass as set"""
		db_data = self("SELECT resource FROM balance.production WHERE amount > 0 AND \
		production_line IN (SELECT id FROM production_line WHERE object_id = ? )", object_class)
		return set(map(lambda x: x[0], db_data))


	# Misc

	def get_player_start_res(self):
		"""Returns resources, that players should get at startup as dict: { res : amount }"""
		ret = {}
		for res, amount in self.cached_query("SELECT resource, amount FROM player_start_res"):
			ret[res] = amount
		return ret

	@decorators.cachedmethod
	def get_storage_building_capacity(self, storage_type):
		"""Returns the amount that a storage building can store of every resource."""
		return self("SELECT size FROM storage_building_capacity WHERE type = ?", storage_type)[0][0]
