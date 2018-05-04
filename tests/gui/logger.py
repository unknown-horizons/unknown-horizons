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
When activated, several hooks are installed into pychan/guichan and catch
key presses and widget interactions.
The results are formatted as code that can be used for writing GUI tests.
"""


import logging
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple

from fife import fife
from fife.extensions.pychan import tools, widgets
from fife.extensions.pychan.events import EventMapper

from horizons.gui import mousetools
from horizons.gui.keylisteners.ingamekeylistener import IngameKeyListener
from horizons.gui.windows import Dialog

log = logging.getLogger(__name__)


# Lookup from fife.Key objects to keynames
KEY_NAME_LOOKUP = {}
for keyname in [k for k in dir(fife.Key) if k.upper() == k]:
	KEY_NAME_LOOKUP[getattr(fife.Key, keyname)] = keyname


class GuiHooks:
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
		"""Capture events on widgets.

		We log events by wrapping callbacks before they are registered at a widget.
		"""
		log = self.logger.new_widget_event

		def deco2(func):
			@wraps(func)
			def wrapper(self, *args, **kwargs):
				func(self, *args, **kwargs)

				def callback(event, widget):
					# this can be a no-op because we're patching addEvent below, which
					# handles the logging
					pass

				# Provide a default callback for listboxes. Some will never have a
				# callback installed because their selection is just read later.
				# But we depend on event callbacks to detect events.
				if isinstance(self.widget_ref(), widgets.ListBox):
					self.capture('action', callback, 'default')
				# We can't detect keypresses on textfields yet, but at least capture
				# the event when we select the widget
				elif isinstance(self.widget_ref(), widgets.TextField):
					self.capture('mouseClicked', callback, 'default')

			return wrapper

		EventMapper.__init__ = deco2(EventMapper.__init__)

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
				data = {
					'keycode': evt.getKey().getValue(),
					'shift': evt.isShiftPressed(),
					'ctrl': evt.isControlPressed()
				}
				log(**data)
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
				x, y = self.get_world_location(evt).to_tuple()
				button = mouse_button.get(evt.getButton())
				data = {
					'tool_name': self.__class__.__name__,
					'event_name': func.__name__,
					'x': x, 'y': y, 'button': button
				}

				log(**data)

				return func(self, evt)

			return wrapper

		# no mouseMoved support yet
		targets = {
			mousetools.BuildingTool: ('mousePressed', 'mouseReleased', 'mouseDragged', ),
			mousetools.SelectionTool: ('mousePressed', 'mouseReleased', 'mouseDragged', ),
			mousetools.TearingTool: ('mousePressed', 'mouseReleased', 'mouseDragged', ),
			mousetools.PipetteTool: ('mousePressed', ),
			mousetools.TileLayingTool: ('mousePressed', 'mouseReleased', 'mouseDragged', ),
		} # type: dict[Any, Tuple[str, ...]]

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

		Dialog._execute = deco4(Dialog._execute)


class TestCodeGenerator:
	"""
	Receives events from GuiHooks and creates test code from it.
	"""
	def __init__(self):
		# Keep a list of events to detect mouse clicks (pressed and released)
		# Clicks are what we're interested in, we don't support mouseMoved
		self._mousetool_events = [] # type: List[Tuple[str, int, int, str]]

		self._dialog_active = False
		self._dialog_opener = [] # type: List[str] # the code that triggered the dialog

		# The generator will not print out new code immediately, because the event might
		# have triggered a dialog (and we don't know yet). Therefore we need to store it
		# until we either receive a new event or know that a dialog was opened.
		self._last_command = [] # type: List[str]
		self._handler_count = 1

		# Keep track of the last slider event. When moving the slider, many events are
		# emitted. We will generate code for the last value.
		self._last_slider_event = None # type: Optional[widgets.Slider]

	def _add(self, code):
		if self._dialog_active:
			# when a dialog is active, we emit the code right away
			self._emit(code)
			return

		if self._last_command:
			self._emit(self._last_command)
		self._last_command = code

	def _emit(self, lines):
		for line in lines:
			if self._dialog_active:
				print('\t', end=' ')
			print(line)

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
			print('# FIXME this container needs a name to identify it!')
			print('# Path: {}'.format(path))
		elif event_name == 'action' and group_name == 'action_listener':
			# this is a custom event defined in engine.pychan_util to play click sounds
			# for widgets
			pass
		else:
			log.debug('# {}'.format(path))
			code = None

			# Emit code for the last slider that was manipulated, but only if the current
			# event is from a different widget. This is a work around to avoid generating
			# lots of code for every small mouse move.
			if self._last_slider_event:
				w = self._last_slider_event
				if w.name != widget.name:
					self._add(["gui.find('{}').slide({:f})".format(w.name, w.value), ""])
					self._last_slider_event = None

			if isinstance(widget, widgets.ListBox):
				selection = widget.items[widget.selected]
				code = "gui.find('{}').select(u'{}')".format(widget.name, selection)
			elif isinstance(widget, widgets.TextField):
				code = "gui.find('{}').write(TODO)".format(widget.name)
			elif isinstance(widget, widgets.Slider):
				self._last_slider_event = widget
			else:
				if group_name == 'default':
					if event_name in ('action', 'mouseClicked'):
						code = "gui.trigger('{}/{}')".format(container.name, widget.name)
					else:
						code = "gui.trigger('{}/{}', '{}')".format(
							container.name, widget.name, event_name)
				else:
					code = "gui.trigger('{}/{}', '{}/{}')".format(
						container.name, widget.name, event_name, group_name)

			if code:
				self._add([code, ''])
				code = None

	def new_key_event(self, keycode, shift=False, ctrl=False):
		"""
		Output test code to press the key.
		"""
		try:
			args = ['gui.Key.{}'.format(KEY_NAME_LOOKUP[keycode])]
			if shift:
				args.append('shift=True')
			if ctrl:
				args.append('ctrl=True')

			code = 'gui.press_key({})'.format(', '.join(args))
		except KeyError:
			code = '# Unknown key (code {})'.format(keycode)

		self._add([code, ''])

	def new_mousetool_event(self, tool_name, event_name, x, y, button):
		"""
		Prints out debug information for all captured events. Tries to detect mouse clicks
		(button pressed and released after) and emit test code for those.
		"""
		if event_name == 'mouseReleased':
			last_event = self._mousetool_events[-1]
			# simple click
			if last_event == ('mousePressed', x, y, button):
				self._add(["gui.cursor_click({}, {}, '{}')".format(x, y, button)])
				self._mousetool_events.pop()
			# mouse dragged
			elif (last_event[0], last_event[-1]) == ('mousePressed', button):
				start = last_event[1], last_event[2]
				end = x, y
				self._add(["gui.cursor_drag(({}, {}), ({}, {}), '{}')".format(
					start[0], start[1], end[0], end[1], button
				)])
		elif event_name == 'mousePressed':
			self._mousetool_events.append((event_name, x, y, button))
		elif event_name == 'mouseDragged':
			# TODO for now we ignore these events, if the position between mousePressed
			# and mouseReleased changed, we assume the mouse was moved and generate a
			# drage event
			pass
		else:
			raise Exception("Event '{}' not supported.".format(event_name))

		# Output debug information, no test code yet
		if button:
			log.debug("# {}.{}({:d}, {:d}, '{}')".format(
				tool_name, event_name, x, y, button))
		else:
			log.debug("# {}.{}({:d}, {:d})".format(
				tool_name, event_name, x, y))

	def dialog_opened(self):
		"""
		Start the dialog handler:

			def func1():
				# code for new events will follow
		"""
		self._dialog_opener = self._last_command
		self._last_command = []
		self._emit(['def func{:d}():'.format(self._handler_count)])
		self._dialog_active = True

	def dialog_closed(self):
		"""
		Emits code like this when the dialog was closed. `func` is the handler code
		that is started in `dialog_opened` and will contain all events in the dialog's
		lifetime.

		    with gui.handler(func):
			    # code that triggered the dialog
				gui.cursor_click(2, 3, 'left')
		"""
		self._dialog_active = False
		self._emit(['with gui.handler(func{:d}):'.format(self._handler_count)])
		for line in self._dialog_opener:
			self._emit(['\t' + line])
		self._last_command = []
		self._handler_count += 1


def setup_gui_logger():
	GuiHooks(logger=TestCodeGenerator())
