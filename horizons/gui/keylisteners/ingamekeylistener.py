# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
import horizons.main

from horizons.util.living import LivingObject

class _Actions(object):
	"""Internal data"""
	GRID, COORD_TOOLTIP, DESTROY_TOOL, PLAYERS_OVERVIEW, ROAD_TOOL, SPEED_UP, SPEED_DOWN, \
	PAUSE, SETTLEMENTS_OVERVIEW, SHIPS_OVERVIEW, LOGBOOK, BUILD_TOOL, ROTATE_RIGHT, \
	ROTATE_LEFT, CHAT, TRANSLUCENCY, TILE_OWNER_HIGHLIGHT, QUICKSAVE, QUICKLOAD, SAVE_MAP, \
	PIPETTE, HEALTH_BAR, ESCAPE, LEFT, RIGHT, UP, DOWN, DEBUG = \
	range(28)

class IngameKeyListener(fife.IKeyListener, LivingObject):
	"""KeyListener Class to process key presses ingame"""

	def __init__(self, session):
		super(IngameKeyListener, self).__init__()
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		self.keyconfig = KeyConfig()
		horizons.main.fife.eventmanager.addKeyListenerFront(self)
		self.keysPressed = []
		# Used to sum up the keyboard autoscrolling
		self.key_scroll = [0, 0]

	def end(self):
		horizons.main.fife.eventmanager.removeKeyListener(self)
		self.session = None
		super(IngameKeyListener, self).end()

	def keyPressed(self, evt):
		keyval = evt.getKey().getValue()
		keystr = evt.getKey().getAsString().lower()
		action = self.keyconfig.translate(evt)

		was = keyval in self.keysPressed
		if not was:
			self.keysPressed.append(keyval)
		if action == _Actions.LEFT:
			if not was: self.key_scroll[0] -= 25
		if action == _Actions.RIGHT:
			if not was: self.key_scroll[0] += 25
		if action == _Actions.UP:
			if not was: self.key_scroll[1] -= 25
		if action == _Actions.DOWN:
			if not was: self.key_scroll[1] += 25

		# We scrolled, do autoscroll
		if self.key_scroll[0] != 0 or self.key_scroll != 0:
			self.session.view.autoscroll_keys(self.key_scroll[0], self.key_scroll[1])

		if action == _Actions.ESCAPE:
			if not self.session.ingame_gui.on_escape():
				return # let the MainListener handle this
		elif action == _Actions.GRID:
			gridrenderer = self.session.view.renderer['GridRenderer']
			gridrenderer.setEnabled( not gridrenderer.isEnabled() )
		elif action == _Actions.COORD_TOOLTIP:
			self.session.coordinates_tooltip.toggle()
		elif action == _Actions.DESTROY_TOOL:
			self.session.toggle_destroy_tool()
		elif action == _Actions.ROAD_TOOL:
			self.session.ingame_gui.toggle_road_tool()
		elif action == _Actions.SPEED_UP:
			self.session.speed_up()
		elif action == _Actions.SPEED_DOWN:
			self.session.speed_down()
		elif action == _Actions.PAUSE:
			self.session.gui.toggle_pause()
		elif action == _Actions.PLAYERS_OVERVIEW:
			self.session.ingame_gui.players_overview.toggle_visibility()
		elif action == _Actions.SETTLEMENTS_OVERVIEW:
			self.session.ingame_gui.players_settlements.toggle_visibility()
		elif action == _Actions.SHIPS_OVERVIEW:
			self.session.ingame_gui.players_ships.toggle_visibility()
		elif action == _Actions.LOGBOOK:
			self.session.ingame_gui.logbook.toggle_visibility()
		elif action == _Actions.DEBUG:
			pass
			#import pdb; pdb.set_trace()
			#debug code to check for memory leaks:
			"""
			import gc
			import weakref
			all_lists = []
			for island in self.session.world.islands:
				buildings_weakref = []
				for b in island.buildings:
					buildings_weakref.append( weakref.ref(b) )
				import random
				random.shuffle(buildings_weakref)
				all_lists.extend(buildings_weakref)

				for b in buildings_weakref:
					if b().id == 17: continue
					if b().id == 1: continue # bo is unremovable

					#if b().id != 2: continue # test storage now

					print 'gonna remove: ', b()
					b().remove()
					collected = gc.collect()
					print 'collected: ', collected

					if b() is not None:
						import pdb ; pdb.set_trace()
						print 'referrers: ', gc.get_referrers(b())
						a = gc.get_referrers(b())
						print

			#print all_lists
			"""

		elif action == _Actions.BUILD_TOOL:
			self.session.ingame_gui.show_build_menu()
		elif action == _Actions.ROTATE_RIGHT:
			if hasattr(self.session.cursor, "rotate_right"):
				# used in e.g. build preview to rotate building instead of map
				self.session.cursor.rotate_right()
			else:
				self.session.view.rotate_right()
				self.session.ingame_gui.minimap.rotate_right()
		elif action == _Actions.ROTATE_LEFT:
			if hasattr(self.session.cursor, "rotate_left"):
				self.session.cursor.rotate_left()
			else:
				self.session.view.rotate_left()
				self.session.ingame_gui.minimap.rotate_left()
		elif action == _Actions.CHAT:
			self.session.ingame_gui.show_chat_dialog()
		elif action == _Actions.TRANSLUCENCY:
			self.session.world.toggle_translucency()
		elif action == _Actions.TILE_OWNER_HIGHLIGHT:
			self.session.world.toggle_owner_highlight()
		elif keyval in (fife.Key.NUM_0, fife.Key.NUM_1, fife.Key.NUM_2, fife.Key.NUM_3, fife.Key.NUM_4, fife.Key.NUM_5, fife.Key.NUM_6, fife.Key.NUM_7, fife.Key.NUM_8, fife.Key.NUM_9):
			num = int(keyval - fife.Key.NUM_0)
			if evt.isControlPressed():
				# create new group (only consider units owned by the player)
				self.session.selection_groups[num] = \
				    set(filter(lambda unit : unit.owner == self.session.world.player,
				               self.session.selected_instances.copy()))
				# drop units of the new group from all other groups
				for group in self.session.selection_groups:
					if group is not self.session.selection_groups[num]:
						group -= self.session.selection_groups[num]
			else:
				for instance in self.session.selected_instances - self.session.selection_groups[num]:
					instance.deselect()
				for instance in self.session.selection_groups[num] - self.session.selected_instances:
					instance.select(reset_cam=True)
				self.session.selected_instances = self.session.selection_groups[num]
		elif action == _Actions.QUICKSAVE:
			self.session.quicksave()
		elif action == _Actions.QUICKLOAD:
			self.session.quickload()
		elif action == _Actions.SAVE_MAP:
			# require shift to make it less likely that an ordinary user stumbles upon this
			# this is done because the maps aren't usable without moving them to the right places
			self.session.ingame_gui.show_save_map_dialog()
		elif action == _Actions.PIPETTE:
			# copy mode: pipette tool
			self.session.toggle_cursor('pipette')
		elif action == _Actions.HEALTH_BAR:
			# shows health bar of every instance with an health component
			self.session.world.toggle_health_for_all_health_instances()
		else:
			return
		evt.consume()

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		action = self.keyconfig.translate(evt)
		try:
			self.keysPressed.remove(keyval)
		except:
			return
		if action == _Actions.LEFT or \
		   action == _Actions.RIGHT:
			self.key_scroll[0] = 0
		if action == _Actions.UP or \
		   action == _Actions.DOWN:
			self.key_scroll[1] = 0
		self.session.view.autoscroll_keys(self.key_scroll[0], self.key_scroll[1])


class KeyConfig(object):
	"""Class for storing key bindings.
	The central function is translate().
	"""
	def __init__(self):
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
		}
		self.keyval_mappings = {
			fife.Key.ESCAPE: _Actions.ESCAPE,
			fife.Key.LEFT: _Actions.LEFT,
			fife.Key.RIGHT: _Actions.RIGHT,
			fife.Key.UP: _Actions.UP,
			fife.Key.DOWN: _Actions.DOWN,
			fife.Key.F2 : _Actions.PLAYERS_OVERVIEW,
			fife.Key.F3 : _Actions.SETTLEMENTS_OVERVIEW,
			fife.Key.F4 : _Actions.SHIPS_OVERVIEW,
			fife.Key.F5 : _Actions.QUICKSAVE,
			fife.Key.F9 : _Actions.QUICKLOAD,
			fife.Key.F12 : _Actions.SAVE_MAP,
		}
		self.requires_shift = set( (
		  _Actions.SAVE_MAP,
		) )

	def translate(self, evt):
		"""
		@param evt: fife.Event
		@return pseudo-enum IngameKeyListener.Action
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
