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

"""
Cleaner interface to various game/gui functions to make tests easier.
"""

import contextlib
from collections import deque

import mock

import horizons.main
from fife import fife
from horizons.constants import GAME_SPEED
from horizons.gui.mousetools import NavigationTool
from horizons.scheduler import Scheduler
from horizons.util import Point


def get_player_ship(session):
	for ship in session.world.ships:
		if ship.owner == session.world.player:
			return ship
	raise Exception('Player ship not found')


class CursorToolsPatch(object):
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

		NavigationTool._orig_get_hover_instances = NavigationTool.get_hover_instances

	def enable(self):
		self.patch1.start()
		self.patch2.start()

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

		NavigationTool.get_hover_instances = NavigationTool._orig_get_hover_instances


class GuiHelper(object):

	Key = fife.Key

	def __init__(self, pychan, runner):
		self._pychan = pychan
		self._manager = self._pychan.manager
		self._runner = runner
		self.follow_mouse = True
		# patch for using map coords with CursorTools is enabled by default
		self.cursor_map_coords = CursorToolsPatch()
		self.cursor_map_coords.enable()

		self.disable_autoscroll()
		self.speed_up()

	@property
	def session(self):
		return horizons.main._modules.session

	@property
	def cursor(self):
		return self.session.cursor

	@property
	def active_widgets(self):
		"""Active widgets are the top level containers currently
		known by pychan.
		"""
		return self._manager.allWidgets.keys()

	def find(self, name):
		"""Recursive find a widget by name."""
		widgets = deque(self.active_widgets)
		while widgets:
			w = widgets.popleft()
			if w.name == name:
				return w
			else:
				if hasattr(w, 'children'):
					widgets.extend(w.children)

		return None

	def trigger(self, root, event):
		"""Trigger a widget event in a container.

		root  - container (object or name) that holds the widget
		event - string describing the event (widget/event/group)

		Example:
			c = gui.find('mainmenu')
			gui.trigger(c, 'okButton/action/default')

		Equivalent to:
			gui.trigger('mainmenu', 'okButton/action/default')
		"""
		widget_name, event_name, group_name = event.split('/')

		# if container is given by name, look it up first
		if isinstance(root, basestring):
			root_name = root
			root = self.find(name=root_name)
			if not root:
				raise Exception("Container '%s' not found" % root_name)

		widget = root.findChild(name=widget_name)
		if not widget:
			raise Exception("'%s' contains no widget with the name '%s'" % (
								root.name, widget_name))
		try:
			callback = widget.event_mapper.callbacks[group_name][event_name]
		except KeyError:
			raise Exception("No callback for event '%s/%s' registered for widget '%s'" % (
								event_name, group_name, widget.name))

		callback()

	@contextlib.contextmanager
	def handler(self, func):
		"""Temporarily install another gui handler, e.g. to handle a dialog."""
		self._runner._gui_handlers.append(func())
		yield
		self._runner._gui_handlers.pop()

	def select(self, objects):
		"""Select all objects in the given list.

		Note, this is not the same process as selection with a mouse. For example
		selecting a ship will not result in the display of its healthbar, but the
		corresponding tab will be shown.
		"""
		self.session.selected_instances = set(objects)
		self.session.cursor.apply_select()

	def press_key(self, keycode, shift=False, ctrl=False):
		"""Simulate a global keypress.

		Example:
			gui.press_key(gui.Key.F4)
			gui.press_key(gui.Key.F4, ctrl=True)
		"""
		evt = mock.Mock()
		evt.getKey.return_value = self.Key(keycode)
		evt.isControlPressed.return_value = ctrl
		evt.isShiftPressed.return_value = shift

		self.session.keylistener.keyPressed(evt)
		self.session.keylistener.keyReleased(evt)

	def cursor_move(self, x, y):
		self.cursor.mouseMoved(self._make_mouse_event(x, y))
		if self.follow_mouse:
			self.session.view.center(x, y)

	def cursor_press_button(self, x, y, button, shift=False, ctrl=False):
		self.cursor.mousePressed(self._make_mouse_event(x, y, button, shift, ctrl))

	def cursor_release_button(self, x, y, button, shift=False, ctrl=False):
		self.cursor.mouseReleased(self._make_mouse_event(x, y, button, shift, ctrl))

	def cursor_click(self, x, y, button, shift=False, ctrl=False):
		self.cursor_move(x, y)
		self.cursor_press_button(x, y, button, shift, ctrl)
		self.cursor_release_button(x, y, button, shift, ctrl)

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
		"""Provide a nicer (yet not perfect) way to run the game for some time.

		Despite its name, this method will run the *game simulation* for X seconds.
		When the game is paused, the timer continues once the game unpauses.

		Example:
			for i in gui.run(seconds=13):
				yield
		"""

		# little hack because we don't have Python3's nonlocal
		class Flag(object):
			running = True

		def stop():
			Flag.running = False

		ticks = Scheduler().get_ticks(seconds)
		Scheduler().add_new_object(stop, None, run_in=ticks)

		while Flag.running:
			yield

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
