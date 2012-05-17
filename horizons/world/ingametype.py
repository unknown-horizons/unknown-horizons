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

import hashlib

from horizons.constants import TIER

class IngameType(type):
	"""Class that is used to create Ingame-Type-Classes from yaml data.
	@param id: building or unit type id
	@param yaml_data: a dict containing all the data read from yaml files

	Note this creates class types, NOT instances.
	These types are created at the beginning of a session
	and are later used to create instances, when buildings are built.
	The __new__() function uses quite some python magic to construct the new class.

	TUTORIAL:
	Check out the __new__() function if you feel your pretty good with python and
	are interested in how it all works,	otherwise, continue to the __init__() function.
	"""

	# Base package to import from, must end with the '.', the package is appended
	basepackage = 'horizons.world.building.'
	# Class name for the type.__new__ constructor
	classstring = 'Type[{id}]'

	def __new__(self, id,  yaml_data):
		class_package = yaml_data['baseclass'].split('.')[0]
		class_name = yaml_data['baseclass'].split('.')[1]

		@classmethod
		def load(cls, session, db, worldid):
			self = cls.__new__(cls)
			self.session = session
			super(cls, self).load(db, worldid)
			return self

		module = __import__(str(self.basepackage+class_package), [], [], [str(class_name)])
		return type.__new__(self, self.classstring.format(id=id),
			(getattr(module, class_name),),
			{'load': load, 'class_package': str(class_package), 'class_name': str(class_name)})

	def _strip_translation_marks(self, string):
		if string.startswith("_ "):
			return string[2:]
		else:
			return string

	def __init__(self, id, yaml_data):
		self.id = id
		# self._name is always some default name
		# self._level_specifc_names is optional and contains a dict like this: { level_id : name }
		# (with entries for all increments in which it is active)
		name_data = yaml_data['name']
		if isinstance(name_data, dict): # { level_id : name }
			# fill up dict (fall down to highest class which has an name
			name = None
			self._level_specific_names = {}
			for lvl in xrange(min(name_data), TIER.CURRENT_MAX + 1):
				if lvl in name_data:
					name = _( self._strip_translation_marks( name_data[lvl] ) )
				assert name is not None, "name attribute is wrong: "+str(yaml_data['name'])
				self._level_specific_names[lvl] = name
			_name = name_data[ min(name_data) ] # use first as default
			self._name = _( self._strip_translation_marks( _name ) )
		else: # assume just one string
			self._name = _( self._strip_translation_marks( name_data ) )
		self.radius = yaml_data['radius']
		self.component_templates = yaml_data['components']
		self.action_sets = yaml_data['actionsets']
		self.baseclass = yaml_data['baseclass'] # mostly only for debug
		self._real_object = None # wrapped by _object

		self._parse_component_templates()

		# TODO: move this to the producer component as soon as there is support for class attributes there
		self.additional_provided_resources = yaml_data['additional_provided_resources'] if 'additional_provided_resources' in yaml_data else []

		"""TUTORIAL: Now you know the basic attributes each type has. Further attributes
		specific to buildings and units can be found in horizons/world/{buildings/units}/__init__.py
		which contains the unit and building specific attributes and loading.

		By now you should know the basic constructs used in uh, so we feel comfortable
		stoping the tutorial here. Be sure to join our IRC channel and idle around there.
		You'll find tasks for getting into the code in our trac.unknown-horizons.org

		Other relevant parts of the code you might be interested in are:
		* commands: horizons/commands. Abstracts all user interactions.
		* scheduler: horizons/scheduler.py. Manages ingame time.
		* extscheduler: horizons/extscheduler.py. Manages wall clock time.
		* scenario: horizons/scenario. Condition-action system for scenarios and full campaigns
		* automatic tests: tests/. Contains unit tests, gui tests and game (system) tests
		* networking: horizons/network. Sending stuff over the wire
		* concreteobject: horizons/world/concreteobject.py. Things with graphicals representation
		* gui: horizons/gui. The ugly parts. IngameGui and Gui, tabs and widgets.
		* production: horizons/world/production
		** Producer: producer component, manages everything
		** ProductionLine: keeps data about the different production lines.
		** Production: the alive version of the production line.Used when a building
		               actually produces something, stores progress and the li ke.
		* engine: horizons/engine. Direct interface to fife.
		* ai: horizons/ai/aiplayer. Way too big to describe here.
		"""

	def _parse_component_templates(self):
		"""Prepares misc data in self.component_templates"""
		producer = [ comp for comp in self.component_templates if \
		             isinstance(comp, dict) and comp.iterkeys().next() == 'ProducerComponent' ]
		if producer:
			# we want to support string production line ids, the code should still only see integers
			# therefore we do a deterministic string -> int conversion here

			producer_data = producer[0]['ProducerComponent']
			original_data = producer_data['productionlines']

			new_data = {}

			for old_key, v in original_data.iteritems():
				if isinstance(old_key, int):
					new_key = old_key
				else:
					# hash the string
					new_key = int(hashlib.sha1(old_key).hexdigest(), 16)
					# crop to integer. this might not be necessary, however the legacy code operated
					# on this data type, so problems might occur, also with respect to performance.
					# in princpile, strings and longs should also be supported, but for the sake of
					# safety, we use ints.
					new_key = int( new_key % 2**31 ) # this ensures it's an integer on all reasonable platforms
				if new_key in new_data:
					raise Exception("Error: production line id conflict. Please change \"%s\" to anything else for \"%s\"" % (old_key, self.name))
				new_data[new_key] = v

			producer_data['productionlines'] = new_data


	@property
	def _object(self):
		if self._real_object is None:
			self._loadObject()
		return self._real_object

	def _loadObject(self):
		"""Inits self._real_object"""
		raise NotImplementedError()

	@property
	def name(self):
		return self._name
