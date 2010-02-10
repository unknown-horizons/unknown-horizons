# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

from dbreader import DbReader
from random import randint

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

	def get_res_name(self, id):
		"""
		Returns the name to a specific resource id.
		@param id: int resource's id, of which the name is returned
		"""
		return self.cached_query("SELECT name FROM resource WHERE id = ?", id)[0][0]

	def get_res_icon(self, id):
		"""Returns icons of a resource
		@param id: resource id
		@return: tuple: (icon_path, icon_disabled_path)"""
		return self.cached_query('SELECT icon, \
			    CASE WHEN (icon_disabled is null) THEN icon ELSE icon_disabled END \
			    FROM data.resource WHERE id = ?', res)[0]

	def get_res(self, only_tradeable=False):
		"""Returns a list of all resources.
		@param only_tradeable: return only those you can trade.
		@return: list of resource ids"""
		sql = "SELECT id FROM resource "
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
			db_data = self(sql, object_id, level)
			if db_data:
				return db_data[0]
			else:
				return None

		else: # search all levels for an action set, starting with highest one
			for possible_level in reversed(xrange(level+1)):
				db_data = self(sql, object_id, possible_level)
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
