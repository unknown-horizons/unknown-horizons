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

"""
Cleaner interface to various game/gui functions to make tests easier.
"""


import contextlib
import os
import tempfile
import types
from unittest import mock

from fife import fife
from fife.extensions import pychan

import horizons.main
from horizons.constants import GAME_SPEED
from horizons.extscheduler import ExtScheduler
from horizons.gui.mousetools.buildingtool import BuildingTool
from horizons.gui.mousetools.cursortool import CursorTool
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.scheduler import Scheduler
from horizons.util.shapes import Point
from horizons.util.startgameoptions import StartGameOptions
from tests.gui import cooperative


def get_player_ship(session):
	"""Returns the first ship of a player."""
	for ship in session.world.ships:
		if ship.owner == session.world.player:
			return ship
	raise Exception('Player ship not found')


def move_ship(gui, ship, coords):
	"""Move ship to coordinates and wait until it arrives."""
	x, y = coords
	gui.cursor_click(x, y, 'right')

	while (ship.position.x, ship.position.y) != (x, y):
		cooperative.schedule()


def found_settlement(gui, ship_pos, coords):
	"""Move ship to coordinates and build a warehouse."""
	x, y = coords
	ship = get_player_ship(gui.session)
	gui.select([ship])
	move_ship(gui, ship, ship_pos)

	# Found a settlement
	gui.trigger('overview_trade_ship/found_settlement')
	assert isinstance(gui.cursor, BuildingTool)
	gui.cursor_click(x, y, 'left')
	assert isinstance(gui.cursor, CursorTool)

	return gui.session.world.player.settlements[-1]


def saveload(gui):
	"""Save and load the game (gui test version). Use like this:

	# For gui tests
	saveload(gui)
	"""
	fd, filename = tempfile.mkstemp()
	os.close(fd)
	assert gui.session.save(savegamename=filename)
	options = StartGameOptions.create_load_game(filename, None)
	# This hands out a new session, but `gui.session` is a property.
	horizons.main.start_singleplayer(options)
	# Restore some properties that were changed for tests:
	# Set game speed to maximum, and disable autoscroll.
	gui.setup()


class CursorToolsPatch:
	"""Temporarly changes CursorTool to interpret mouse event coordinates
	as map coordinates instead of window coordinates. Makes it easier to
	write tests.

	Example:
		gui.cursor_map_coords.enable()
		gui.cursor_move(2, 3)
		gui.cursor_map_coords.disable()
	"""
	def __init__(self):
		def patched_world_location_from_event(self, evt):
			"""Typically we expect a Mock MouseEvent, genereated by `_make_mouse_event`.

			However NavigationTool keeps track of the last event position, which is
			an instance of fife.ScreenPoint.
			"""
			try:
				# fife.MouseEvent
				x = evt.getX()
				y = evt.getY()
			except AttributeError:
				# fife.ScreenPoint
				x = evt.x
				y = evt.y

			return Point(x, y)

		self.patch1 = mock.patch('horizons.gui.mousetools.CursorTool.get_world_location', patched_world_location_from_event)
		self.patch2 = mock.patch('horizons.gui.mousetools.CursorTool.get_exact_world_location', patched_world_location_from_event)
		self.patch3 = mock.patch('horizons.gui.mousetools.TileLayingTool.get_world_location', patched_world_location_from_event)

		NavigationTool._orig_get_hover_instances = NavigationTool.get_hover_instances

	def enable(self):
		self.patch1.start()
		self.patch2.start()
		self.patch3.start()

		# this makes selecting buildings by clicking on them possible. without this, get_hover_instances receives an event with map
		# coordinates, and will not find the correct building (if any). to fix this, we're converting the coordinates back to screen space
		# and can avoid changing any other code
		def deco(func):
			def wrapped(self, evt, *args, **kwargs):
				screen_point = self.session.view.cam.toScreenCoordinates(fife.ExactModelCoordinate(evt.getX(), evt.getY()))
				evt = mock.Mock()
				evt.getX.return_value = screen_point.x
				evt.getY.return_value = screen_point.y
				return func(self, evt, *args, **kwargs)
			return wrapped
		NavigationTool.get_hover_instances = deco(NavigationTool.get_hover_instances)

	def disable(self):
		self.patch1.stop()
		self.patch2.stop()
		self.patch3.stop()

		NavigationTool.get_hover_instances = NavigationTool._orig_get_hover_instances


class GuiHelper:

	Key = fife.Key

	def __init__(self, pychan, runner):
		self._pychan = pychan
		self._manager = self._pychan.manager
		self._runner = runner
		self.follow_mouse = True
		# patch for using map coords with CursorTools is enabled by default
		self.cursor_map_coords = CursorToolsPatch()
		self.cursor_map_coords.enable()
		self.setup()

	def setup(self):
		self.disable_autoscroll()
		self.speed_up()

	@property
	def session(self):
		return horizons.main.session

	@property
	def cursor(self):
		return self.session.ingame_gui.cursor

	@property
	def active_widgets(self):
		"""Active widgets are the top level containers currently
		known by pychan.
		"""
		return self._manager.allWidgets

	def _get_children(self, w):
		if hasattr(w, 'children'):
			return w.children
		elif hasattr(w, 'findChildren'):
			return w.findChildren()

	def _find(self, widgets, name):
		"""Recursive find a widget by name.

		This is the actual search implementation behind `GuiHelper.find`.

		Finds all components that match the right-most name, e.g. foo in bar/baz/foo. From
		there, go up the tree, removing candidates that have no match for other path
		components, e.g. no baz in their parents.
		"""
		path_components = name.split('/')

		first_part = path_components.pop()
		filtered = [w for w in widgets if w.name == first_part]
		if not filtered:
			return None

		candidates = [(f, [f.parent]) for f in filtered]
		while path_components:
			path = path_components.pop()
			new_candidates = []
			for candidate, up in candidates:
				w = up.pop()
				while w and w.name != path:
					if w.name != '__unnamed__':
						up.append(w)
					w = w.parent

				if w and w.name == path:
					new_candidates.append((candidate, up + [w]))

			candidates = new_candidates

		if len(candidates) > 1:
			candidates = sorted(candidates, key=lambda c: len(c[1]))
			best_matches = [c[0] for c in candidates if len(c[1]) == len(candidates[0][1])]

			if len(best_matches) > 1:
				raise Exception('Ambigious specification {}, found {} matches'.format(
					name, len(best_matches)))
			else:
				return best_matches[0]
		elif candidates:
			return candidates[0][0]

	def find(self, name):
		"""Find a widget by name.

		`name` can consist of multiple widget names separated by a slash. In this
		case, this is interpreted as a path to the widget with the last name.
		This is necessary when multiple widgets exist with the same name.

		Example:

			gui.find('menu/button')
			# look for a widget 'menu' with a descendant named 'button'

		Recursively searches through all widgets. Some widgets will be extended
		with helper functions to allow easier interaction in tests.
		"""
		match = self._find(self.active_widgets, name)

		gui_helper = self

		if isinstance(match, pychan.widgets.ListBox):
			def select(self, value):
				"""Change selection in listbox to value.

				Example:

				    w = gui.find('list_widget')
				    w.select('A')
				"""
				index = self.items.index(value)
				self.selected = index
				# trigger callbacks for selection change
				gui_helper._trigger_widget_callback(self, can_fail=True)
				gui_helper.run()

			match.select = types.MethodType(select, match)
		elif isinstance(match, pychan.widgets.TextField):
			def write(self, text):
				"""Change text inside a textfield."""
				self.text = str(text)
				return self # return self to allow chaining

			def enter(self):
				"""Trigger callback as if ENTER was pressed."""
				gui_helper._trigger_widget_callback(self, can_fail=True)
				gui_helper.run()

			match.write = types.MethodType(write, match)
			match.enter = types.MethodType(enter, match)
		elif isinstance(match, pychan.widgets.Slider):
			def slide(self, value):
				"""Set the slider to this value and trigger callbacks."""
				self.value = float(value)

				# try two possible event group names
				# TODO find out why some sliders use 'stepslider' and others 'default'
				if not gui_helper._trigger_widget_callback(self, can_fail=True):
					gui_helper._trigger_widget_callback(self, group_name="stepslider", can_fail=True)
					gui_helper.run()

			match.slide = types.MethodType(slide, match)

		return match

	def trigger(self, widget, event=None, mouse=None):
		"""Trigger a widget event in a container.

		root  - widget (object, name or path)
				For more information on path, see `GuiHelper.find`.
		event - Optional. string describing the event (event/group)
		mouse - Optional. Can be 'left' or 'right'. Some event callbacks look
				at the event that occured, so we need to tell what mouse
				button triggered this.

		Example:
			c = gui.find('mainmenu/okButton')
			gui.trigger(c, 'action/default')

		Equivalent to:
			gui.trigger('mainmenu/okButton', 'action/default')

		Even shorter:

			gui.trigger('mainmenu/okButton')
		"""
		group_name = 'default'
		event_name = 'action'

		parts = event.split('/') if event else []
		if len(parts) == 2:
			event_name, group_name = parts
		elif len(parts) == 1:
			event_name, = parts

		# if widget is given by name, look it up first
		if isinstance(widget, str):
			widget_name = widget
			widget = self.find(widget_name)
			if not widget:
				raise Exception("Widget '{}' not found".format(widget_name))

		self._trigger_widget_callback(widget, event_name, group_name, mouse=mouse)
		self.run()

	def _trigger_widget_callback(self, widget, event_name="action", group_name="default", can_fail=False, mouse=None):
		"""Call callbacks for the given widget."""
		# Check if this widget has any event callbacks at all
		try:
			callbacks = widget.event_mapper.callbacks[group_name]
		except KeyError:
			if can_fail:
				return False
			raise Exception("No callbacks for event group '{}' for event '{}'".format(
							group_name, widget.name))

		# Unusual events are handled normally
		if event_name not in ('action', 'mouseClicked'):
			try:
				callback = callbacks[event_name]
			except KeyError:
				raise Exception("No callback for event '{}/{}' registered for widget '{}'".format(
								event_name, group_name, widget.name))
		# Treat action and mouseClicked as the same event. If a callback is not registered
		# for one, try the other
		else:
			callback = callbacks.get(event_name)
			if not callback:
				callback = callbacks.get(event_name == 'action' and 'mouseClicked' or 'action')

			if not callback:
				raise Exception("No callback for event 'action' or 'mouseClicked' registered for widget '{}'".format(
								widget.name))

		kwargs = {'widget': widget}
		if mouse:
			kwargs['event'] = self._make_mouse_event(0, 0, button=mouse)

		pychan.tools.applyOnlySuitable(callback, **kwargs)

	@contextlib.contextmanager
	def handler(self, func):
		"""Temporarily install another gui handler, e.g. to handle a dialog."""
		g = cooperative.spawn(func)
		yield
		g.join()

	def select(self, objects):
		"""Select all objects in the given list.

		Note, this is not the same process as selection with a mouse. For example
		selecting a ship will not result in the display of its healthbar, but the
		corresponding tab will be shown.
		"""
		self.session.selected_instances = set(objects)
		self.cursor.apply_select()

	def press_key(self, keycode, shift=False, ctrl=False):
		"""Simulate a global keypress.

		Example:
			gui.press_key(gui.Key.F4)
			gui.press_key(gui.Key.F4, ctrl=True)
		"""
		evt = mock.Mock()
		evt.isConsumed.return_value = False
		evt.getKey.return_value = self.Key(keycode)
		evt.isControlPressed.return_value = ctrl
		evt.isShiftPressed.return_value = shift

		if self.session:
			keylistener = self.session.ingame_gui.keylistener
		else:
			keylistener = horizons.main.gui.mainlistener

		keylistener.keyPressed(evt)
		keylistener.keyReleased(evt)

	def cursor_move(self, x, y):
		self.cursor.mouseMoved(self._make_mouse_event(x, y))
		if self.follow_mouse:
			self.session.view.center(x, y)

	def cursor_press_button(self, x, y, button, shift=False, ctrl=False):
		self.cursor.mousePressed(self._make_mouse_event(x, y, button, shift, ctrl))

	def cursor_release_button(self, x, y, button, shift=False, ctrl=False):
		self.cursor.mouseReleased(self._make_mouse_event(x, y, button, shift, ctrl))

	def cursor_click(self, x, y, button, shift=False, ctrl=False):
		# NOTE `self.run()` is a fix for gui tests with fife rev 4060+
		# it is not known why this helps, but perhaps it's not that unreasonable
		# to give the engine some time in between events (even if we trigger the
		# mousetools directly)

		self.cursor_move(x, y)
		self.run()
		self.cursor_press_button(x, y, button, shift, ctrl)
		self.run()
		self.cursor_release_button(x, y, button, shift, ctrl)
		self.run()

	def cursor_multi_click(self, *coords):
		"""Do multiple clicks in succession.

		Shift is hold to enable non-stop build and after the last coord it will be
		cancelled with a right click.
		"""
		for (x, y) in coords:
			self.cursor_click(x, y, 'left', shift=True)

		# Cancel
		x, y = coords[-1]
		self.cursor_click(x, y, 'right')

	def cursor_drag(self, start_coords, end_coords, button):
		"""Press mouse button, move the mouse, release button."""
		start_x, start_y = start_coords
		end_x, end_y = end_coords
		self.cursor_move(start_x, start_y)
		self.cursor_press_button(start_x, start_y, button)
		self.run()

		steps = max(abs(end_x - start_x), abs(end_y - start_y))
		x_step = (end_x - start_x) / float(steps)
		y_step = (end_y - start_y) / float(steps)

		for i in range(steps):
			x = int(start_x + i * x_step)
			y = int(start_y + i * y_step)
			self.cursor.mouseDragged(self._make_mouse_event(x, y, button))
			self.run()

		self.cursor_release_button(end_x, end_y, button)

	def _make_mouse_event(self, x, y, button=None, shift=False, ctrl=False):
		if button:
			button = {'left': fife.MouseEvent.LEFT,
					  'right': fife.MouseEvent.RIGHT}[button]

		evt = mock.Mock()
		evt.isConsumedByWidgets.return_value = False
		evt.getX.return_value = x
		evt.getY.return_value = y
		evt.getButton.return_value = button
		evt.isShiftPressed.return_value = shift
		evt.isControlPressed.return_value = ctrl

		return evt

	def run(self, seconds=0):
		"""Provide a nice way to run the game for some time.

		Despite its name, this method will run the *game simulation* for X seconds.
		When the game is paused, the timer continues once the game unpauses.
		"""

		if not seconds:
			cooperative.schedule()
		else:
			running = True

			def stop():
				nonlocal running
				running = False

			# Scheduler only exists inside games, use ExtScheduler in the mainmenu
			if Scheduler():
				ticks = Scheduler().get_ticks(seconds)
				Scheduler().add_new_object(stop, None, run_in=ticks)
			else:
				ExtScheduler().add_new_object(stop, None, run_in=seconds)

			while running:
				cooperative.schedule()

	def disable_autoscroll(self):
		"""
		NavigationTool.mouseMoved is using the 'real' mouse position in the window to
		check if it is near the borders and initiates auto scroll. However, we are
		sending events with map coordinates, so a location at (0, 2) would trigger
		scrolling. Disable autoscroll by replacing view.autoscroll with a NOP.
		"""
		if hasattr(self.session, 'view'):
			# try to disable only if we're ingame already
			# Tests starting in the menu need to do call `disable_autoscroll()` explicitly
			self.session.view.autoscroll = mock.Mock()

	def speed_up(self):
		"""Run the test at maximum game speed."""
		if self.session:
			self.session.speed_set(GAME_SPEED.TICK_RATES[-1])

	def speed_default(self):
		"""Reset game to normal speed."""
		if self.session:
			self.session.speed_set(GAME_SPEED.TICKS_PER_SECOND)

	def debug(self):
		"""Call this to stop the test from running and be able to interact with game."""
		self.cursor_map_coords.disable()
		self.speed_default()
		self.run(2**20)

	def print_widget_tree(self, widget):
		"""
		Helper function that recurses through a widget and its children and prints them
		nested.
		"""
		def visitor(w, level):
			print('  ' * level, '<{0} name="{1}">'.format(w.__class__.__name__, w.name))
			for child in self._get_children(w):
				visitor(child, level + 1)
			print('  ' * level, '</{0}>'.format(w.__class__.__name__))

		visitor(widget, 0)
