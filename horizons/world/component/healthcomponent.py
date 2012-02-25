# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
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

import logging

from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.world.component import Component

@metaChangeListenerDecorator("damage_dealt")
class HealthComponent(Component):
	"""
	Class that handles the health component
	"""
	log = logging.getLogger("component.health")

	# Store the name of this component
	NAME = 'health'

	def __init__(self, maxhealth):
		super(HealthComponent, self).__init__()
		assert maxhealth is not None, "Can not add HealthComponent without maxhealth!"
		self.max_health = float(maxhealth) if maxhealth is not None else None

	def initialize(self):
		self.health = float(self.max_health)
		self._add_listeners()

	def _add_listeners(self):
		self.add_damage_dealt_listener(self.check_if_alive)
		self.add_damage_dealt_listener(self.redraw_health)

	def save(self, db):
		db("INSERT INTO unit_health(owner_id, health) VALUES(?, ?)", self.instance.worldid, self.health)

	def load(self, db, worldid):
		self.health = db.get_health(worldid)
		self._add_listeners()

	def deal_damage(self, weapon_id, damage):
		#TODO retrieve modifiers from database by owner_id/weapon_id
		#scaling factor multiplies the damage taken by the unit
		scaling_factor = 1
		self.health -= scaling_factor * damage
		self.health = max(self.health, 0.0) # don't go below 0
		self.log.debug("dealing damage %s to %s; new health: %s", scaling_factor*damage, self.instance, self.health)
		self.on_damage_dealt()

	def check_if_alive(self, caller = None):
		if self.health <= 0:
			self.log.debug("Unit %s dies, health: %s", self.instance, self.health)
			self.instance.remove()

	def redraw_health(self, caller = None):
		if not self.instance:
			return
		if self.instance in self.session.selected_instances:
			if hasattr(self.instance, 'draw_health'):
				self.instance.draw_health()

