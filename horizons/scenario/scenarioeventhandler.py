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

import json
import yaml
import copy

from horizons.scheduler import Scheduler
from horizons.util import Callback, LivingObject, YamlCache

from horizons.scenario import ACTIONS, CONDITIONS


class InvalidScenarioFileFormat(Exception):
	def __init__(self, msg=None):
		if msg is None:
			msg = "Invalid scenario file."
		super(InvalidScenarioFileFormat, self).__init__(msg)

class ScenarioEventHandler(LivingObject):
	"""Handles event, that make up a scenario. See wiki.
	An instance of this class is bound to a set of events. On a new scenario, you need a new instance.

	Scenarios consist of condition-action events.
	When all conditions of an event become true, the action is executed and the event is
	removed from the scenario. All events only happen once.

	Whenever the game state changes in a way, that can change the truth value of a condition,
	the event handler must be notified. It will then check all relevant events.
	It is imperative for this notification to always be triggered, else the scenario gets stuck.
	For conditions, where this approach doesn't make sense (e.g. too frequent changes),
	a periodic check can be used.

	Save/load works by dumping all info into a yaml string in the savegame,
	which is loaded just like normal scenarios are loaded.
	"""

	CHECK_CONDITIONS_INTERVAL = 3 # seconds

	PICKLE_PROTOCOL = 2

	def __init__(self, session, scenariofile=None):
		"""
		@param session: Session instance
		@param scenariofile: yaml file that describes the scenario
		@throws InvalidScenarioFileFormat on yaml parse error
		"""
		self.inited = False
		self.session = session
		self._events = []
		self._data = {}
		# map: condition types -> events
		self._event_conditions = {}
		self._scenario_variables = {} # variables for set_var, var_eq ...
		for cond in CONDITIONS.registry.keys():
			self._event_conditions[cond] = set()
		if scenariofile:
			self._apply_data( self._parse_yaml_file( scenariofile ) )

		self.sleep_ticks_remaining = 0

		self.start()


	def start(self):
		# Add the check_events method to the scheduler to be checked every few seconds
		Scheduler().add_new_object(self._scheduled_check, self,
				                   run_in = Scheduler().get_ticks(self.CHECK_CONDITIONS_INTERVAL), loops = -1)

	def sleep(self, ticks):
		"""Sleep the ScenarioEventHandler for number of ticks. This delays all
		callbacks by the specific amount"""
		callbacks = Scheduler().get_classinst_calls(self)
		for callback in callbacks:
			Scheduler().rem_object(callback)
			callback.run_in = callback.run_in + ticks
			Scheduler().add_object(callback)
		self.sleep_ticks_remaining = ticks
		Scheduler().add_new_object(self._reduce_sleep, self, loops = ticks)

	def _reduce_sleep(self):
		self.sleep_ticks_remaining -= 1

	def end(self):
		Scheduler().rem_all_classinst_calls(self)
		self.session = None
		self._events = None
		self._data = None

	def save(self, db):
		if self.inited: # only save in case we have data applied
			db("INSERT INTO metadata(name, value) VALUES(?, ?)", "scenario_events", self.to_yaml())
		for key, value in self._scenario_variables.iteritems():
			db("INSERT INTO scenario_variables(key, value) VALUES(?, ?)", key,
			   json.dumps(value))

	def load(self, db):
		for key, value in db("SELECT key, value FROM scenario_variables"):
			self._scenario_variables[key] = json.loads(value)
		data = db("SELECT value FROM metadata WHERE name = ?", "scenario_events")
		if not data:
			return # nothing to load
		self._apply_data( self._parse_yaml( data[0][0] ) )

	def schedule_check(self, condition):
		"""Let check_events run in one tick for condition. Useful for lag prevetion if time is a
		critical factor, e.g. when the user has to wait for a function to return.."""
		if self.session.world.inited: # don't check while loading
			Scheduler().add_new_object(Callback(self.check_events, condition), self, run_in=self.sleep_ticks_remaining)

	def schedule_action(self, action):
		if self.sleep_ticks_remaining > 0:
			Scheduler().add_new_object(Callback(action, self.session), self, run_in = self.sleep_ticks_remaining)
		else:
			action(self.session)

	def check_events(self, condition):
		"""Checks whether an event happened.
		@param condition: condition from enum conditions that changed"""
		if not self.session.world.inited: # don't check while loading
			return
		events_to_remove = []
		for event in self._event_conditions[condition]:
			event_executed = event.check(self)
			if event_executed:
				events_to_remove.append(event)
		for event in events_to_remove:
			self._remove_event(event)

	def get_map_file(self):
		return self._data['mapfile']

	@classmethod
	def get_metadata_from_file(cls, filename):
		"""Returns (difficulty, author, description) from a yaml file.
		Returns "unknown" for all of these fields not specified.
		@throws InvalidScenarioFile"""
		fallback = _('unknown')
		yamldata = cls._parse_yaml_file(filename)
		difficulty = yamldata.get('difficulty', fallback)
		author = yamldata.get('author', fallback)
		desc = yamldata.get('description', fallback)
		return difficulty, author, desc

	def drop_events(self):
		"""Removes all events. Useful when player lost."""
		while self._events:
			self._remove_event(self._events[0])

	@staticmethod
	def _parse_yaml(string_or_stream):
		try:
			return YamlCache.load_yaml_data(string_or_stream)
		except Exception as e: # catch anything yaml or functions that yaml calls might throw
			raise InvalidScenarioFileFormat(str(e))

	@classmethod
	def _parse_yaml_file(cls, filename):
		return YamlCache.get_file(filename, game_data=True)

	def _apply_data(self, data):
		"""Apply data to self loaded via from yaml
		@param data: return value of yaml.load or _parse_yaml resp.
		"""
		self._data = data
		for event_dict in self._data['events']:
			event = _Event(self.session, event_dict)
			self._events.append( event )
			for cond in event.conditions:
				self._event_conditions[ cond.cond_type ].add( event )
		self.inited = True

	def _scheduled_check(self):
		"""Check conditions that can only be checked periodically"""
		for cond_type in CONDITIONS.check_periodically:
			self.check_events(cond_type)

	def _remove_event(self, event):
		assert isinstance(event, _Event)
		for cond in event.conditions:
			# we have to use discard here, since cond.cond_type might be the same
			# for multiple conditions of event
			self._event_conditions[ cond.cond_type ].discard( event )
		self._events.remove( event )

	def to_yaml(self):
		"""Returns yaml representation of current state of self.
		Another object of this type, constructed with the return value of this function, has
		to result in the very same object."""
		# every data except events are static, so reuse old data
		data = copy.deepcopy(self._data)
		del data['events']
		yaml_code = dump_dict_to_yaml(data)
		yaml_code = yaml_code.rstrip(u'}\n') # remove last } so we can add stuff
		yaml_code += ', events: [ %s ] }' % ', '.join(event.to_yaml() for event in self._events)
		return yaml_code


###
# Simple utility classes

def assert_type(var, expected_type, name):
	if not isinstance(var, expected_type):
		raise InvalidScenarioFileFormat('%s should be a %s, but is: %s' % (
			name, expected_type.__name__, str(var)))


class _Event(object):
	"""Internal data structure representing an event."""
	def __init__(self, session, event_dict):
		self.session = session
		self.actions = []
		self.conditions = []
		assert_type(event_dict['actions'], list, "actions")
		for action_dict in event_dict['actions']:
			self.actions.append( _Action(action_dict) )
		assert_type(event_dict['conditions'], list, "conditions")
		for cond_dict in event_dict['conditions']:
			self.conditions.append( _Condition(session, cond_dict) )

	def check(self, scenarioeventhandler):
		for cond in self.conditions:
			if not cond():
				return False
		for action in self.actions:
			scenarioeventhandler.schedule_action(action)
		return True

	def to_yaml(self):
		"""Returns yaml representation of self"""
		return '{ actions: [ %s ] , conditions: [ %s ]  }' % \
			   (', '.join(action.to_yaml() for action in self.actions),
				', '.join(cond.to_yaml() for cond in self.conditions))


class _Action(object):
	"""Internal data structure representing an ingame scenario action"""
	def __init__(self, action_dict):
		assert_type(action_dict, dict, "action specification")

		try:
			self.action_type = action_dict['type']
		except KeyError:
			raise InvalidScenarioFileFormat('Encountered action without type\n'+str(action_dict))
		try:
			self.callback = ACTIONS.get(self.action_type)
		except KeyError:
			raise InvalidScenarioFileFormat('Found invalid action type: %s' % self.action_type)

		self.arguments = action_dict.get('arguments', [])

	def __call__(self, session):
		"""Executes action."""
		self.callback(session, *self.arguments)

	def to_yaml(self):
		"""Returns yaml representation of self"""
		arguments_yaml = dump_dict_to_yaml(self.arguments)
		return "{arguments: %s, type: %s}" % (arguments_yaml, self.action_type)


class _Condition(object):
	"""Internal data structure representing a condition"""

	def __init__(self, session, cond_dict):
		self.session = session
		assert_type(cond_dict, dict, "condition specification")

		try:
			self.cond_type = cond_dict['type']
		except KeyError:
			raise InvalidScenarioFileFormat("Encountered condition without type\n"+str(cond_dict))
		try:
			self.callback = CONDITIONS.get(self.cond_type)
		except KeyError:
			raise InvalidScenarioFileFormat('Found invalid condition type: %s' % self.cond_type)

		self.arguments = cond_dict.get('arguments', [])

	def __call__(self):
		"""Check for condition.
		@return: bool"""
		return self.callback(self.session, *self.arguments)

	def to_yaml(self):
		"""Returns yaml representation of self"""
		arguments_yaml = dump_dict_to_yaml(self.arguments)
		return '{arguments: %s, type: "%s"}' % ( arguments_yaml, self.cond_type)


def dump_dict_to_yaml(data):
	"""Wrapper for dumping yaml data using common parameters"""
	# NOTE: the line below used to end with this: .replace('\n', '')
	# which broke formatting of logbook messages, of course. Revert in case of problems.

	# default_flow_style: makes use of short list notation without newlines (required here)
	return yaml.safe_dump(data, line_break='\n', default_flow_style=True)

