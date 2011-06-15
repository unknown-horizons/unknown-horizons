# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.

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
from horizons.util.changelistener import metaChangeListenerDecorator

@metaChangeListenerDecorator("damage_dealt")
class HealthComponent(object):
	"""
	Class that handles the health component
	"""

	def __init__(self, instance):
		id = instance.id
		db = instance.session.db
		health = db.cached_query("SELECT max_health FROM health WHERE id = ?", id)[0][0]
		self.health = float(health)
		self.max_health = float(health)

	def deal_damage(self, weapon_id, damage):
		#TODO retrieve modifiers from database by owner_id/weapon_id
		#scaling factor multiplies the damage taken by the unit
		scaling_factor = 1
		self.health -= scaling_factor * damage
		self.on_damage_dealt()

	def save(self, db, worldid):
		db("INSERT INTO unit_health(owner_id, health) VALUES(?, ?)", worldid, self.health)

	def load(self, db, worldid):
		self.health = db("SELECT health FROM unit_health WHERE owner_id = ?", worldid)[0][0]
