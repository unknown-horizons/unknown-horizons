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

from string import ascii_uppercase

from fife import fife

import horizons.main
from horizons.util.python.singleton import Singleton

class KeyConfig(object):
	"""Class for storing key bindings.
	The central function is translate().
	"""
	__metaclass__ = Singleton

	class _Actions(object):
		"""Internal data. Use inside keylistener module."""
		GRID, COORD_TOOLTIP, DESTROY_TOOL, PLAYERS_OVERVIEW, ROAD_TOOL, SPEED_UP, SPEED_DOWN, \
		PAUSE, SETTLEMENTS_OVERVIEW, SHIPS_OVERVIEW, LOGBOOK, BUILD_TOOL, ROTATE_RIGHT, \
		ROTATE_LEFT, CHAT, TRANSLUCENCY, TILE_OWNER_HIGHLIGHT, QUICKSAVE, QUICKLOAD, SAVE_MAP, \
		PIPETTE, HEALTH_BAR, ESCAPE, LEFT, RIGHT, UP, DOWN, DEBUG, CONSOLE, HELP, SCREENSHOT, \
		SHOW_SELECTED, REMOVE_SELECTED = \
		range(33)


	def __init__(self):
		_Actions = self._Actions

		self.keyval_action_mappings = dict() # map key ID (int) to action (int)
		self.action_keyname_mappings = dict() # map action name (str) to key name (str)
		#TODO temporary settings keys, get rid of this and just use all settings!
		# for some reason getAllSettings decided to not work for module 'keys' :(
		custom_key_actions = ["GRID", "COORD_TOOLTIP", "DESTROY_TOOL", "ROAD_TOOL", "SPEED_UP", "SPEED_UP", "SPEED_DOWN", "PAUSE", "LOGBOOK", "BUILD_TOOL", "ROTATE_RIGHT", "ROTATE_LEFT", "CHAT", "TRANSLUCENCY", "TILE_OWNER_HIGHLIGHT", "PIPETTE", "HEALTH_BAR", "DEBUG", "SCREENSHOT", "SHOW_SELECTED", "REMOVE_SELECTED", "ESCAPE", "LEFT", "RIGHT", "UP", "DOWN", "HELP", "PLAYERS_OVERVIEW", "SHIPS_OVERVIEW", "SETTLEMENTS_OVERVIEW", "QUICKSAVE", "QUICKLOAD", "CONSOLE", "SAVE_MAP"]
		for action in custom_key_actions:
			action_id = getattr(_Actions, action)
			key = horizons.main.fife.get_key_for_action(action).upper()
			key_id = self.get_key_by_name(key)
			self.keyval_action_mappings[key_id] = action_id
			self.action_keyname_mappings[action] = key

		self.requires_shift = set( (
		  _Actions.SAVE_MAP,
		) )

	def translate(self, evt):
		"""
		@param evt: fife.Event
		@return pseudo-enum _Action
		"""
		keyval = evt.getKey().getValue()

		if keyval in self.keyval_action_mappings:
			action = self.keyval_action_mappings[keyval]
		else:
			return None

		if action in self.requires_shift and not evt.isShiftPressed():
			return None
		else:
			return action # all checks passed

	def get_key_by_name(self, keyname):
		return self.get_keys_by_name().get(keyname, self.get_fife_key_name(keyname))

	def get_keys_by_name(self, only_free_keys=False, force_include=None):
		def is_available(key, value):
			if force_include and key in force_include:
				return True
			special_keys = ('WORLD_', 'ENTER', 'ALT', 'COMPOSE',
			                'LEFT_', 'RIGHT_', 'POWER', 'INVALID_KEY')
			return (key.startswith(tuple(ascii_uppercase)) and
			        not key.startswith(special_keys) and
			        not (only_free_keys and value in self.keyval_action_mappings))
		return dict( (k, v) for k, v in fife.Key.__dict__.iteritems()
		                    if is_available(k, v))

	def get_keyval_to_actionid_map(self):
		return self.keyval_action_mappings

	def get_actionname_to_keyname_map(self):
		return self.action_keyname_mappings

	def get_fife_key_name(self, key):
		"""For keys that will yield keystr values, allow their input in xml settings."""
		fife_keyname_map = {
			'+': 'PLUS',
			'-': 'MINUS',
			'.': 'PERIOD',
			',': 'COMMA',
		}
		return fife_keyname_map.get(key, key)

	def save_new_key(self, action, newkey):
		oldkey = horizons.main.fife.get_key_for_action(action)
		horizons.main.fife.set_key_for_action(action, newkey)
		horizons.main.fife.save_settings() #TODO remove this, save only when hitting OK

		# Now keep track of which keys are still in use and which are available again
		self.action_keyname_mappings[action] = newkey
		old_key_id = self.get_key_by_name(oldkey)
		new_key_id = self.get_key_by_name(newkey)
		action_id = getattr(self._Actions, action)
		del self.keyval_action_mappings[old_key_id]
		self.keyval_action_mappings[new_key_id] = action_id
