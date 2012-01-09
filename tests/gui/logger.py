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
When activated, the GUI logger hooks into pychan/guichan and logs actions such
as key presses and widget interactions.
The output is formatted as code that can be used for writing GUI tests.
"""

from functools import wraps

from horizons.gui import mousetools
from horizons.gui.keylisteners.ingamekeylistener import IngameKeyListener

from fife import fife
from fife.extensions.pychan import tools
from fife.extensions.pychan.events import EventMapper


# Lookup from fife.Key objects to keynames
KEY_NAME_LOOKUP = {}
for keyname in [k for k in dir(fife.Key) if k.upper() == k]:
	KEY_NAME_LOOKUP[getattr(fife.Key, keyname)] = keyname


def _find_container(widget):
	"""
	Walk up the tree to find the container the given widget is in.

	Returns the container and a path of widget names collected when traversing
	the tree.
	"""
	path = [widget.name]
	while widget.parent:
		widget = widget.parent
		path.append(widget.name)

	path.reverse()
	return widget, '/'.join(map(str, path))


def _log_widget_event(widget, event_name, group_name):
	"""
	Output test code to replay the events.

	TODO: Detect dialogs (they need to be handled differently)
	"""
	container, path = _find_container(widget)

	print "# %s" % path
	print "c = gui.find(name='%s')" % container.name
	print "gui.trigger(c, '%s/%s/%s')" % (widget.name, event_name, group_name)
	print ''


def _log_key_event(key):
	"""
	Output test code to press the key.
	"""
	print 'gui.pressKey(gui.Key.%s)' % key
	print ''


# Keep a list of events to detect mouse clicks (pressed and released)
# Clicks are what we're interested in, we don't support mouseMoved/mouseDragged
mousetool_events = []

def _log_mousetool_event(tool_name, event_name, x, y, button):
	"""
	Prints out debug information for all captured events. Tries to detect mouse clicks
	(button pressed and released after) and emit test code for those.
	"""
	if event_name == 'mouseReleased':
		last_event = mousetool_events[-1]
		if last_event == ('mousePressed', x, y, button):
			print "gui.cursor_click(%s, %s, '%s')" % (x, y, button)
			mousetool_events.pop()
	elif event_name == 'mousePressed':
		mousetool_events.append((event_name, x, y, button))
	else:
		raise Exception("Event '%s' not supported." % event_name)

	# Output debug information, no test code yet
	if button:
		print "# %s.%s(%d, %d, '%s')" % (tool_name, event_name, x, y, button)
	else:
		print "# %s.%s(%d, %d)" % (tool_name, event_name, x, y)


def setup_gui_logger():
	# Wrap event callbacks before they are registered at a widget
	def deco(func):
		@wraps(func)
		def wrapper(self, event_name, callback, group_name):
			# filter out mouse events (too much noise)
			if 'mouse' in event_name and event_name != 'mouseClicked':
				return func(self, event_name, callback, group_name)

			def new_callback(event, widget):
				"""
				pychan will pass the callback event and widget keyword arguments if expected.
				We do not know if callback expected these, so we use tools.applyOnlySuitable -
				which is what pychan does.
				"""
				_log_widget_event(widget, event_name, group_name)
				return tools.applyOnlySuitable(callback, event=event, widget=widget)

			return func(self, event_name, new_callback, group_name)

		return wrapper

	EventMapper.addEvent = deco(EventMapper.addEvent)

	# Catch events when a key is released
	def deco2(func):
		@wraps(func)
		def wrapper(self, evt):
			keycode = evt.getKey().getValue()
			_log_key_event(KEY_NAME_LOOKUP[keycode])
			return func(self, evt)

		return wrapper

	IngameKeyListener.keyReleased = deco2(IngameKeyListener.keyReleased)

	# Catch mouse events of the various mouse tools
	mouse_button = {
		fife.MouseEvent.LEFT: 'left', fife.MouseEvent.RIGHT: 'right',
	}

	def deco3(func):
		@wraps(func)
		def wrapper(self, evt):
			x, y = self._get_world_location_from_event(evt).to_tuple()
			button = mouse_button.get(evt.getButton())
			data = {
				'tool_name': self.__class__.__name__,
				'event_name': func.__name__,
				'x': x, 'y': y, 'button': button
			}

			_log_mousetool_event(**data)

			return func(self, evt)

		return wrapper

	# no mouseDragged/mouseMoved support yet
	targets = {
		mousetools.BuildingTool: ('mousePressed', 'mouseReleased', ),
		mousetools.SelectionTool: ('mousePressed', 'mouseReleased', ),
		mousetools.TearingTool: ('mousePressed', 'mouseReleased', ),
		mousetools.PipetteTool: ('mousePressed', ),
	}

	for tool, events in targets.items():
		for event in events:
			original = getattr(tool, event)
			setattr(tool, event, deco3(original))
