# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

import horizons.main

from horizons.entities import Entities
from horizons.util import WorldObject
from horizons.command import GenericCommand, Command

class GenericUnitCommand(GenericCommand):
	"""Same as GenericCommand, but checks if issuer == owner in __call__"""
	def __call__(self, issuer):
		if self._get_object().owner.worldid != issuer.worldid:
			return
		else:
			return super(GenericUnitCommand, self).__call__(issuer)

class Act(GenericUnitCommand):
	"""Command class that moves a unit.
	@param unit: Instance of Unit
	@param x, y: float coordinates where the unit is to be moved.
	"""
	def __init__(self, unit, x, y):
		super(Act, self).__init__(unit, "go", x, y)

class CreateUnit(Command):
	"""Command class that creates a unit.
	"""
	def __init__(self, owner_id, unit_id, x, y, **kwargs):
		"""
		@param session: Session instance
		@param id: Unit id that is to be created.
		@param x, y: Unit's initial position
		@param kwargs: Additional parameters for unit creation
		"""
		self.owner_id = owner_id
		self.unit_id = unit_id
		self.x = x
		self.y = y
		self.kwargs = kwargs

	def __call__(self, issuer):
		"""__call__() gets called by the manager.
		@param issuer: the issuer of the command
		"""
		owner = WorldObject.get_object_by_id(self.owner_id)
		return Entities.units[self.unit_id](session=owner.session, owner=owner, \
		                                    x=self.x, y=self.y, **self.kwargs)
