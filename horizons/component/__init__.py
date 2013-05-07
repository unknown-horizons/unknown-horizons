# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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
	"""
	Base class for all components. Something like an interface.

	TUTORIAL:
	This is what all components share, basically only set up and tear down.
	It would be advisable to look through all methods here,
	and especially to see the difference between loading components (from
	a savegame) and setting them up in a normal game.

	Once you know how it works, please proceed to horizons/world/ingametype.py
	where you'll see how the actual things in Unknown Horizons are created.
	"""

	#  Store the name of this component. This has to be overwritten in subclasses
	NAME = None

	# Store dependencies to other components here
	DEPENDENCIES = []

	def __init__(self):
		"""
		Used for initialization code that does not require any other components.
		This is always called first, on construction and on load."""
		super(Component, self).__init__()
		self.instance = None # Has to be set by the componentholder

	@property
	def session(self):
		return self.instance.session

	def initialize(self):
		"""
		This is called by the ComponentHolder after it set the instance.
		Use this to initialize any needed infrastructure.
		When this is called, it is guaranteed that all other components this one
		has a dependency on have been added, but initalize may not have been called
		on them, only __init__. It is only called after construction, not on load().
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
		This does on load what __init() and initalize() together do on constructions at runtime.
		Has to set up everything that is not setup in __init__(). Note that on loading
		__init__() is called with the data needed by the component through get_instance(),
		but initialize() is not, so any work needed for loading as well should be moved
		to a separate method and called here.
		"""
		pass

	@classmethod
	def get_instance(cls, arguments=None):
		"""
		This function is used to instantiate classes from yaml data. Override this if
		the component has more than just a basic constructor with primitive types
		(takes custom classes as arguments, e.g. Storages)
		"""
		arguments = arguments or {}
		return cls(**arguments)


	def __gt__(self, other):
		return other.__class__ in self.DEPENDENCIES

	def __lt__(self, other):
		return not self.__gt__(other)
