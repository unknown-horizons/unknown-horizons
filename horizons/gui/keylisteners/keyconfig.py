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

from fife import fife

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
		self.keystring_mappings = {
		  "g" : _Actions.GRID,
		  "h" : _Actions.COORD_TOOLTIP,
		  "x" : _Actions.DESTROY_TOOL,
		  "r" : _Actions.ROAD_TOOL,
		  "+" : _Actions.SPEED_UP,
		  "=" : _Actions.SPEED_UP,
		  "-" : _Actions.SPEED_DOWN,
		  "p" : _Actions.PAUSE,
		  "l" : _Actions.LOGBOOK,
		  "b" : _Actions.BUILD_TOOL,
		  "." : _Actions.ROTATE_RIGHT,
		  "," : _Actions.ROTATE_LEFT,
		  "c" : _Actions.CHAT,
		  "t" : _Actions.TRANSLUCENCY,
		  "a" : _Actions.TILE_OWNER_HIGHLIGHT,
		  "o" : _Actions.PIPETTE,
		  "k" : _Actions.HEALTH_BAR,
		  "d" : _Actions.DEBUG,
		  "s" : _Actions.SCREENSHOT,
		  "j" : _Actions.SHOW_SELECTED,
		}
		self.keyval_mappings = {
			fife.Key.DELETE: _Actions.REMOVE_SELECTED,
			fife.Key.ESCAPE: _Actions.ESCAPE,
			fife.Key.LEFT: _Actions.LEFT,
			fife.Key.RIGHT: _Actions.RIGHT,
			fife.Key.UP: _Actions.UP,
			fife.Key.DOWN: _Actions.DOWN,
			fife.Key.F1 : _Actions.HELP,
			fife.Key.F2 : _Actions.PLAYERS_OVERVIEW,
			fife.Key.F3 : _Actions.SHIPS_OVERVIEW,
			fife.Key.F4 : _Actions.SETTLEMENTS_OVERVIEW,
			fife.Key.F5 : _Actions.QUICKSAVE,
			fife.Key.F9 : _Actions.QUICKLOAD,
			fife.Key.F10 : _Actions.CONSOLE,
			fife.Key.F12 : _Actions.SAVE_MAP,
		}
		self.requires_shift = set( (
		  _Actions.SAVE_MAP,
		) )

	def translate(self, evt):
		"""
		@param evt: fife.Event
		@return pseudo-enum _Action
		"""
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()

		action = None
		if keystr in self.keystring_mappings:
			action = self.keystring_mappings[keystr]
		elif keyval in self.keyval_mappings:
			action = self.keyval_mappings[keyval]

		if action is None:
			return None
		elif action in self.requires_shift and not evt.isShiftPressed():
			return None
		else:
			return action # all checks passed

