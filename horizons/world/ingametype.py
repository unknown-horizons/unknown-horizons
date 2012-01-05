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

from horizons.constants import SETTLER

class IngameType(type):

	# Base package to import from, must end with the '.', the package is appended
	basepackage = 'horizons.world.building.'
	# Class name beginning for the type.__new__ constructor
	classstring = 'Type['

	def __new__(self, id,  yaml_data):
		self.class_package =  yaml_data['baseclass'].split('.')[0]
		self.class_name = yaml_data['baseclass'].split('.')[1]

		@classmethod
		def load(cls, session, db, worldid):
			self = cls.__new__(cls)
			self.session = session
			super(cls, self).load(db, worldid)
			return self

		module = __import__(self.basepackage+self.class_package, [], [], [self.class_name])
		return type.__new__(self, self.classstring + str(id) + ']',
			(getattr(module, self.class_name),),
			{'load': load})


	def __init__(self, id, yaml_data):
		self.id = id
		self._name = yaml_data['name']
		self.radius = yaml_data['radius']
		self.component_templates = yaml_data['components']
		self.action_sets = yaml_data['actionsets']
		self.action_sets_by_level = self.action_sets_by_level(self.action_sets)
		self._object = None

	def action_sets_by_level(self, action_sets):
		as_by_level = {}
		for i in xrange(0, SETTLER.CURRENT_MAX_INCR+1):
			as_by_level[i] = []
			for setname, value in action_sets.iteritems():
				if 'level' in value and value['level'] == i:
					as_by_level[i].append(setname)
				elif 'level' not in value and i == 0:
					as_by_level[i] = setname
		return as_by_level
