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
When activated, several hooks are installed into pychan/guichan and catch
key presses and widget interactions.
The results are formatted as code that can be used for writing GUI tests.
"""

import logging
from functools import wraps

from horizons.gui import mousetools, Gui
from horizons.gui.keylisteners.ingamekeylistener import IngameKeyListener

from fife import fife
from fife.extensions.pychan import tools
from fife.extensions.pychan.events import EventMapper


log = logging.getLogger(__name__)


# Lookup from fife.Key objects to keynames
KEY_NAME_LOOKUP = {}
for keyname in [k for k in dir(fife.Key) if k.upper() == k]:
	KEY_NAME_LOOKUP[getattr(fife.Key, keyname)] = keyname


class GuiHooks(object):
	"""
	Install hooks for several events and pass events to a logger.
	"""
	def __init__(self, logger):
		self.logger = logger
		self._setup_widget_events()
		self._setup_key_events()
		self._setup_mousetool_events()
		self._setup_dialog_detector()

	def _setup_widget_events(self):
		"""
		Wrap event callbacks before they are registered at a widget.
		"""
		log = self.logger.new_widget_event

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
					log(widget, event_name, group_name)
					return tools.applyOnlySuitable(callback, event=event, widget=widget)

				return func(self, event_name, new_callback, group_name)

			return wrapper

		EventMapper.addEvent = deco(EventMapper.addEvent)

	def _setup_key_events(self):
		"""
		Catch events when a key is released.
		"""
		log = self.logger.new_key_event

		def deco2(func):
			@wraps(func)
			def wrapper(self, evt):
				keycode = evt.getKey().getValue()
				log(KEY_NAME_LOOKUP[keycode])
				return func(self, evt)

			return wrapper

		IngameKeyListener.keyReleased = deco2(IngameKeyListener.keyReleased)

	def _setup_mousetool_events(self):
		"""
		Catch mouse events of the various mouse tools.
		"""
		log = self.logger.new_mousetool_event

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

				log(**data)

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

	def _setup_dialog_detector(self):
		"""
		Catch dialog execution.
		"""
		logger = self.logger

		def deco4(func):
			@wraps(func)
			def wrapper(self, *args, **kwargs):
				logger.dialog_opened()
				result = func(self, *args, **kwargs)
				logger.dialog_closed()
				return result
			return wrapper

		Gui.show_dialog = deco4(Gui.show_dialog)


class TestCodeGenerator(object):
	"""
	Receives events from GuiHooks and creates test code from it.
	"""
	def __init__(self):
		# Keep a list of events to detect mouse clicks (pressed and released)
		# Clicks are what we're interested in, we don't support mouseMoved/mouseDragged
		self._mousetool_events = []

	def _find_container(self, widget):
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

	def new_widget_event(self, widget, event_name, group_name):
		"""
		Output test code to trigger an event on a widget.
		"""
		container, path = self._find_container(widget)

		if container.name == '__unnamed__':
			print '# TODO this container needs a name to identify it correctly'
			print '# Path: %s' % path
		else:
			log.debug('# %s' % path)

		print "c = gui.find(name='%s')" % container.name
		print "gui.trigger(c, '%s/%s/%s')" % (widget.name, event_name, group_name)
		print ''

	def new_key_event(self, key):
		"""
		Output test code to press the key.
		"""
		print 'gui.pressKey(gui.Key.%s)' % key
		print ''

	def new_mousetool_event(self, tool_name, event_name, x, y, button):
		"""
		Prints out debug information for all captured events. Tries to detect mouse clicks
		(button pressed and released after) and emit test code for those.
		"""
		if event_name == 'mouseReleased':
			last_event = self._mousetool_events[-1]
			if last_event == ('mousePressed', x, y, button):
				print "gui.cursor_click(%s, %s, '%s')" % (x, y, button)
				self._mousetool_events.pop()
		elif event_name == 'mousePressed':
			self._mousetool_events.append((event_name, x, y, button))
		else:
			raise Exception("Event '%s' not supported." % event_name)

		# Output debug information, no test code yet
		if button:
			log.debug("# %s.%s(%d, %d, '%s')" % (tool_name, event_name, x, y, button))
		else:
			log.debug("# %s.%s(%d, %d)" % (tool_name, event_name, x, y))

	def dialog_opened(self):
		print '# Dialog opened'

	def dialog_closed(self):
		print '# Dialog closed'


def setup_gui_logger():
	GuiHooks(logger=TestCodeGenerator())
