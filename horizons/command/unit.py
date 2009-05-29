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

import fife
import horizons.main
from horizons.util import Point, WorldObject

class Act(object):
	"""Command class that moves a unit.
	@param unit_fife_id: int FifeId of the unit that is to be moved.
	@param x, y: float coordinates where the unit is to be moved.
	@param layer: the layer the unit is present on.
	"""
	def __init__(self, unit, x, y):
		self.unit = unit.getId()
		self.x = x
		self.y = y

	def __call__(self, issuer):
		"""__call__() gets called by the manager.
		@param issuer: the issuer of the command
		"""
		WorldObject.get_object_by_id(self.unit).go(self.x, self.y)

class CreateUnit(object):
	"""Command class that creates a unit.
	@param id: Unit id that is to be created.
	@param x, y: Units initial position
	"""
	def __init__(self, building_id, prodline_id):
		self.building_id = building_id
		self.prodline_id = prodline_id

	def __call__(self, issuer):
		"""__call__() gets called by the manager.
		@param issuer: the issuer of the command
		"""
		building = WorldObject.get_object_by_id(self.building_id)
		building.produce(self.prodline_id)

from horizons.util.encoder import register_classes
register_classes(Act)
register_classes(CreateUnit)
