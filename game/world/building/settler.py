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

from building import Building, Selectable
from game.world.production import SecondaryProducer
from game.gui.tabwidget import TabWidget
import game.main
from buildable import BuildableSingle

class Settler(SecondaryProducer, BuildableSingle, Selectable, Building):
	"""Represents a settlers house, that uses resources and creates inhabitants."""
	def __init__(self, x, y, owner, instance = None, **kwargs):
		super(Settler, self).__init__(x=x, y=y, owner=owner, instance=instance, **kwargs)
		self.inhabitants = 1 # TODE: read initial value from the db
		self.max_inhabitants = 4 # TODO: read from db!

		# run self.tick every second tick (NOTE: this should be discussed)
		#game.main.session.scheduler.add_new_object(self.tick, self, 2, -1)

	def tick(self):
		"""Called by the ticker, to produce gold/inhabitants.
		"""
		# check if production is disabled and check if building is in storage mode or is a storage
		if self.active_production_line == None or self.production[self.active_production_line]['time'] == 0:
			return

		self._current_production += 1
		if (self._current_production % (self.production[self.active_production_line]['time']) == 0):
			# time to produce res
			for res in self.production[self.active_production_line]['res'].items():
				# check for needed resources
				if res[1] < 0:
					if self.inventory.get_value(res[0]) + res[1] < 0:
						return

				# check for storage capacity
				elif self.inventory.get_value(res[0]) == self.inventory.get_size(res[0]):
					return

			# everything ok, actual production:
			for res in self.production[self.active_production_line]['res'].items():
				self.inventory.alter_inventory(res[0], int(res[1]*float(self.inhabitants)/float(self.max_inhabitants)))

				#debug:
				#if res[1] >0: print "PRODUCING", res[0], "IN", self.id

	def create_carriage(self):
		# SecondaryProducer is also a consumer. Consumers create carriages by default. Settler shouldn't.
		pass
