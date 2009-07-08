# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

from secondaryproduction import SecondaryProduction
from horizons.world.building.building import Building
import horizons.main

class UnitProduction(SecondaryProduction):

	log = logging.getLogger("world.unitproducer")

	def __init__(self, **kwargs):
		super(UnitProduction, self).__init__(**kwargs)
		self.output_point = None
		# _init is autocalled by the primary producer

	def _init(self):
		# production_queue holds the ids of the production_lines
		# currently waiting for construction.
		self.production_queue = []
		self.progress = 0

		self._PrimaryProduction__used_resources = {}
		# Load production lines
		self.production = {}
		for (id,) in horizons.main.db("SELECT rowid FROM data.production_line where %(type)s = ?"\
								  % {'type' : 'building' if self.object_type == 0 else 'unit'}, self.id):
			self.production[id] = UnitProductionLine(id)

		# Set production line to None, we don't produce automatically
		self.active_production_line = None
		self.active = False

		if isinstance(self, Building):
			self.toggle_costs()  # needed to get toggle to the right position


	def toggle_active(self):
		if len(self.production_queue) > 0 or self.active_production_line is not None:
			super(UnitProduction, self).toggle_active()

	def production_step(self):
		self.log.debug("UnitProduction production_step %s", self.getId())
		if sum(self._PrimaryProduction__used_resources.values()) >= -sum(p for p in self.production[self.active_production_line].production.values() if p < 0):
			for res, amount in self.production[self.active_production_line].production.items():
				if amount > 0:
					self.inventory.alter(res, amount)
			self._PrimaryProduction__used_resources = {}
			# ONLY DIFFERENCE TO PRIMARY PRODUCER HERE
			self.create_unit()
		if "idle_full" in horizons.main.action_sets[self._action_set_id].keys():
			self.act("idle_full", self._instance.getFacingLocation(), True)
		else:
			self.act("idle", self._instance.getFacingLocation(), True)

		if len(self.production_queue) > 0:
			# Start producing the next item in our production queue
			self.active_production_line = self.production_queue.pop()
			self.addChangeListener(self.check_production_startable)
			self.check_production_startable()
		else:
			# No more units in the queue, go inactive
			self.active_production_line = None
			self.toggle_active()

	def create_unit(self):
		"""Creates the specified unit at the buildings output point."""
		self.log.debug("CREATING UNIT! %s", id)
		if self.output_point is None:
			for point in self.position.get_radius_coordinates(3):
				if point in horizons.main.session.world.water:
					self.output_point = point
					break

		# Create the new units at the output_point
		for unit in self.production[self.active_production_line].unit.values():
			horizons.main.session.entities.units[unit](x=self.output_point[0], y=self.output_point[1], owner=self.owner)
		self.progress = 0


	def produce(self, prod_line):
		"""Called to start the UnitProduction's unit creation process.
		This should be used to start a production after the user has specified it.\n
		@param prod_line: id of the production line that is to be used.
		"""
		assert prod_line in self.production.keys(), "ERROR: You specified an invalid production line!"
		if self.active:
			#Enqueue the new production, we are still producing.
			self.production_queue.append(prod_line)
		else:
			# Start production
			self.active_production_line = prod_line
			self.toggle_active()

class UnitProductionLine(object):

	def __init__(self, id):
		super(UnitProductionLine, self).__init__()
		self.id = id
		self.time = horizons.main.db("SELECT time FROM data.production_line WHERE rowid=?", id)[0][0]
		self.production = {}
		self.unit = {}
		for unit_id, amount in \
			horizons.main.db("SELECT unit, amount FROM data.unit_production WHERE production_line=?", id):
			self.unit[unit_id] = amount
		for res, amount in \
			horizons.main.db("SELECT resource, amount FROM data.production WHERE production_line=?", id):
			self.production[res] = amount
