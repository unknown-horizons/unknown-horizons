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
from yaml import load, dump
from yaml import SafeLoader as Loader

from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.component.namedcomponent import NamedComponent, SettlementNameComponent, ShipNameComponent, PirateShipNameComponent
from horizons.world.tradepost import TradePostComponent
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.world.component.healthcomponent import HealthComponent
from horizons.world.units import UnitClass

class ComponentHolder(object):
	"""
	Class that manages Component plug-ins
	It can be inherided by all objects that can hold components
	"""

	class_mapping = {
	    'StorageComponent': StorageComponent,
	    'NamedComponent': NamedComponent,
	    'ShipNameComponent': ShipNameComponent,
	    'PirateShipNameComponent': PirateShipNameComponent,
	    'SettlementNameComponent': SettlementNameComponent,
	    'TradePostComponent': TradePostComponent,
	    'AmbientSoundComponent': AmbientSoundComponent,
	    "HealthComponent": HealthComponent
	}


	def __init__(self, *args, **kwargs):
		super(ComponentHolder, self).__init__(*args, **kwargs)
		self.__load_components()

	def __load_components(self):
		self.components = {}
		if hasattr(self, 'component_templates'):
			for entry in self.component_templates:
				if isinstance(entry, dict):
					for key, value in entry.iteritems():
						component = self.class_mapping[key].get_instance(value)
						self.components[component.NAME] = component
				else:
					component = self.class_mapping[entry].get_instance()
					self.components[component.NAME] = component


	def remove(self):
		for component in self.components.values():
			component.remove()
		super(ComponentHolder, self).remove()

	def load(self, db, worldid):
		super(ComponentHolder, self).load(db, worldid)
		self.__load_components()
		for name in self.components:
			self.components[name].load(db, worldid)

	def save(self, db):
		super(ComponentHolder, self).save(db)
		for name in self.components:
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

	def get_component_by_name(self, name):
		if name in self.components:
			return self.components[name]
		else:
			return None

	@classmethod
	def read_component_file(cls, filename):
		stream = file(filename, 'r')
		result = load(stream, Loader=Loader)
		print result
		components = []

		for index, entry in enumerate(components):
			print index, entry

		unit = UnitClass(None, id=result['id'], class_package=result['classpackage'], class_type=result['classtype'], radius=result['radius'], classname=result['classname'], action_sets=result['actionsets'])
		print unit

		return components