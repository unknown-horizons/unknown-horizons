# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from yaml import YAMLObject, SafeLoader

class Component(YAMLObject):

	yaml_loader = SafeLoader

	#  Store the name of this component. This has to be overwritten in subclasses
	NAME = None

	# Must be set by each subclass!
	yaml_tag = None

	def __init__(self):
		"""
		@param instance: instance that has the component
		"""
		super(Component, self).__init__()
		assert self.yaml_tag is not None
		self.instance = None # Has to be set by the componentholder

	def initialize(self):
		"""
		This is called by the ComponentHolder it set the instance. Use this to
		initialize any needed infrastructure
		"""
		pass

	def remove(self):
		"""
		Removes component and reference to instance
		"""
		self.instance = None

	def save(self, db):
		"""
		Will do nothing, but will be always called in componentholder code, even if not implemented
		"""
		pass

	def load(self, db, worldid):
		pass
