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

import random

from horizons.constants import PATHS
from horizons.util import decorators
from horizons.util.dbreader import DbReader
from horizons.gui.util import get_res_icon_path
from horizons.entities import Entities

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
		"""Returns the translated name for a specific resource id.
		@param id: int resource's id, of which the name is returned """
		name = self.cached_query("SELECT name FROM resource WHERE id = ?", id)[0][0]
		return _(name)

	def get_res_inventory_display(self, id):
		sql = "SELECT shown_in_inventory FROM resource WHERE id = ?"
		return self.cached_query(sql, id)[0][0]

	def get_res_value(self, id):
		"""Returns the resource's value
		@param id: resource id
		@return: float value"""
		return self.cached_query("SELECT value FROM resource WHERE id=?", id)[0][0]

	def get_res(self, only_tradeable=False, only_inventory=False):
		"""Returns a list of all resources.
		@param only_tradeable: return only those you can trade.
		@param only_inventory: return only those displayed in inventories.
		@return: list of resource ids"""
		sql = "SELECT id FROM resource WHERE id"
		if only_tradeable:
			sql += " AND tradeable = 1"
		if only_inventory:
			sql += " AND shown_in_inventory = 1"
		db_data = self.cached_query(sql)
		return map(lambda x: x[0], db_data)

	def get_res_id_and_icon(self, only_tradeable=False, only_inventory=False):
		"""Returns a list of all resources and the matching icon paths.
		@param only_tradeable: return only those you can trade.
		@param only_inventory: return only those displayed in inventories.
		@return: list of tuples: (resource ids, resource icon)"""
		sql = "SELECT id FROM resource WHERE id "
		if only_tradeable:
			sql += " AND tradeable = 1 "
		if only_inventory:
			sql += " AND shown_in_inventory = 1 "
		query = self.cached_query(sql)
		format_data = lambda res: (res, get_res_icon_path(res))
		return [format_data(row[0]) for row in query]

	# Sound table

	def get_sound_file(self, soundname):
		"""
		Returns the soundfile to the related sound name.
		@param sound: string, key in table sounds_special
		"""
		sql = 'SELECT file FROM sounds \
		       INNER JOIN sounds_special ON sounds.id = sounds_special.sound AND \
		       sounds_special.type = ?'
		return self.cached_query(sql, soundname)[0][0]

	# Building table

	def get_building_tooltip(self, building_class_id):
		"""Returns tooltip text of a building class.
		ATTENTION: This text is automatically translated when loaded
		already. DO NOT wrap the return value of this method in _()!
		@param building_class_id: class of building, int
		@return: string tooltip_text
		"""
		buildingtype = Entities.buildings[building_class_id]
		#xgettext:python-format
		tooltip = _("{building}: {description}")
		return tooltip.format(building=_(buildingtype._name),
		                      description=_(buildingtype.tooltip_text))

	@decorators.cachedmethod
	def get_related_building_ids(self, building_class_id):
		"""Returns list of building ids related to building_class_id.
		@param building_class_id: class of building, int
		@return list of building class ids
		"""
		sql = "SELECT related_building FROM related_buildings WHERE building = ?"
		return map(lambda x: x[0], self.cached_query(sql, building_class_id))

	@decorators.cachedmethod
	def get_related_building_ids_for_menu(self, building_class_id):
		"""Returns list of building ids related to building_class_id, which should
		be shown in the build_related menu.
		@param building_class_id: class of building, int
		@return list of building class ids
		"""
		sql = "SELECT related_building FROM related_buildings WHERE building = ? and show_in_menu = 1"
		return map(lambda x: x[0], self.cached_query(sql, building_class_id))

	@decorators.cachedmethod
	def get_inverse_related_building_ids(self, building_class_id):
		"""Inverse of the above, gives the lumberjack to the tree.
		@param building_class_id: class of building, int
		@return list of building class ids
		"""
		sql = "SELECT building FROM related_buildings WHERE related_building = ?"
		return map(lambda x: x[0], self.cached_query(sql, building_class_id))

	@decorators.cachedmethod
	def get_buildings_with_related_buildings(self):
		"""Returns all buildings that have related buildings"""
		sql = "SELECT DISTINCT building FROM related_buildings"
		return map(lambda x: x[0], self.cached_query(sql))

	# Messages

	def get_msg_visibility(self, msg_id_string):
		"""
		@param msg_id_string: string id of the message
		@return: int: for how long in seconds the message will stay visible
		"""
		sql = "SELECT visible_for FROM message WHERE id_string = ?"
		return self.cached_query(sql, msg_id_string)[0][0]

	def get_msg_text(self, msg_id_string):
		"""
		@param msg_id_string: string id of the message
		"""
		sql = "SELECT text FROM message_text WHERE id_string = ?"
		return self.cached_query(sql, msg_id_string)[0][0]

	def get_msg_icon_id(self, msg_id_string):
		"""
		@param msg_id_string: string id of the message
		@return: int: id
		"""
		sql = "SELECT icon FROM message where id_string = ?"
		return self.cached_query(sql, msg_id_string)[0][0]

	def get_msg_icons(self, msg_id_string):
		"""
		@param msg_id_string: string id of the message
		@return: tuple: (up, down, hover) images
		"""
		sql = "SELECT up_image, down_image, hover_image FROM message_icon WHERE icon_id = ?"
		return self.cached_query(sql, msg_id_string)[0]

	#
	#
	# Inhabitants
	#
	#

	def get_settler_name(self, level):
		"""Returns the name for a specific settler level
		@param level: int settler's level
		@return: string settler's level name"""
		sql = "SELECT name FROM settler_level WHERE level = ?"
		return self.cached_query(sql, level)[0][0]

	def get_settler_house_name(self, level):
		"""Returns name of the residential building for a specific increment
		@param level: int settler's level
		@return: string settler's housing name"""
		sql = "SELECT residential_name FROM settler_level WHERE level = ?"
		return self.cached_query(sql, level)[0][0]

	def get_settler_tax_income(self, level):
		sql = "SELECT tax_income FROM settler_level WHERE level=?"
		return self.cached_query(sql, level)[0][0]

	def get_settler_inhabitants_max(self, level):
		sql = "SELECT inhabitants_max FROM settler_level WHERE level=?"
		return self.cached_query(sql , level)[0][0]
	
	def get_settler_inhabitants_min(self, level):
		"""The minimum inhabitants before a setter levels down
		is the maximum inhabitants of the previous level."""
		if level == 0:
			return 0
		else: 
			sql = "SELECT inhabitants_max FROM settler_level WHERE level=?"
			return self.cached_query(sql, level-1)[0][0]

	def get_settler_happiness_increase_requirement(self):
		sql = "SELECT value FROM balance_values WHERE name='happiness_inhabitants_increase_requirement'"
		return self.cached_query(sql)[0][0]

	def get_settler_happiness_decrease_limit(self):
		sql = "SELECT value FROM balance_values WHERE name='happiness_inhabitants_decrease_limit'"
		return self.cached_query(sql)[0][0]

	# Misc

	def get_player_start_res(self):
		"""Returns resources, that players should get at startup as dict: { res : amount }"""
		start_res = self.cached_query("SELECT resource, amount FROM player_start_res")
		return dict(start_res)

	@decorators.cachedmethod
	def get_storage_building_capacity(self, storage_type):
		"""Returns the amount that a storage building can store of every resource.
		@param storage_type: building class id"""
		sql = "SELECT size FROM storage_building_capacity WHERE type = ?"
		return self.cached_query(sql, storage_type)[0][0]

	# Tile sets

	def get_random_tile_set(self, ground_id):
		"""Returns a tile set for a tile of type ground_id"""
		sql = "SELECT set_id FROM tile_set WHERE ground_id = ?"
		db_data = self.cached_query(sql, ground_id)
		return random.choice(db_data)[0] if db_data else None

	@decorators.cachedmethod
	def get_translucent_buildings(self):
		"""Returns building types that should become translucent on demand"""
		# use set because of quick contains check
		return frozenset( id for (id, b) in Entities.buildings.iteritems() if b.translucent )

	# Weapon table

	def get_weapon_stackable(self, weapon_id):
		"""Returns True if the weapon is stackable, False otherwise."""
		return self.cached_query("SELECT stackable FROM weapon WHERE id = ?", weapon_id)[0][0]

	def get_weapon_attack_radius(self, weapon_id):
		"""Returns weapon's attack radius modifier."""
		return self.cached_query("SELECT attack_radius FROM weapon WHERE id = ?", weapon_id)[0][0]


	# Units

	def get_unit_type_name(self, type_id):
		"""Returns the name of a unit type identified by its type"""
		return Entities.units[type_id].name


def read_savegame_template(db):
	savegame_template = open(PATHS.SAVEGAME_TEMPLATE, "r")
	db.execute_script( savegame_template.read() )

def read_island_template(db):
	savegame_template = open(PATHS.ISLAND_TEMPLATE, "r")
	db.execute_script( savegame_template.read() )
