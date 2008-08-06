# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

from provider import Provider
from consumer import Consumer
from game.world.units.unit import Unit
import game.main
from game.util import WeakList
from game.gui.tabwidget import TabWidget

class PrimaryProducer(Provider):
	"""Class used for production buildings"""
	def __init__(self, **kwargs):
		"""
		"""
		super(PrimaryProducer, self).__init__(**kwargs)
		# infos about production
		self.production = {}

		# Init production lines
		for (id,) in game.main.db("SELECT rowid FROM data.production_line where %(type)s = ?" % {'type' : 'building' if self.object_type == 0 else 'unit'}, self.id):
			self.production[id] = ProductionLine(id)

		self.active_production_line = None if len(self.production) == 0 else min(self.production.keys())

		self.__used_resources = {}

		if self.active_production_line is not None:
			self.addChangeListener(self.check_production_startable)
			self.check_production_startable()

	def check_production_startable(self):
		for res, amount in self.production[self.active_production_line].production.items():
			if amount > 0 and self.inventory.get_value(res) + amount > self.inventory.get_size(res):
				return
		usable_resources = {}
		if min(self.production[self.active_production_line].production.values()) < 0:
			for res, amount in self.production[self.active_production_line].production.items():
				#we have something to work with, if the res is needed, we have something in the inv and we dont already have used everything we need from that resource
				if amount < 0 and self.inventory.get_value(res) > 0 and self.__used_resources.get(res, 0) < -amount:
					usable_resources[res] = -amount - self.__used_resources.get(res, 0)
			if len(usable_resources) == 0:
				return
			time = int(round(self.production[self.active_production_line].time * sum(self.__used_resources.values()) / -sum(p for p in self.production[self.active_production_line].production.values() if p < 0)))
		else:
			time = 0
		self.removeChangeListener(self.check_production_startable)
		for res, amount in usable_resources.items():
			if res in self.__used_resources:
				self.__used_resources[res] += amount
			else:
				self.__used_resources[res] = amount
		for res, amount in usable_resources.items():
			assert(self.inventory.alter_inventory(res, -amount) == 0)
		game.main.session.scheduler.add_new_object(self.production_step, self, 16 *
		(self.production[self.active_production_line].time if min(self.production[self.active_production_line].production.values()) >= 0
		else (int(round(self.production[self.active_production_line].time * sum(self.__used_resources.values()) / -sum(p for p in self.production[self.active_production_line].production.values() if p < 0))
				) - time)))
		self._instance.act("working", self._instance.getFacingLocation(), True)
		#print self.getId(), "begin working"

	def production_step(self):
		#print self.getId(), "production_step"
		if sum(self.__used_resources.values()) >= -sum(p for p in self.production[self.active_production_line].production.values() if p < 0):
			for res, amount in self.production[self.active_production_line].production.items():
				if amount > 0:
					self.inventory.alter_inventory(res, amount)
			self.__used_resources = {}
		self._instance.act("default", self._instance.getFacingLocation(), True)
		self.addChangeListener(self.check_production_startable)
		self.check_production_startable()

	def save(self, db):
		super(PrimaryProducer, self).save(db)
		db("INSERT INTO producer (rowid, active_production_line) VALUES(?,?)", self.getId(), self.active_production_line)

		
class SecondaryProducer(Consumer, PrimaryProducer):
	"""Represents a producer, that consumes ressources for production of other ressources (e.g. blacksmith)"""

	def show_menu(self):
		game.main.session.ingame_gui.show_menu(TabWidget(2, self))
		

class ProductionLine(object):
	def __init__(self, id):
		self.id = id
		self.time = game.main.db("SELECT time FROM data.production_line WHERE rowid = ?", self.id)[0][0]
		self.production = {}
		for res, amount in game.main.db("SELECT resource, amount FROM data.production WHERE production_line = ?", self.id):
			self.production[res] = amount
