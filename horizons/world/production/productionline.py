# -*- coding: utf-8 -*-
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

from horizons.constants import UNITS

class ProductionLine(object):
	"""Class that collects the production line data."""

	def __init__(self, id, data):
		"""Inits self from yaml data"""
		self.__data = data or {}
		self.id = id
		self.__init()

	def __init(self):
		self._init_finished = False
		# time in seconds that production takes:
		self.time = self.__data.get('time', 1)
		# whether this prodline influences animation:
		self.changes_animation = self.__data.get('changes_animation', True)
		# whether statistics about this production line should be kept:
		self.save_statistics = self.__data.get('save_statistics', True)

		# here we store all resource information.
		# needed resources have a negative amount, produced ones are positive.
		self.production = {}
		self.produced_res = {} # contains only produced
		self.consumed_res = {} # contains only consumed
		self.unit_production = {} # Stores unit_id: amount entries, if units are to be produced
		if 'produces' in self.__data:
			for produced_object, amount in self.__data['produces']:
				if produced_object < UNITS.DIFFERENCE_BUILDING_UNIT_ID:
					self.production[produced_object] = amount
					self.produced_res[produced_object] = amount
				else:
					self.unit_production[produced_object] = amount
		if 'consumes' in self.__data:
			for res, amount in self.__data['consumes']:
				self.production[res] = amount
				self.consumed_res[res] = amount

		self._init_finished = True

	def __str__(self):
		return "ProductionLineData(lineid=%s)" % self.id

	def alter_production_time(self, modifier):
		"""Sets time to original production time multiplied by modifier"""
		self.time = self.__data.get('time', 1) * modifier

	def change_amount(self, res, amount):
		"""Alters an amount of a res at runtime. Because of redundancy, you can only change
		amounts here."""
		self.production[res] = amount
		if res in self.consumed_res:
			self.consumed_res[res] = amount
		if res in self.produced_res:
			self.produced_res[res] = amount

	def save(self, db, for_worldid):
		# we don't have a worldid, we load it for another world id
		for res, amount in self.production.iteritems():
			db("INSERT INTO production_line(for_worldid, type, res, amount) VALUES(?, ?, ?, ?)",
			   for_worldid, "NORMAL", res, amount)
		for res, amount in self.consumed_res.iteritems():
			db("INSERT INTO production_line(for_worldid, type, res, amount) VALUES(?, ?, ?, ?)",
			   for_worldid, "CONSUMED", res, amount)
		for res, amount in self.produced_res.iteritems():
			db("INSERT INTO production_line(for_worldid, type, res, amount) VALUES(?, ?, ?, ?)",
			   for_worldid, "PRODUCED", res, amount)
		for unit, amount in self.unit_production.iteritems():
			db("INSERT INTO production_line(for_worldid, type, res, amount) VALUES(?, ?, ?, ?)",
			   for_worldid, "UNIT", unit, amount)

		db("INSERT INTO production_line(for_worldid, type, res, amount) VALUES(?, ?, ?, ?)",
			   for_worldid, "TIME", self.time, None)


	def load(self, db, for_worldid):
		# we don't have a worldid, we load it for another world id
		self.production = {}
		self.consumed_res = {}
		self.produced_res = {}
		self.unit_production = {}
		for t, res, amount in db.get_production_line_row(for_worldid):
			if t == "TIME":
				self.time = res
			else:
				{ "NORMAL"   : self.production,
				  "CONSUMED" : self.consumed_res,
				  "PRODUCED" : self.produced_res,
				  "UNIT"     : self.unit_production }[t][res] = amount


	def get_original_copy(self):
		"""Returns a copy of this production, in its original state, no changes
		applied"""
		return ProductionLine(self.id, self.__data)
