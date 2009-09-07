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

'''
Warning:
	A Singleton is to some extend the OOP-version of a global variable.
	The Singleton pattern has many downsides.
	Please be sure you that this is really the best solution before using this code!
'''

class Singleton(type):
	"""Traditional Singleton design pattern.

	USAGE:
	class MyClass(object):
		__metaclass__ = Singleton
	"""
	def __init__(self, name, bases, dict):
		super(Singleton, self).__init__(name, bases, dict)
		self.instance = None

	def __call__(self, *args, **kwargs):
		if self.instance is None:
			self.instance = super(Singleton, self).__call__(*args, **kwargs)
		return self.instance

class ManualConstructionSingleton(Singleton):
	"""Same as Singleton, but Class() never creates an instance. Only create_instances() does."""
	def __call__(self):
		return self.instance

	def create_instance(self, *args, **kwargs):
		self.instance = super(ManualConstructionSingleton, self).__call__(*args, **kwargs)


