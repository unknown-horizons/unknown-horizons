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
import horizons.main

from horizons.util.living import LivingObject
from horizons.gui.keylisteners import KeyConfig
from horizons.component.selectablecomponent import SelectableComponent
from horizons.command.game import TogglePauseCommand, SpeedDownCommand, SpeedUpCommand

class IngameKeyListener(fife.IKeyListener, LivingObject):
	"""KeyListener Class to process key presses ingame"""

	def __init__(self, session):
		super(IngameKeyListener, self).__init__()
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
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
		action = KeyConfig().translate(evt)

		_Actions = KeyConfig._Actions

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

		key_event_handled = True

		if action == _Actions.ESCAPE:
			handled_by_ingame_gui = self.session.ingame_gui.on_escape()
			if not handled_by_ingame_gui:
				key_event_handled = False # let the MainListener handle this
		elif action == _Actions.GRID:
			gridrenderer = self.session.view.renderer['GridRenderer']
			gridrenderer.setEnabled( not gridrenderer.isEnabled() )
		elif action == _Actions.COORD_TOOLTIP:
			self.session.coordinates_tooltip.toggle()
		elif action == _Actions.DESTROY_TOOL:
			self.session.toggle_destroy_tool()
		elif action == _Actions.REMOVE_SELECTED:
			self.session.remove_selected()
		elif action == _Actions.ROAD_TOOL:
			self.session.ingame_gui.toggle_road_tool()
		elif action == _Actions.SPEED_UP:
			SpeedUpCommand().execute(self.session)
		elif action == _Actions.SPEED_DOWN:
			SpeedDownCommand().execute(self.session)
		elif action == _Actions.PAUSE:
			TogglePauseCommand().execute(self.session)
		elif action == _Actions.PLAYERS_OVERVIEW:
			self.session.ingame_gui.logbook.toggle_stats_visibility(widget='players')
		elif action == _Actions.SETTLEMENTS_OVERVIEW:
			self.session.ingame_gui.logbook.toggle_stats_visibility(widget='settlements')
		elif action == _Actions.SHIPS_OVERVIEW:
			self.session.ingame_gui.logbook.toggle_stats_visibility(widget='ships')
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
					if b().id == 1: continue # warehouse is unremovable

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
				    set(filter(lambda unit : unit.owner.is_local_player,
				               self.session.selected_instances))
				# drop units of the new group from all other groups
				for group in self.session.selection_groups:
					if group is not self.session.selection_groups[num]:
						group -= self.session.selection_groups[num]
			else:
				# deselect
				# we need to make sure to have a cursor capable of selection (for apply_select())
				# this handles deselection implicitly in the destructor
				self.session.set_cursor('selection')

				# apply new selection
				for instance in self.session.selection_groups[num]:
					instance.get_component(SelectableComponent).select(reset_cam=True)
				# assign copy since it will be randomly changed, the unit should only be changed on ctrl-events
				self.session.selected_instances = self.session.selection_groups[num].copy()
				# show menu depending on the entities selected
				if self.session.selected_instances:
					self.session.cursor.apply_select()
				else:
					# nothing is selected here, we need to hide the menu since apply_select doesn't handle that case
					self.session.ingame_gui.show_menu(None)
		elif action == _Actions.QUICKSAVE:
			self.session.quicksave() # load is only handled by the MainListener
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
		elif action == _Actions.SHOW_SELECTED:
			if self.session.selected_instances:
				# scroll to first one, we can never guarantee to display all selected units
				instance = iter(self.session.selected_instances).next()
				self.session.view.center( * instance.position.center().to_tuple())
				for instance in self.session.selected_instances:
					if hasattr(instance, "path") and instance.owner.is_local_player:
						self.session.ingame_gui.minimap.show_unit_path(instance)
		else:
			key_event_handled = False # nope, nothing triggered

		if key_event_handled:
			evt.consume() # prevent other listeners from being called

	def keyReleased(self, evt):
		keyval = evt.getKey().getValue()
		_Actions = KeyConfig._Actions
		action = KeyConfig().translate(evt)
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

