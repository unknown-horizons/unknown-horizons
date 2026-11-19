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

"""Inject real SDL3 input events into the running game.

The GUI tests normally drive ``CursorTool`` directly with mock mouse events.
That cannot reproduce driver- or engine-level bugs, because it bypasses SDL and
FIFE's event translation completely. These helpers push events through
``SDL_PushEvent`` instead, so the real ``EventManager`` path is exercised.

Only the event types needed by the touch/scroll regression tests are modelled.
"""

import ctypes
import ctypes.util
import os
import sys

SDL_EVENT_MOUSE_WHEEL = 0x403
SDL_MOUSEWHEEL_NORMAL = 0
SDL_MOUSEWHEEL_FLIPPED = 1

SDL_EVENT_FINGER_DOWN = 0x700
SDL_EVENT_FINGER_UP = 0x701
SDL_EVENT_FINGER_MOTION = 0x702
SDL_EVENT_FINGER_CANCELED = 0x703

SDL_EVENT_PINCH_BEGIN = 0x710
SDL_EVENT_PINCH_UPDATE = 0x711
SDL_EVENT_PINCH_END = 0x712


class _SDLMouseWheelEvent(ctypes.Structure):
	_fields_ = [
		("type", ctypes.c_uint32),
		("reserved", ctypes.c_uint32),
		("timestamp", ctypes.c_uint64),
		("windowID", ctypes.c_uint32),
		("which", ctypes.c_uint32),
		("x", ctypes.c_float),
		("y", ctypes.c_float),
		("direction", ctypes.c_uint32),
		("mouse_x", ctypes.c_float),
		("mouse_y", ctypes.c_float),
		("integer_x", ctypes.c_int32),
		("integer_y", ctypes.c_int32),
	]


class _SDLTouchFingerEvent(ctypes.Structure):
	_fields_ = [
		("type", ctypes.c_uint32),
		("reserved", ctypes.c_uint32),
		("timestamp", ctypes.c_uint64),
		("touchID", ctypes.c_uint64),
		("fingerID", ctypes.c_uint64),
		("x", ctypes.c_float),
		("y", ctypes.c_float),
		("dx", ctypes.c_float),
		("dy", ctypes.c_float),
		("pressure", ctypes.c_float),
		("windowID", ctypes.c_uint32),
	]


class _SDLPinchFingerEvent(ctypes.Structure):
	_fields_ = [
		("type", ctypes.c_uint32),
		("reserved", ctypes.c_uint32),
		("timestamp", ctypes.c_uint64),
		("scale", ctypes.c_float),
		("windowID", ctypes.c_uint32),
	]


class _SDL_Event(ctypes.Union):
	_fields_ = [
		("type", ctypes.c_uint32),
		("wheel", _SDLMouseWheelEvent),
		("tfinger", _SDLTouchFingerEvent),
		("pinch", _SDLPinchFingerEvent),
		("padding", ctypes.c_uint8 * 128),
	]


class SDLInputUnavailable(RuntimeError):
	"""Raised when SDL_PushEvent cannot be reached from this process."""


_push_event = None


def _find_loaded_library():
	"""Return the path of the library that exports SDL_PushEvent."""
	if sys.platform.startswith("linux"):
		try:
			with open("/proc/self/maps", encoding="ascii", errors="ignore") as maps:
				for line in maps:
					fields = line.split()
					if len(fields) < 6:
						continue
					path = fields[-1]
					if "fifengine" in os.path.basename(path) and os.path.exists(path):
						return path
		except OSError:
			pass
	elif sys.platform == "win32":
		return "SDL3.dll"
	elif sys.platform == "darwin":
		return ctypes.util.find_library("SDL3") or "libSDL3.dylib"
	return None


def _get_push_event():
	global _push_event
	if _push_event is not None:
		return _push_event

	library_path = _find_loaded_library()
	if library_path is None:
		raise SDLInputUnavailable("cannot locate libfifengine/SDL3 in this process")

	try:
		library = ctypes.CDLL(library_path)
		push_event = library.SDL_PushEvent
	except (OSError, AttributeError) as exc:
		raise SDLInputUnavailable(f"SDL_PushEvent is not exported by {library_path}") from exc

	push_event.argtypes = [ctypes.POINTER(_SDL_Event)]
	push_event.restype = ctypes.c_bool
	_push_event = push_event
	return push_event


def push_event(event, description):
	"""Push a prepared event into SDL's queue.

	Raises:
		SDLInputUnavailable: if SDL cannot be reached.
		RuntimeError: if SDL rejects the event.
	"""
	if not _get_push_event()(ctypes.byref(event)):
		raise RuntimeError(f"SDL_PushEvent rejected the synthetic {description} event")


def push_mouse_wheel(x, y, mouse_x, mouse_y, flipped=False):
	"""Push a real SDL_EVENT_MOUSE_WHEEL at the given window coordinates.

	``x``/``y`` use SDL's convention: positive x is right, positive y is up.
	"""
	event = _SDL_Event()
	event.wheel.type = SDL_EVENT_MOUSE_WHEEL
	event.wheel.x = x
	event.wheel.y = y
	event.wheel.direction = SDL_MOUSEWHEEL_FLIPPED if flipped else SDL_MOUSEWHEEL_NORMAL
	event.wheel.mouse_x = mouse_x
	event.wheel.mouse_y = mouse_y
	push_event(event, "mouse wheel")


def push_finger(event_type, touch_id, finger_id, x, y, dx=0.0, dy=0.0, pressure=0.5):
	"""Push a real SDL_EVENT_FINGER_* event.

	``x``/``y`` are normalized window coordinates in 0..1.
	"""
	event = _SDL_Event()
	event.tfinger.type = event_type
	event.tfinger.touchID = touch_id
	event.tfinger.fingerID = finger_id
	event.tfinger.x = x
	event.tfinger.y = y
	event.tfinger.dx = dx
	event.tfinger.dy = dy
	event.tfinger.pressure = pressure
	push_event(event, "finger")


def push_finger_pan(
	touch_id,
	fingers,
	dx,
	dy,
	steps,
	start_x=0.4,
	start_y=0.4,
	spacing=0.1,
):
	"""Push a complete two-finger (or N-finger) pan gesture.

	Every finger is placed on a horizontal line and moved by ``dx``/``dy`` per
	step. The finger states are converted to DOWN, MOTION, and UP events.
	"""
	finger_ids = [touch_id * 100 + index for index in range(fingers)]
	last_positions = []

	for index, finger_id in enumerate(finger_ids):
		x = start_x + index * spacing
		y = start_y + index * spacing
		last_positions.append([x, y])
		push_finger(SDL_EVENT_FINGER_DOWN, touch_id, finger_id, x, y)

	for _ in range(steps):
		for index, finger_id in enumerate(finger_ids):
			x, y = last_positions[index]
			x += dx
			y += dy
			# Fingers cannot leave the normalized window area.
			x = min(max(x, 0.0), 1.0)
			y = min(max(y, 0.0), 1.0)
			last_positions[index] = [x, y]
			push_finger(SDL_EVENT_FINGER_MOTION, touch_id, finger_id, x, y, dx=dx, dy=dy)

	for index, finger_id in enumerate(finger_ids):
		x, y = last_positions[index]
		push_finger(SDL_EVENT_FINGER_UP, touch_id, finger_id, x, y)


def push_pinch(event_type, scale):
	"""Push a real SDL_EVENT_PINCH_* event."""
	event = _SDL_Event()
	event.pinch.type = event_type
	event.pinch.scale = scale
	push_event(event, "pinch")
