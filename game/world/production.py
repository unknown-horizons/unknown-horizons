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

class PrimaryProducer(Provider):
	check_production_interval = 2
	# run self.tick every second tick (NOTE: this should be discussed)
	# running every tick currently requires all production times to be
	# a multiple of 2
	"""Class used for production buildings"""
	def __init__(self, **kwargs):
		"""
		"""
		super(PrimaryProducer, self).__init__(**kwargs)
		# infos about production
		self.production = {}

		# Init production lines
		result = game.main.db("SELECT rowid FROM production_line where %(type)s = ?" % {'type' : 'building' if self.object_type == 0 else 'unit'}, self.id)
		for id in result:
			self.production[id] = ProductionLine(id)


		if len(self.production) == 0:
			self.active_production_line = -1
		else:
			self.active_production_line = min(self.production.keys())

		self._current_production = 0

		game.main.session.scheduler.add_new_object(self.tick, self, self.__class__.check_production_interval, -1)

	def tick(self):
		"""Called by the ticker, to produce goods.
		"""
		# check if production is disabled
		if self.active_production_line == -1:
			return

		# check if building is in storage mode or is a storage
		if self.production[self.active_production_line].time == 0:
			return

		self._current_production += self.__class__.check_production_interval
		if self._current_production % self.production[self.active_production_line].time == 0:
			# time to produce res
			for res in self.production[self.active_production_line].production.items():
				# res[0]: resource; res[1]: amount
				
				# check for needed resources
				if res[1] < 0:
					if self.inventory.get_value(res[0]) + res[1] < 0:
						# missing res res[0]
						#print 'PROD', self.id,'missing', res[0]
						return

				# check for storage capacity
				else:
					if self.inventory.get_value(res[0]) == self.inventory.get_size(res[0]):
						# no space for res[0]
						#print 'PROD', self.id,'no space for', res[0]
						return

			# everything ok, actual production:
			for res in self.production[self.active_production_line].production.items():
				print self.id, "PRODUCE" 'res', res[0], 'amount', res[1]
				self.inventory.alter_inventory(res[0], res[1])
				print self.id, "PRODUCE : inventory = ", self.inventory

class SecondaryProducer(Consumer, PrimaryProducer):
	"""Represents a producer, that consumes ressources for production of other ressources (e.g. blacksmith)"""

	def show_menu(self):
		game.main.session.ingame_gui.show_menu(TabWidget(2, self))

class ProductionLine(object):
	def __init__(self, id):
		self.id = id
		self.time = game.main.db("SELECT time FROM production_line WHERE rowid == ?", self.id)
		self.active = False
		self.production = game.main.db("SELECT resource, amount FROM production WHERE production_line = ?);", self.id)