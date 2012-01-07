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

from functools import wraps

from fife.extensions.pychan import tools
from fife.extensions.pychan.events import EventMapper


def _find_container(widget):
	"""
	Walk through the tree to find the container the given widget is in.
	"""
	path = [widget.name]
	while widget.parent:
		widget = widget.parent
		path.append(widget.name)

	path.reverse()
	return widget, '/'.join(map(str, path))


def _log_event(widget, event_name, group_name):
	"""
	Output test code to replay the events.

	TODO: Detect dialogs (they need to be handled differently)
	"""
	container, path = _find_container(widget)

	print "# %s" % path
	print "c = gui.find(name='%s')" % container.name
	print "gui.trigger(c, '%s/%s/%s')" % (widget.name, event_name, group_name)
	print ''


def setup_gui_logger():
	"""
	By monkey-patching pychan.events.EventMapper.addEvent, we can decorate the callbacks
	with out log output.
	"""
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
				_log_event(widget, event_name, group_name)
				return tools.applyOnlySuitable(callback, event=event, widget=widget)

			return func(self, event_name, new_callback, group_name)

		return wrapper

	EventMapper.addEvent = log(EventMapper.addEvent)
