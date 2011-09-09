# -*- coding: utf-8 -*-
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

import copy

import horizons.main

class ProductionLine(object):
	"""Data structure for handling production lines of Producers. A production line
	is a way of producing something (contains needed and produced resources for this line,
	as well as the time, that it takes to complete the product.

	Attributes: see _ProductionLineData.__init__
	"""
	# here we store templates for the prod_lines, since they are inited from db and therefore
	# on construction, every instance is the same. a reference instance (template) is created
	# and copied on demand.
	_data = {} # { id : ProductionLineInstance }

	def __init__(self, ident):
		self.__dict__ = copy.deepcopy( self.get_const_production_line(ident).__dict__ )

	@classmethod
	def get_const_production_line(cls, ident):
		"""Returns unchangeable production line data"""
		try:
			return cls._data[ident]
		except KeyError:
			cls._data[ident] = _ProductionLineData(ident)
			return cls._data[ident]

	@classmethod
	def reset(cls):
		cls._data.clear()

	def alter_production_time(self, modifier):
		"""Sets time to original production time multiplied by modifier"""
		self.time = self._data[self.id].time * modifier

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
		for t, res, amount in db("SELECT type, res, amount FROM production_line WHERE for_worldid = ?", for_worldid):
			if t == "TIME":
				self.time = res
			else:
				{ "NORMAL"   : self.production,
				  "CONSUMED" : self.consumed_res,
				  "PRODUCED" : self.produced_res,
				  "UNIT"     : self.unit_production }[t][res] = amount


	def __str__(self): # debug
		return 'ProductionLine(id=%s;prod=%s)' % (self.id, self.production)


class _ProductionLineData(object):
	"""Actually saves the data under the hood. Internal Use Only!"""
	def __init__(self, ident):
		"""Inits self from db and registers itself as template"""
		self._init_finished = False
		self.id = ident
		db_data = horizons.main.db("SELECT time, changes_animation, save_statistics FROM production_line WHERE id = ?", self.id)[0]
		self.time = float(db_data[0]) # time in seconds that production takes
		self.changes_animation = bool(db_data[1]) # whether this prodline influences animation
		self.save_statistics = bool(db_data[2]) # whether statistics about this production line should be kept
		# here we store all resource information.
		# needed resources have a negative amount, produced ones are positive.
		self.production = {}
		self.produced_res = {} # contains only produced
		self.consumed_res = {} # contains only consumed
		for res, amount in horizons.main.db("SELECT resource, amount FROM production WHERE production_line = ?", self.id):
			self.production[res] = amount
			if amount > 0:
				self.produced_res[res] = amount
			elif amount < 0:
				self.consumed_res[res] = amount
			else:
				assert False
		# Stores unit_id: amount entries, if units are to be produced by this production line
		self.unit_production = {}
		for unit, amount in horizons.main.db("SELECT unit, amount FROM unit_production WHERE production_line = ?", self.id):
			self.unit_production[int(unit)] = amount # Store the correct unit id =>  -1.000.000

		self._init_finished = True

	def __setattr__(self, name, value):
		if hasattr(self, "_init_finished") and self._init_finished:
			raise TypeError, 'ProductionLineData is const, use ProductionLine'
		else:
			self.__dict__[name] = value

	def __str__(self):
		return "ProductionLineData(lineid=%s)" % self.id
