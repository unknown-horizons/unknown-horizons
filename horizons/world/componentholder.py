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

	def add_component(self, component_name, component_class):
		"""
		Adds new component to holder.
		@param component_name: name identifier of the added component
		@param component_class: class of the component that will be initialized
			all components will have the init only with instance attribute
		"""
		component = component_class(self)
		assert isinstance(component, Component)
		self.components[component_name] = component

	def remove_component(self, component_name):
		"""
		Removes component from holder.
		"""
		if self.has_component(component_name):
			self.components[component_name].remove()
			del self.components[component_name]

	def has_component(self, component_name):
		"""
		Check if holder has component with component name
		"""
		return component_name in self.components
	
	def get_component(self, component_name):
		if self.has_component(component_name):
			return self.components[component_name]
		else:
			return None

