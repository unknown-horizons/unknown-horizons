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
from horizons.gui.mousetools.cursortool import CursorTool
from horizons.scheduler import Scheduler
from horizons.util import Point


class GuiHelper(object):

	Key = fife.Key

	def __init__(self, pychan, runner):
		self._pychan = pychan
		self._manager = self._pychan.manager
		self._runner = runner

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

		root  - container that holds the widget
		event - string describing the event (widget/event/group)

		Example:
			c = gui.find('mainmenu')
			gui.trigger(c, 'OkButton/action/default')
		"""
		widget_name, event_name, group_name = event.split('/')

		try:
			# Some widgets use numbers as name. Their name needs to be converted,
			# otherwise the lookup fails.
			widget_name = int(widget_name)
		except ValueError:
			pass

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

	def pressKey(self, keycode):
		"""Simulate a global keypress.

		Example:
			gui.pressKey(gui.Key.F4)
		"""
		evt = mock.Mock()
		evt.getKey.return_value = self.Key(keycode)

		self.session.keylistener.keyPressed(evt)
		self.session.keylistener.keyReleased(evt)

	@contextlib.contextmanager
	def cursor_map_coords(self):
		"""Temporarly changes CursorTool to interpret mouse event coordinates
		as map coordinates instead of window coordinates. Makes it easier to
		write tests.

		Example:
			with gui.cursor_map_coords():
				gui.cursor_move(2, 3)
		"""
		old = CursorTool._get_world_location_from_event

		def new(self, evt):
			return Point(evt.getX(), evt.getY())

		CursorTool._get_world_location_from_event = new
		yield
		CursorTool._get_world_location_from_event = old

	def cursor_move(self, x, y):
		self.cursor.mouseMoved(self._make_mouse_event(x, y))

	def cursor_press_button(self, x, y, button):
		self.cursor.mousePressed(self._make_mouse_event(x, y, button))

	def cursor_release_button(self, x, y, button):
		self.cursor.mouseReleased(self._make_mouse_event(x, y, button))

	def _make_mouse_event(self, x, y, button=None):
		if button:
			button = {'left': fife.MouseEvent.LEFT,
					  'right': fife.MouseEvent.RIGHT}[button]

		evt = mock.Mock()
		evt.isConsumedByWidgets.return_value = False
		evt.getX.return_value = x
		evt.getY.return_value = y
		evt.getButton.return_value = button

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
