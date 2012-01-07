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
import subprocess
from functools import wraps


class TestFinished(StopIteration):
	"""Needed to distinguish between the real test finishing, or a
	dialog handler that ends."""
	__test__ = False
	pass


class GuiHelper(object):

	def __init__(self, pychan, runner):
		self._pychan = pychan
		self._manager = self._pychan.manager
		self._runner = runner

	@property
	def active_widgets(self):
		return self._manager.allWidgets.keys()

	def find(self, name):
		"""Find a container by name."""
		for w in self.active_widgets:
			if w.name == name:
				return w
		return None

	def trigger(self, root, event):
		"""Trigger a widget event in a container.

		root  - container that holds the widget
		event - string describing the event
		"""
		widget_name, event_name, group_name = event.split('/')
		widget = root.findChild(name=widget_name)
		callback = widget.event_mapper.callbacks[group_name][event_name]
		callback()

	@contextlib.contextmanager
	def handler(self, func):
		"""Temporarily install another gui handler, e.g. to handle a dialog."""
		self._runner._gui_handlers.append(func())
		yield
		self._runner._gui_handlers.pop()


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
		test_gen = test(GuiHelper(self._engine.pychan, self))
		self._gui_handlers.append(test_gen)
		self.start()

	def load_test(self, test_name):
		"""Load test from dotted path, e.g.:
		
			tests.gui.test_example.example
		"""
		import sys
		path, name = test_name.rsplit('.', 1)
		__import__(path)
		module = sys.modules[path]
		return getattr(module, name)

	def start(self):
		self._engine.pump.append(self._tick)

	def stop(self):
		self._engine.pump.remove(self._tick)
		self._engine.quit()

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


def setup_gui_logger():
	"""
	By monkey-patching pychan.events.EventMapper.addEvent, we can decorate the callbacks
	with out log output.
	"""
	from fife.extensions.pychan import tools
	from fife.extensions.pychan.events import EventMapper

	def find_container(widget):
		"""
		Walk through the tree to find the container the given widget is in.
		"""
		while widget.parent:
			widget = widget.parent
		return widget

	def log(func):
		@wraps(func)
		def wrapper(self, event_name, callback, group_name):
			# filter out mouse events (too much noise)
			if 'mouse' in event_name:
				return func(self, event_name, callback, group_name)

			def new_callback(event, widget):
				"""
				pychan will pass the callback event and widget keyword arguments if expected.
				We do not know if callback expected these, so we use tools.applyOnlySuitable -
				which is what pychan does.
				"""
				print widget, find_container(widget), event_name + '/' + group_name
				return tools.applyOnlySuitable(callback, event=event, widget=widget)

			return func(self, event_name, new_callback, group_name)

		return wrapper

	EventMapper.addEvent = log(EventMapper.addEvent)


def gui_test(func):
	"""Magic nose integration.

	Each GUI test is run in a new process. In case of an error, stderr will be
	printed. That way it will appear in the nose failure listing.
	"""
	@wraps(func)
	def wrapped():
		test_name = '%s.%s' % (func.__module__, func.__name__)
		proc = subprocess.Popen(['python', 'run_uh.py', '--gui-test', test_name],
								stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = proc.communicate()
		if stderr:
			print stderr
			assert False, 'Test failed'

	# we need to store the original function, otherwise the new process will execute
	# this decorator, thus spawning a new process..
	wrapped.__original__ = func
	wrapped.gui = True # mark as gui for test selection
	return wrapped

gui_test.__test__ = False
