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

from horizons.component import Component
from horizons.world.production.producer import Producer

class SettlerUpgradeComponent(Component):
	"""Keeps track of upgrade material data.

	Depends heavily on the code in settler.py and is not meant as generic upgrade mechanism.
	The legacy code of settler.py can however be refactored to this file to make it modular and generally usable by other buildings.
	"""

	DEPENDENCIES = [Producer]

	# basically, this is arbitrary as long as it's not the same as any of the regular
	# production lines of the settler. We reuse data that has arbitrarily been set earlier
	# to preserve savegame compatibility.
	production_line_ids = { 1 : 24, 2 : 35, 3: 23451, 4: 34512, 5: 45123 }

	def __init__(self, upgrade_material_data):
		super(SettlerUpgradeComponent, self).__init__()
		self.upgrade_material_data = upgrade_material_data

	def initialize(self):
		self.__init()

	def load(self, db, worldid):
		self.__init()

	def __init(self):
		production_lines = self.instance.get_component(Producer).production_lines
		for level, prod_line_id in self.__class__.production_line_ids.iteritems():
			production_lines[prod_line_id] = self.get_production_line_data(level)


	def get_production_line_data(self, level):
		"""Returns production line data for the upgrade to this level"""
		prod_line_data = {
		  'time': 1,
		  'changes_animation' : 0,
		  'enabled_by_default' : False,
		  'save_statistics' : False,
		  'consumes' : self.upgrade_material_data[level]
		}
		return prod_line_data

	@classmethod
	def get_production_line_id(cls, level):
		"""Returns production line id for the upgrade to this level"""
		return cls.production_line_ids[level]





