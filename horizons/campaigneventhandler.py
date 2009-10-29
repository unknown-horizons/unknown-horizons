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

import yaml
import copy

import horizons.main

from horizons.ext.enum import Enum
from horizons.constants import RES
from horizons.scheduler import Scheduler
from horizons.util import Callback, LivingObject


# event conditions to specify at check_events()
CONDITIONS = Enum('settlements_num_greater', 'settler_level_greater', \
                  'player_gold_greater', 'player_gold_less', 'settlement_balance_greater',
                  'building_num_of_type_greater', 'settlement_inhabitants_greater',
                  'player_balance_greater', 'player_inhabitants_greater',
                  'player_res_stored_greater', 'settlement_res_stored_greater', 'time_passed')

# conditions that can only be checked periodically
_scheduled_checked_conditions = (CONDITIONS.player_gold_greater, \
                                CONDITIONS.player_gold_less, \
                                CONDITIONS.settlement_balance_greater, \
                                CONDITIONS.settlement_inhabitants_greater, \
                                CONDITIONS.player_balance_greater, \
                                CONDITIONS.player_inhabitants_greater, \
                                CONDITIONS.player_res_stored_greater,
                                CONDITIONS.settlement_res_stored_greater,
                                CONDITIONS.time_passed)

class InvalidScenarioFileFormat(Exception):
	def __init__(self, msg=None):
		if msg is None:
			msg = "Invalid campaign file."
		super(InvalidScenarioFileFormat, self).__init__(msg)


class CampaignEventHandler(LivingObject):
	"""Handles event, that make up a campaign. See wiki."""

	def __init__(self, session, campaignfile = None):
		"""
		@param session: Session instance
		@param campaignfile: yaml file that describes the campaign
		@throws InvalidScenarioFileFormat on yaml parse error
		"""
		self.inited = False
		self.session = session
		self._events = []
		self._data = {}
		# map: condition types -> events
		self._event_conditions = {}
		for cond in CONDITIONS:
			self._event_conditions[cond] = set()
		if campaignfile:
			self._apply_data( self._parse_yaml( open(campaignfile, 'r') ) )

		# Add the check_events method to the scheduler to be checked every few seconds
		Scheduler().add_new_object(self._scheduled_check, self, runin = Scheduler().get_ticks(3), loops = -1)

	def end(self):
		Scheduler().rem_all_classinst_calls(self)
		self.session = None
		self._events = None
		self._data = None

	def save(self, db):
		if self.inited: # only save in case we have data applied
			db("INSERT INTO metadata(name, value) VALUES(?, ?)", "campaign_events", self.to_yaml())

	def load(self, db):
		data = db("SELECT value FROM metadata where name = ?", "campaign_events")
		if len(data) == 0:
			return # nothing to load
		self._apply_data( self._parse_yaml( data[0][0] ) )

	def schedule_check(self, condition):
		"""Let check_events run in one tick for condition. Useful for lag prevetion if time is a
		critical factor, e.g. when the user has to wait for a function to return.."""
		if self.session.world.inited: # don't check while loading
			Scheduler().add_new_object(Callback(self.check_events, condition), self)

	def check_events(self, condition):
		"""Checks whether an event happened.
		@param condition: condition from enum conditions that changed"""
		if not self.session.world.inited: # don't check while loading
			return
		events_to_remove = []
		for event in self._event_conditions[condition]:
			event_executed = event.check()
			if event_executed:
				events_to_remove.append(event)
		for event in events_to_remove:
			self._remove_event(event)

	def get_map_file(self):
		return self._data['mapfile']

	@classmethod
	def get_description_from_file(cls, filename):
		"""Returns the description from a yaml file.
		@throws InvalidScenarioFile"""
		return cls._parse_yaml( open(filename, 'r') )['description']

	def drop_events(self):
		"""Removes all events. Useful when player lost."""
		while self._events:
			self._remove_event(self._events[0])

	@staticmethod
	def _parse_yaml(string_or_stream):
		try:
			return yaml.load( string_or_stream )
		except Exception, e: # catch anything yaml or functions that yaml calls might throw
			raise InvalidScenarioFileFormat(str(e))

	def _apply_data(self, data):
		"""Apply data to self loaded via yaml.load
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
		for cond_type in _scheduled_checked_conditions:
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
		yaml_code = yaml.dump(data, line_break=u'\n')
		yaml_code = yaml_code.rstrip(u'}\n')
		#yaml_code = yaml_code.strip('{}')
		yaml_code += ', events: [ %s ] }' % ', '.join(event.to_yaml() for event in self._events)
		return yaml_code


###
# Campaign Actions

def show_message(session, *message):
	"""Shows a custom message in the messagewidget. If you pass more than one message, they
	will be shown after each other after a delay"""
	delay = 6
	delay_ticks = Scheduler().get_ticks(delay)
	delay_iter = 1
	for msg in message:
		Scheduler().add_new_object(Callback(session.ingame_gui.message_widget.add_custom, \
		                                    None, None, msg, visible_for=90), None, runin=delay_iter)
		delay_iter += delay_ticks

def show_db_message(session, message_id):
	"""Shows a message specified in the db on the ingame message widget"""
	session.ingame_gui.message_widget.add(None, None, message_id)

def do_win(session):
	"""Called when player won"""
	show_db_message(session, 'YOU_HAVE_WON')
	horizons.main.fife.play_sound('effects', "content/audio/sounds/events/szenario/win.ogg")

def do_lose(session):
	"""Called when player lost"""
	show_message(session, 'You failed the scenario.')
	horizons.main.fife.play_sound('effects', 'content/audio/sounds/events/szenario/loose.ogg')
	# drop events after this event
	Scheduler().add_new_object(session.campaign_eventhandler.drop_events, session.campaign_eventhandler)

###
# Campaign Conditions

def settlements_num_greater(session, limit):
	"""Returns whether the number of settlements owned by the human player is greater than limit."""
	return len(_get_player_settlements(session)) > limit

def settler_level_greater(session, limit):
	"""Returns wheter the max level of settlers is greater than limit"""
	return (session.world.player.settler_level > limit)

def player_gold_greater(session, limit):
	"""Returns whether the player has more gold then limit"""
	return (session.world.player.inventory[RES.GOLD_ID] > limit)

def player_gold_less(session, limit):
	"""Returns whether the player has less gold then limit"""
	return (session.world.player.inventory[RES.GOLD_ID] < limit)

def settlement_balance_greater(session, limit):
	"""Returns whether at least one settlement of player has a balance > limit"""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.balance > limit)

def player_balance_greater(session, limit):
	"""Returns whether the cumulative balance of all player settlements is > limit"""
	return (sum(settlement.balance for settlement in _get_player_settlements(session)) > limit)

def settlement_inhabitants_greater(session, limit):
	"""Returns whether at least one settlement of player has more than limit inhabitants"""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.inhabitants > limit)

def player_inhabitants_greater(session, limit):
	"""Returns whether all settlements of player combined have more than limit inhabitants"""
	return (sum(settlement.inhabitants for settlement in _get_player_settlements(session)) > limit)

def building_num_of_type_greater(session, building_class, limit):
	"""Check if player has more than limit buildings on a settlement"""
	for settlement in _get_player_settlements(session):
		if len([building for building in settlement.buildings if \
		       building.id == building_class]) > limit:
			return True
	return False

def player_res_stored_greater(session, res, limit):
	"""Returns whether all settlements of player combined have more than limit of res"""
	return (sum(settlement.inventory[res] for settlement in _get_player_settlements(session)) > limit)

def settlement_res_stored_greater(session, res, limit):
	"""Returs whether at least one settlement of player has more than limit of res"""
	return any(settlement for settlement in _get_player_settlements(session) if \
	           settlement.inventory[res] > limit)

def time_passed(self, secs):
	"""Returns whether at least secs seconds have passed since game start."""
	return (Scheduler().cur_tick >= Scheduler().get_ticks(secs))

def _get_player_settlements(session):
	"""Helper generator, returns settlements of local player"""
	return [ settlement for settlement in session.world.settlements if settlement.owner == session.world.player ]

###
# Simple utility classes

class _Event(object):
	"""Internal data structure representing an event."""
	def __init__(self, session, event_dict):
		self.session = session
		self.actions = []
		self.conditions = []
		for action_dict in event_dict['actions']:
			self.actions.append( _Action(action_dict) )
		for cond_dict in event_dict['conditions']:
			self.conditions.append( _Condition(session, cond_dict) )

	def check(self):
		for cond in self.conditions:
			if not cond():
				return False
		for action in self.actions:
			action(self.session)
		return True

	def to_yaml(self):
		"""Returns yaml representation of self"""
		return '{ actions: [ %s ] , conditions: [ %s ]  }' % \
		       (', '.join(action.to_yaml() for action in self.actions), \
		        ', '.join(cond.to_yaml() for cond in self.conditions))


class _Action(object):
	"""Internal data structure representing an ingame campaign action"""
	action_types = {
	  'message': show_message,
	  'db_message': show_db_message,
	  'win' : do_win,
	  'lose' : do_lose
	}

	def __init__(self, action_dict):
		self._action_type_str = action_dict['type']
		try:
			self.callback = self.action_types[ action_dict['type'] ]
		except KeyError:
			raise InvalidScenarioFileFormat('Found invalid action type: %s' % action_dict['type'])
		self.arguments = action_dict['arguments'] if 'arguments' in action_dict else []

	def __call__(self, session):
		"""Executes action."""
		self.callback(session, *self.arguments)

	def to_yaml(self):
		"""Returns yaml representation of self"""
		arguments_yaml = yaml.safe_dump(self.arguments, line_break='\n').replace('\n', '')
		return "{arguments: %s, type: %s}" % (arguments_yaml, self._action_type_str)


class _Condition(object):
	"""Internal data structure representing a condition"""
	# map condition types to functions here if renaming is necessary
	condition_types = { }
	def __init__(self, session, cond_dict):
		self.session = session
		try:
			self.cond_type = CONDITIONS.get_item_for_string(cond_dict['type'])
		except KeyError:
			raise InvalidScenarioFileFormat('Found invalid condition type: %s' % cond_dict['type'])
		# first check the global namespace for a function called same as the condition.
		# if a function has to be named differently, map the CONDITION type in self.condition_types
		if cond_dict['type'] in globals():
			self.callback = globals()[cond_dict['type']]
		else:
			self.callback = self.condition_types[ self.cond_type  ]
		self.arguments = cond_dict['arguments'] if 'arguments' in cond_dict else []

	def __call__(self):
		"""Check for condition.
		@return: bool"""
		return self.callback(self.session, *self.arguments)

	def to_yaml(self):
		"""Returns yaml representation of self"""
		arguments_yaml = yaml.safe_dump(self.arguments, line_break='\n').replace('\n', '')
		return '{arguments: %s, type: "%s"}' % ( arguments_yaml, self.cond_type.key)

