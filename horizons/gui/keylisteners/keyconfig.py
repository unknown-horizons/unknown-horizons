# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

import horizons.globals
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
		ROTATE_LEFT, CHAT, TRANSLUCENCY, TILE_OWNER_HIGHLIGHT, QUICKSAVE, QUICKLOAD, \
		PIPETTE, HEALTH_BAR, ESCAPE, LEFT, RIGHT, UP, DOWN, DEBUG, CONSOLE, HELP, SCREENSHOT, \
		SHOW_SELECTED, REMOVE_SELECTED = \
		range(32)


	def __init__(self):
		_Actions = self._Actions

		self.all_keys = self.get_keys_by_name()
		# map key ID (int) to action it triggers (int)
		self.keyval_action_mappings = {}

		custom_key_actions = horizons.globals.fife.get_hotkey_settings()
		for action in custom_key_actions:
			action_id = getattr(_Actions, action)
			keys_for_action = horizons.globals.fife.get_keys_for_action(action)
			for key in keys_for_action:
				key_id = self.get_key_by_name(key.upper())
				self.keyval_action_mappings[key_id] = action_id

		self.requires_shift = set([_Actions.DEBUG])

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
		def is_available(key, value):
			special_keys = ('WORLD_', 'ENTER', 'ALT', 'COMPOSE',
			                'LEFT_', 'RIGHT_', 'POWER', 'INVALID_KEY')
			return (key.startswith(tuple(ascii_uppercase)) and
			        not key.startswith(special_keys))
		return dict( (k, v) for k, v in fife.Key.__dict__.iteritems()
		                    if is_available(k, v))

	def get_current_keys(self, action):
		return horizons.globals.fife.get_keys_for_action(action)

	def get_default_keys(self, action):
		return horizons.globals.fife.get_keys_for_action(action, default=True)
