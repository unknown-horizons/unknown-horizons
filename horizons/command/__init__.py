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

__all__ = ['building', 'unit', 'sounds']

import logging

from horizons.util import WorldObject, get_all_subclasses
from horizons.network.packets import SafeUnpickler

class Command(object):
	"""Base class for every Command."""
	log = logging.getLogger("command")
	@classmethod
	def allow_network(self, klass):
		"""
		NOTE: this is a security related method and may lead to
		execution of arbritary code if used in a wrong way
		see documentation inside horizons.network.packets.SafeUnpickler
		"""
		SafeUnpickler.add('server', klass)

	def execute(self, session, local=False):
		"""Execute command.
		@param session: Execute command on this session's manager.
		@param local: Execute the command only locally (only used in multiplayer manager)
		@return: Propagated return value of manager's execute function.
		"""
		return session.manager.execute(self, local)

	@classmethod
	def get_all_commands(cls):
		return list(get_all_subclasses(cls))


class GenericCommand(Command):
	"""Code generator for trivial commands on an object.
	It saves an object's world id, and executes a method specified as string on it in __call__

	NOTE: Do not use floats! 2.6 and 2.7 handle them differently.
	Use like this to call obj.mymethod(42, 1337):

	class MyCommand(GenericCommand):
	  def __init__(self, obj):
	    super(MyCommand,self).__init__(obj, "mymethod", 42, 1337)
	 """
	def __init__(self, obj, method, *args, **kwargs):
		self.obj_id = obj.worldid
		self.method = method
		self.args = args
		self.kwargs = kwargs

	def __call__(self, issuer):
		return getattr(self._get_object(), self.method)(*self.args, **self.kwargs)

	def _get_object(self):
		return WorldObject.get_object_by_id(self.obj_id)

	def __str__(self):
		return "GenericCommand(%s, %s, %s, %s, %s)" % (self.__class__, self._get_object(), self.method, self.args, self.kwargs)

class GenericComponentCommand(Command):
	"""Code generator for trivial commands on a component."""
	def __init__(self, component, method, *args, **kwargs):
		self.obj_id = component.instance.worldid
		self.method = method
		self.component_name = component.NAME
		self.args = args
		self.kwargs = kwargs

	def __call__(self, issuer):
		return getattr(self._get_object().get_component_by_name(self.component_name), self.method)(*self.args, **self.kwargs)

	def _get_object(self):
		return WorldObject.get_object_by_id(self.obj_id)

	def __str__(self):
		return "GenericCompCommand(%s, %s, %s, %s, %s, %s)" % (self.__class__, self._get_object(), self.component_name, self.method, self.args, self.kwargs)
