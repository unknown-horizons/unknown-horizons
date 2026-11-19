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

"""Regression tests for touchpad / two-finger scrolling.

The tests inject real SDL events with ``tests.gui.sdl_input`` instead of calling
``CursorTool`` directly. That exercises SDL -> FIFE ``EventManager`` -> mouse
listener dispatch -> UH, which is where the historical ``Caught a director
exception`` crash happened.

Run them with::

	pytest --gui-tests tests/gui/test_touch_scroll.py

They use a dummy video/audio driver, so no physical input device is needed.
"""

from fife import fife

import horizons.globals
from tests.gui import gui_test
from tests.gui.sdl_input import push_finger_pan, push_mouse_wheel


class _WheelRecorder(fife.IMouseListener):
	"""Record all four wheel callbacks."""

	def __init__(self):
		fife.IMouseListener.__init__(self)
		self.events = []

	def isGlobalListener(self):
		return True

	def mouseWheelMovedUp(self, evt):
		self.events.append("up")

	def mouseWheelMovedDown(self, evt):
		self.events.append("down")

	def mouseWheelMovedLeft(self, evt):
		self.events.append("left")

	def mouseWheelMovedRight(self, evt):
		self.events.append("right")


class _PartialWheelRecorder(fife.IMouseListener):
	"""Record vertical wheel callbacks and omit the horizontal ones.

	Omitting ``mouseWheelMovedLeft``/``mouseWheelMovedRight`` is deliberate: it
	reproduces the listener shape that used to abort the process. FIFE must
	provide no-op defaults so this subclass stays valid.
	"""

	def __init__(self):
		fife.IMouseListener.__init__(self)
		self.events = []

	def isGlobalListener(self):
		return True

	def mouseWheelMovedUp(self, evt):
		self.events.append("up")

	def mouseWheelMovedDown(self, evt):
		self.events.append("down")


def _install_recorders():
	complete = _WheelRecorder()
	partial = _PartialWheelRecorder()
	event_manager = horizons.globals.fife.eventmanager
	event_manager.addMouseListenerFront(complete)
	event_manager.addMouseListenerFront(partial)
	return event_manager, complete, partial


def _remove_recorders(event_manager, *recorders):
	for recorder in recorders:
		event_manager.removeMouseListener(recorder)


def _screen_center():
	settings = horizons.globals.fife.engine_settings
	return settings.getScreenWidth() // 2, settings.getScreenHeight() // 2


def _pump(gui, seconds=0.2):
	gui.run(seconds=seconds)


@gui_test(use_dev_map=True, timeout=60)
def test_two_finger_scroll_ingame(gui):
	"""Vertical pans zoom; horizontal pans neither zoom nor crash."""
	event_manager, complete, partial = _install_recorders()
	try:
		x, y = _screen_center()

		zoom_before_wheel = gui.session.view.cam.getZoom()
		push_mouse_wheel(0.0, 1.0, x, y)
		_pump(gui)
		zoom_after_wheel = gui.session.view.cam.getZoom()
		assert zoom_after_wheel > zoom_before_wheel

		# Mostly vertical, with the small horizontal jitter a real touchpad
		# produces. This must stay vertical.
		complete.events.clear()
		partial.events.clear()
		push_finger_pan(touch_id=1, fingers=2, dx=0.007, dy=0.05, steps=5)
		_pump(gui)
		assert complete.events, "no wheel events reached a mouse listener"
		assert "left" not in complete.events, complete.events
		assert "right" not in complete.events, complete.events
		assert "down" in complete.events, complete.events
		assert gui.session.view.cam.getZoom() < zoom_after_wheel

		# A deliberate horizontal pan must not zoom. The partial listener is
		# still installed; under a pure-virtual listener interface this is the
		# event that used to abort the process.
		zoom_before_horizontal = gui.session.view.cam.getZoom()
		complete.events.clear()
		partial.events.clear()
		push_finger_pan(
			touch_id=2,
			fingers=2,
			dx=0.08,
			dy=0.005,
			steps=5,
			start_x=0.2,
			start_y=0.5,
		)
		_pump(gui)
		assert complete.events, "no horizontal wheel events reached a mouse listener"
		assert set(complete.events) == {"right"}, complete.events
		assert gui.session.view.cam.getZoom() == zoom_before_horizontal
	finally:
		_remove_recorders(event_manager, complete, partial)


@gui_test(timeout=60)
def test_two_finger_scroll_menu(gui):
	"""The same gestures must not crash in the main menu."""
	event_manager, complete, partial = _install_recorders()
	try:
		x, y = _screen_center()

		# One event over the map-like background and one over the
		# singleplayer button, so both empty-space and widget hit-testing are
		# involved.
		for wheel_x, wheel_y, pos_x, pos_y in (
			(-1.0, 0.0, x, y),
			(1.0, 0.0, 500, 180),
		):
			push_mouse_wheel(wheel_x, wheel_y, pos_x, pos_y)
			_pump(gui)

		assert "left" in complete.events, complete.events
		assert "right" in complete.events, complete.events

		complete.events.clear()
		partial.events.clear()
		push_finger_pan(touch_id=3, fingers=2, dx=0.03, dy=0.03, steps=4)
		_pump(gui)
		assert complete.events, "no wheel events reached a mouse listener"
		assert "left" not in complete.events, complete.events
		assert "right" not in complete.events, complete.events
	finally:
		_remove_recorders(event_manager, complete, partial)


@gui_test(use_dev_map=True, timeout=60)
def test_finger_events_reach_touch_listener(gui):
	"""Raw finger events are delivered next to the compatibility wheel input."""

	class TouchRecorder(fife.ITouchListener):
		def __init__(self):
			fife.ITouchListener.__init__(self)
			self.downs = 0
			self.motions = 0
			self.ups = 0

		def touchDown(self, evt):
			self.downs += 1

		def touchMotion(self, evt):
			self.motions += 1

		def touchUp(self, evt):
			self.ups += 1

	recorder = TouchRecorder()
	event_manager = horizons.globals.fife.eventmanager
	event_manager.addTouchListenerFront(recorder)
	try:
		push_finger_pan(touch_id=4, fingers=2, dx=0.007, dy=0.05, steps=3)
		_pump(gui)
		assert recorder.downs == 2, recorder.downs
		assert recorder.motions == 6, recorder.motions
		assert recorder.ups == 2, recorder.ups
	finally:
		event_manager.removeTouchListener(recorder)
