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

import contextlib
from collections import deque

import mock

import horizons.main
from fife import fife
from horizons.gui.mousetools.cursortool import CursorTool
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
	def active_widgets(self):
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
		event - string describing the event
		"""
		widget_name, event_name, group_name = event.split('/')

		try:
			# Some widgets use numbers as name, they need to be converted
			# otherwise the lookup fails.
			widget_name = int(widget_name)
		except ValueError:
			pass

		widget = root.findChild(name=widget_name)
		callback = widget.event_mapper.callbacks[group_name][event_name]
		callback()

	@contextlib.contextmanager
	def handler(self, func):
		"""Temporarily install another gui handler, e.g. to handle a dialog."""
		self._runner._gui_handlers.append(func())
		yield
		self._runner._gui_handlers.pop()

	def select(self, objects):
		self.session.selected_instances = set(objects)
		self.session.cursor.apply_select()

	def pressKey(self, keycode):
		evt = mock.Mock()
		evt.getKey.return_value = self.Key(keycode)

		self.session.keylistener.keyPressed(evt)
		self.session.keylistener.keyReleased(evt)

	@contextlib.contextmanager
	def cursor_map_coords(self):
		"""
		Temporarly changes CursorTool to interpret mouse event coordinates
		as map coordinates. Makes it easier to write tests.
		"""
		old = CursorTool._get_world_location_from_event

		def new(self, evt):
			return Point(evt.getX(), evt.getY())

		CursorTool._get_world_location_from_event = new
		yield
		CursorTool._get_world_location_from_event = old

	def cursor_move(self, x, y):
		self.session.cursor.mouseMoved(self._make_mouse_event(x, y))

	def cursor_press_button(self, x, y, button):
		self.session.cursor.mousePressed(self._make_mouse_event(x, y, button))

	def cursor_release_button(self, x, y, button):
		self.session.cursor.mouseReleased(self._make_mouse_event(x, y, button))

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
