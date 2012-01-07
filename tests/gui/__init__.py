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
import inspect
import os
import subprocess
import sys
from collections import deque
from functools import wraps

import mock
from fife import fife
import horizons.main
from horizons.gui.mousetools.cursortool import CursorTool
from horizons.util import Point


# path where test savegames are stored (tests/gui/ingame/fixtures/)
TEST_FIXTURES_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ingame', 'fixtures')


class TestFinished(StopIteration):
	"""Needed to distinguish between the real test finishing, or a
	dialog handler that ends."""
	__test__ = False
	pass


class GuiHelper(object):

	Key = fife.Key

	def __init__(self, pychan, runner):
		self._pychan = pychan
		self._manager = self._pychan.manager
		self._runner = runner
		self.session = horizons.main._modules.session

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


class TestRunner(object):
	"""
	I assumed it would be necessay to run the test 'in parallel' to the
	engine, e.g. click a button, let the engine run, click another button.
	That's why the TestRunner installs its _tick method into engine.pump, to
	be called once in a while. The test is a generator to make use of yield
	to allow the test to give up control to the engine.

	For the above example it is not necessary, but it might be needed later on,
	so let's leave it that way for now.
	"""
	__test__ = False

	def __init__(self, engine, test_path):
		self._engine = engine
		# Stack of test generators, see _tick
		self._gui_handlers = []

		test = self.load_test(test_path).__original__ # see gui_test
		self.setup_test(test)
		test_gen = test(GuiHelper(self._engine.pychan, self))
		self._gui_handlers.append(test_gen)
		self.start()

	def setup_test(self, test):
		if test.__use_dev_map__:
			from horizons.main import _start_dev_map
			_start_dev_map(0, False)

	def load_test(self, test_name):
		"""Load test from dotted path, e.g.:
		
			tests.gui.test_example.example
		"""
		path, name = test_name.rsplit('.', 1)
		__import__(path)
		module = sys.modules[path]
		return getattr(module, name)

	def start(self):
		self._engine.pump.append(self._tick)

	def stop(self):
		self._engine.pump.remove(self._tick)
		self._engine.breakLoop(0)

	def _tick(self):
		try:
			# Normally, we would just use the test generator here. But dialogs
			# start their own mainloop, and then we would call the test generator
			# again (while it is still running). Therefore, dialogs have to be handled
			# with separate generators.
			self._gui_handlers[-1].next() # run the most recent generator
		except TestFinished:
			self.stop()
		except StopIteration:
			pass


def gui_test(*args, **kwargs):
	"""Magic nose integration.

	Each GUI test is run in a new process. In case of an error, stderr will be
	printed. That way it will appear in the nose failure listing.

	The decorator can be used in 2 ways:

		1. No decorator arguments

			@gui_test
			def foo(session, player):
				pass

		2. Pass extra arguments (timeout, different map generator)

			@gui_test(use_dev_map=True)
			def foo(session, player):
				pass
	"""
	no_decorator_arguments = len(args) == 1 and not kwargs and inspect.isfunction(args[0])

	use_dev_map = kwargs.get('use_dev_map', False)
	use_fixture = kwargs.get('use_fixture', None)

	def deco(func):
		@wraps(func)
		def wrapped():
			test_name = '%s.%s' % (func.__module__, func.__name__)
			args = ['python', 'run_uh.py', '--gui-test', test_name]
			if use_fixture:
				path = os.path.join(TEST_FIXTURES_DIR, use_fixture + '.sqlite')
				args.extend(['--load-map', path])

			try:
				# if nose does not capture stdout, then most likely someone wants to
				# use a debugger (he passed -s at the cmdline). In that case, we will
				# redirect stdout/stderr from the gui-test process to the testrunner
				# process.
				sys.stdout.fileno()
				stdout = sys.stdout
				stderr = sys.stderr
				nose_captured = False
			except AttributeError:
				# if nose captures stdout, we can't redirect to sys.stdout, as that was
				# replaced by StringIO. Instead we capture it and return the data at the
				# end.
				stdout = subprocess.PIPE
				stderr = subprocess.PIPE
				nose_captured = True

			proc = subprocess.Popen(args, stdout=stdout, stderr=stderr)
			stdout, stderr = proc.communicate()
			if proc.returncode != 0:
				if nose_captured:
					print stdout
					print '-' * 30
					print stderr
				assert False, 'Test failed'

		# we need to store the original function, otherwise the new process will execute
		# this decorator, thus spawning a new process..
		func.__use_dev_map__ = use_dev_map
		wrapped.__original__ = func
		wrapped.gui = True # mark as gui for test selection
		return wrapped

	if no_decorator_arguments:
		# return the wrapped function
		return deco(args[0])
	else:
		# return a decorator
		return deco

gui_test.__test__ = False
