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

from horizons.component import Component

from horizons.component.storagecomponent import StorageComponent
from horizons.component.namedcomponent import NamedComponent, SettlementNameComponent, ShipNameComponent, PirateShipNameComponent
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.component.healthcomponent import HealthComponent
from horizons.component.selectablecomponent import SelectableComponent
from horizons.component.commandablecomponent import CommandableComponent
from horizons.component.collectingcomponent import CollectingComponent
from horizons.component.settlerupgradecomponent import SettlerUpgradeComponent
from horizons.world.production.producer import Producer, QueueProducer, UnitProducer

class ComponentHolder(object):
	"""
	Class that manages Component plug-ins
	It can be inherited by all objects that can hold components

	TUTORIAL:
	I can't explain component-oriented architecture to you here, but i can give you
	an overview of how we use it:
	Instead of putting all different features of entities into single classes,
	as it's common in OOP, every feature is put into a component. This should
	increase the encapsulation, and it's easier if an object consists of 15 independent
	building blocks than if it were 15 classes, where many override the same function call
	and fight about who gets called first.
	Check class_mapping for a complete list of the different components we use.

	The components are stored in a dict, the key is their name (a string).
	This is necessary so objects can be defined as a collection of their components in
	human readable format. This is done via yaml files in content/objects in our case.
	You could check out e.g. content/objects/buildings/lumberjackcamp.yaml to see what
	it looks like.

	This class manages the components, it stores them and makes them accessible.
	Check out the actual component class in horizons/component/__init__.py
	"""

	class_mapping = {
	    'StorageComponent': StorageComponent,
	    'NamedComponent': NamedComponent,
	    'ShipNameComponent': ShipNameComponent,
	    'PirateShipNameComponent': PirateShipNameComponent,
	    'SettlementNameComponent': SettlementNameComponent,
	    'TradePostComponent': TradePostComponent,
	    'AmbientSoundComponent': AmbientSoundComponent,
	    "HealthComponent": HealthComponent,
	    'ProducerComponent': Producer,
	    'QueueProducerComponent': QueueProducer,
	    'UnitProducerComponent': UnitProducer,
	    'SelectableComponent': SelectableComponent,
	    'CommandableComponent': CommandableComponent,
	    'CollectingComponent': CollectingComponent,
	    'SettlerUpgradeComponent': SettlerUpgradeComponent,
	}


	def __init__(self, *args, **kwargs):
		super(ComponentHolder, self).__init__(*args, **kwargs)
		self.components = {}

	def initialize(self):
		"""Has to be called every time an componentholder is created. This is not
		in __init__() because we need to make sure that all other sub/parent classes
		have been inited, for example the ConcreteObject class. This is to ensure
		that all member variables of sub/parent classes are correctly set when we
		init the components. If someday all code is moved to components, this will
		not be necessary any more."""
		for component in self.__create_components():
			self.add_component(component)

	def __create_components(self):
		tmp_comp = []
		if hasattr(self, 'component_templates'):
			for entry in self.component_templates:
				if isinstance(entry, dict):
					for key, value in entry.iteritems():
						component = self.class_mapping[key].get_instance(value)
						tmp_comp.append(component)
				else:
					component = self.class_mapping[entry].get_instance()
					tmp_comp.append(component)
		# 'Resolve' dependencies by utilizing overloaded gt/lt
		tmp_comp.sort()
		return tmp_comp

	def remove(self):
		for component in self.components.values():
			component.remove()
		super(ComponentHolder, self).remove()

	def load(self, db, worldid):
		super(ComponentHolder, self).load(db, worldid)
		self.components = {}
		for component in self.__create_components():
			component.instance = self
			component.load(db, worldid)
			self.components[component.NAME] = component

	def save(self, db):
		super(ComponentHolder, self).save(db)
		for component in self.components.itervalues():
			component.save(db)

	def add_component(self, component):
		"""
		Adds new component to holder and sets the instance attribute on the component
		@param component: a component instance that is to be added
			all components will have the init only with instance attribute
		"""
		assert isinstance(component, Component)
		component.instance = self
		self.components[component.NAME] = component
		component.initialize()

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
	def get_component_template(cls, component_name):
		"""Returns the component template data given a component NAME"""
		for entry in cls.component_templates:
			if isinstance(entry, dict):
				for key, value in entry.iteritems():
					if cls.class_mapping[key].NAME == component_name:
						return value
		raise KeyError("This class does not contain a component with name: " + component_name)

