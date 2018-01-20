# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

import logging
from string import ascii_uppercase

from fife import fife

import horizons.globals
from horizons.ext.enum import Enum
from horizons.util.python.singleton import Singleton


class KeyConfig(object, metaclass=Singleton):
	"""Class for storing key bindings.
	The central function is translate().
	"""

	_Actions = Enum('LEFT', 'RIGHT', 'UP', 'DOWN',
	                'ROTATE_LEFT', 'ROTATE_RIGHT', 'SPEED_UP', 'SPEED_DOWN', 'PAUSE',
	                'ZOOM_IN', 'ZOOM_OUT',
	                'BUILD_TOOL', 'DESTROY_TOOL', 'ROAD_TOOL', 'PIPETTE',
	                'PLAYERS_OVERVIEW', 'SETTLEMENTS_OVERVIEW', 'SHIPS_OVERVIEW',
	                'LOGBOOK', 'CHAT',
	                'QUICKSAVE', 'QUICKLOAD', 'ESCAPE',
	                'TRANSLUCENCY', 'TILE_OWNER_HIGHLIGHT',
	                'HEALTH_BAR', 'SHOW_SELECTED', 'REMOVE_SELECTED',
	                'HELP', 'SCREENSHOT',
	                'DEBUG', 'CONSOLE', 'GRID', 'COORD_TOOLTIP')

	def __init__(self):
		_Actions = self._Actions
		self.log = logging.getLogger("gui.keys")

		self.all_keys = self.get_keys_by_name()
		# map key ID (int) to action it triggers (int)
		self.keyval_action_mappings = {}
		self.loadKeyConfiguration()

		self.requires_shift = {_Actions.DEBUG}

	def loadKeyConfiguration(self):
		self.keyval_action_mappings = {}
		custom_key_actions = horizons.globals.fife.get_hotkey_settings()
		for action in custom_key_actions:
			action_id = getattr(self._Actions, action, None)
			if action_id is None:
				self.log.warning('Unknown hotkey in settings: %s', action)
				continue

			keys_for_action = horizons.globals.fife.get_keys_for_action(action)
			for key in keys_for_action:
				key_id = self.get_key_by_name(key.upper())
				self.keyval_action_mappings[key_id] = action_id

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
		return self.all_keys.get(keyname)

	def get_keys_by_name(self):
		def is_available(key):
			special_keys = ('WORLD_', 'ENTER', 'ALT', 'COMPOSE',
			                'LEFT_', 'RIGHT_', 'POWER', 'INVALID_KEY')
			return (key.startswith(tuple(ascii_uppercase)) and
			        not key.startswith(special_keys))
		return {k: v for k, v in fife.Key.__dict__.items()
				if is_available(k)}

	def get_keys_by_value(self):
		def is_available(key):
			special_keys = ('WORLD_', 'ENTER', 'ALT', 'COMPOSE',
			                'LEFT_', 'RIGHT_', 'POWER', 'INVALID_KEY')
			return (key.startswith(tuple(ascii_uppercase)) and
			        not key.startswith(special_keys))
		return {v: k for k, v in fife.Key.__dict__.items()
				if is_available(k)}

	def get_keyval_to_actionid_map(self):
		return self.keyval_action_mappings

	def get_current_keys(self, action):
		return horizons.globals.fife.get_keys_for_action(action)

	def get_default_keys(self, action):
		return horizons.globals.fife.get_keys_for_action(action, default=True)

	def get_actions_by_name(self):
		"""Returns a list of the names of all the actions"""
		return [str(x) for x in self._Actions]

	def get_bindable_actions_by_name(self):
		"""Returns a list of the names of the actions which can be binded in the hotkeys interface"""
		actions = [str(x) for x in self._Actions]
		unbindable_actions = ['DEBUG', 'ESCAPE']
		for action in unbindable_actions:
			actions.remove(action)
		return actions
