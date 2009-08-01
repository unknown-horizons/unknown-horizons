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

from horizons.world.resourcehandler import ResourceHandler
from horizons.world.building.buildingresourcehandler import BuildingResourceHandler
from horizons.world.production.production import Production

import horizons.main

class Producer(ResourceHandler):
	"""Class for objects, that produce something.
	"""
	log = logging.getLogger("world.production")

	production_class = Production

	def __init__(self, **kwargs):
		super(Producer, self).__init__(**kwargs)
		self.__init()
		# add production lines as specified in db.
		for prod_line in horizons.main.db("SELECT id FROM production_line WHERE object_id = ? \
				AND enabled_by_default = 1", self.id):
			self.add_production(self.production_class(self.inventory, prod_line[0]))

	def __init(self):
		pass

	def add_production(self, production):
		assert isinstance(production, Production)
		self.log.debug('Producer %s: added production line %s', self.getId(), \
									 production.get_production_line_id())
		self._productions[production.get_production_line_id()] = production
		self._changed()

	def load_production(self, db, worldid):
		return self.production_class.load(db, worldid)


class ProducerBuilding(Producer, BuildingResourceHandler):
	"""Class for buildings, that produce something.
	Uses BuildingResourceHandler additionally to ResourceHandler, to enable building-specific
	behaviour"""
	pass
