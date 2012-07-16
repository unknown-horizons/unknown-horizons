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

from horizons.entities import Entities
from horizons.util import WorldObject
from horizons.command import GenericCommand, Command
from horizons.util.worldobject import WorldObjectNotFound

class GenericUnitCommand(GenericCommand):
	"""Same as GenericCommand, but checks if issuer == owner in __call__"""
	def __call__(self, issuer):
		try:
			unit = self._get_object()
		except WorldObjectNotFound as e:
			self.log.warn("Tried to call a unit command on an inexistent unit. It could have been killed: %s", e)
			return
		if unit.owner.worldid != issuer.worldid:
			return # don't move enemy units
		else:
			return super(GenericUnitCommand, self).__call__(issuer)

class Act(GenericUnitCommand):
	"""Command class that moves a unit.
	@param unit: Instance of Unit
	@param x, y: float coordinates where the unit is to be moved.
	"""
	def __init__(self, unit, x, y):
		super(Act, self).__init__(unit, "go", x, y)

GenericCommand.allow_network(Act)

class Attack(GenericUnitCommand):
	"""Command class that triggers attack
	@param unit: Instance of Unit
	@param target: Instance of Target
	"""
	def __init__(self, unit, target):
		super(Attack, self).__init__(unit, "user_attack", target.worldid)

GenericCommand.allow_network(Attack)

class RemoveUnit(GenericUnitCommand):
	"""
	Command class that removes the unit. Not to be used if .remove() is going to be called through an indirect command anyway.
	@param unit: Instance of Unit
	"""
	def __init__(self, unit):
		super(RemoveUnit, self).__init__(unit, "remove")

GenericCommand.allow_network(RemoveUnit)

class CreateUnit(Command):
	"""Command class that creates a unit.
	TODO: remove this command and put the code in a method in e.g. world.
	Commands are there for user interactions, and there is no user interaction, that creates a unit
	You always only add a production that creates then units, but that is simulated on every machine

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
		unit = Entities.units[self.unit_id](session=owner.session, owner=owner,
		                                    x=self.x, y=self.y, **self.kwargs)
		unit.initialize()
		return unit

GenericCommand.allow_network(CreateUnit)


class SetStance(GenericUnitCommand):
	"""Command class that moves a unit.
	@param unit: Instance of Unit
	@param stance: stance as string representation
	"""
	def __init__(self, unit, stance):
		super(SetStance, self).__init__(unit, "set_stance", stance.NAME)

	def __call__(self, issuer):
		# we need the stance component, so resolve the name
		self.args = ( self._get_object().get_component_by_name( self.args[0] ) , )
		return super(GenericUnitCommand, self).__call__(issuer)

GenericCommand.allow_network(SetStance)

