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

class Component(object):

	#  Store the name of this component. This has to be overwritten in subclasses
	NAME = None

	# Store dependencies to other components here
	DEPENDENCIES = []

	def __init__(self):
		"""
		Used for initialisation code that does not require any other components
		"""
		super(Component, self).__init__()
		self.instance = None # Has to be set by the componentholder
		self.session = None  # Has to be set by the componentholder

	def initialize(self):
		"""
		This is called by the ComponentHolder after it set the instance.
		Use this to initialize any needed infrastructure.
		When this is called, it is guaranteed that all other components have been added,
		but initalized may not have been called on them, only __init__.
		It is only called after construction, not on load.
		"""
		pass

	def remove(self):
		"""
		Removes component and reference to instance
		"""
		self.instance = None

	def save(self, db):
		"""
		Will do nothing, but will be always called in componentholder code, even if not implemented.
		"""
		pass

	def load(self, db, worldid):
		"""
		This does on load what __init__, __init and initalize together do on constructions at runtime.
		Has to set up *everything*, also add every member variable.
		"""
		pass

	@classmethod
	def get_instance(cls, arguments={}):
		"""
		This function is used to instantiate classes from yaml data. Override this if
		the component has more than just a basic constructor with primitiv types
		(takes Custom classes as arguments e.g. Storages)
		"""
		return cls(**arguments)


	def __gt__(self, other):
		return other.__class__ in self.DEPENDENCIES

	def __lt__(self, other):
		return not self.__gt__(other)