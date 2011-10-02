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

from component import Component
import sys

class ComponentHolder(object):
	"""
	Class that manages Component plug-ins
	It can be inherided by all objects that can hold components
	"""
	def __init__(self, *args, **kwargs):
		self.components = {}
		super(ComponentHolder, self).__init__(*args, **kwargs)

	def remove(self):
		for component in self.components.values():
			component.remove()
		super(ComponentHolder, self).remove()

	def load(self, db, worldid):
		super(ComponentHolder, self).load(db, worldid)
		self.components = {}
		for name, module_name, class_name in db('SELECT name, module, class FROM component WHERE worldid = ?', worldid):
			# get the class object from module and call init on it
			module = __import__(module_name)
			module = sys.modules[module_name]
			self.components[name] = getattr(module, class_name)(self)
			self.components[name].load(db, worldid)

	def save(self, db):
		super(ComponentHolder, self).save(db)
		for name in self.components:
			db('INSERT INTO component(worldid, name, module, class) VALUES(?, ?, ?, ?)', \
				self.worldid, name, self.components[name].__class__.__module__, self.components[name].__class__.__name__)
			self.components[name].save(db)

	def add_component(self, component):
		"""
		Adds new component to holder and sets the instance attribute on the component
		@param component: a component instance that is to be added
			all components will have the init only with instance attribute
		"""
		assert isinstance(component, Component)
		component.instance = self
		component.initialize()
		self.components[component.NAME] = component

	def remove_component(self, component_class):
		"""
		Removes component from holder.
		"""
		if self.has_component(component_class):
			self.components[component_class.NAME].remove()
			del self.components[component_class.NAME]

	def has_component(self, component_class):
		"""
		Check if holder has component with component name
		"""
		return component_class.NAME in self.components

	def get_component(self, component):
		if self.has_component(component):
			return self.components[component.NAME]
		else:
			return None

