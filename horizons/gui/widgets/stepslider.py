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

import math

from fife.extensions.pychan.attrs import IntAttr, UnicodeAttr
from fife.extensions.pychan.widgets import Slider, Widget


class StepSlider(Slider):
	"""
	A slider widget that snaps to discrete step values.

	The StepSlider accepts a list of discrete step values (via the `steps`
	attribute) and ensures the slider marker only rests on those values.

	Value Property
	----------------
	- Getting `slider.value` returns the *discrete step value* (e.g., 100, 150)
	  not the internal index.
	- Setting `slider.value = 150` finds the matching step and moves the marker.
	- Setting `slider.value = 2` (an index) falls back to index-based positioning
	  for backward compatibility.

	Steps Attribute
	-----------------
	Can be set as a list: `slider.steps = [50, 100, 150, 200, 250]`
	Or as a semicolon-separated string (for XML): `slider.steps = "50 ; 100 ; 150 ; 200 ; 250"`

	Callbacks
	-----------
	Use `slider.capture(callback)` to register a callback that fires when the
	discrete step changes. Callbacks are only triggered when the actual step
	value changes, not on every internal widget update.

	Example
	-------
		slider = StepSlider()
		slider.steps = [0.5, 0.7, 1.0, 1.4, 2.0]
		slider.value = 1.0  # Sets to third step (index 2)
		print(slider.value)  # Prints 1.0
	"""

	ATTRIBUTES = Widget.ATTRIBUTES + [
		IntAttr('orientation'),
		IntAttr('marker_length'),
		UnicodeAttr('steps')]

	def __init__(self, *args, **kwargs):
		self._callbacks_by_group = {} # super init calls capture, so we need this here

		super().__init__(*args, **kwargs)

		self._last_step_value = None # for recognizing new steps, self.value is overwritten in the base class sometimes
		self._steps = None

		super().capture(self._update, 'action', 'stepslider')
		super().capture(self._mouse_released_snap, 'mouseReleased', 'stepslider')

	def _mouse_released_snap(self):
		"""
		When mouse is released, snap slider marker to the nearest discrete step
		to avoid the marker being displayed in-between steps.
		"""
		# Retrieve the value of the step that is closest to marker's current position
		# (`_get_value`), and set that value on the slider to move the marker (`_set_value`).
		self.value = self.value

	def capture(self, callback, event_name='action', group_name='default'):
		"""
		Register a callback for slider events.

		For `action` events (discrete step changes), the callback is stored and
		called only when the step value actually changes (see `_update`).
		Other event types are passed to the parent implementation.

		Args:
			callback: Function to call when event occurs.
			event_name: Event type ('action' for step changes).
			group_name: Callback group name (default: 'default').
		"""
		if event_name == 'action':
			self._callbacks_by_group[group_name] = callback
		else:
			super().capture(callback, event_name, group_name)

	def _update(self):
		"""
		Notify registered callbacks when a different discrete step is selected.

		This is called internally when the underlying widget fires an 'action' event.
		It compares the current step value with the last reported step value and
		only calls callbacks if the step actually changed.
		"""
		if self.value != self._last_step_value:
			self._last_step_value = self.value
			for callback in self._callbacks_by_group.values():
				callback()

	def _set_steps(self, steps):
		"""
		Set the discrete step values for this slider.

		Args:
			steps: Either a list of numeric values [50, 100, 150]
				   or a semicolon-separated string "50 ; 100 ; 150" (for XML).
		"""
		if isinstance(steps, str):
			self._steps = [float(s.strip()) for s in steps.split(';')]
		else:
			self._steps = steps

		# Configure the underlying widget to use indices as its scale
		self.scale_start = 0.0
		self.scale_end = float(len(self._steps) - 1)
		self.step_length = 1.0

	def _get_steps(self):
		"""Return the list of discrete step values."""
		return self._steps

	steps = property(_get_steps, _set_steps)

	def _get_value(self):
		"""
		Get the current discrete step value.

		Returns:
			The step value (e.g., 100, 150) corresponding to the marker's position,
			or the raw widget value if no steps are defined.
		"""
		value = self.real_widget.getValue()
		if self._steps:
			index = int(round(value))
			# Ensure index is within bounds of _steps
			index = max(0, min(index, len(self._steps) - 1))
			return self._steps[index]
		return value

	def _set_value(self, value):
		"""
		Set the slider to a specific discrete step value or index.

		Args:
			value: Either a step value from the steps list (e.g., 100),
				   or an integer index (e.g., 1 for the second step).

		Behavior:
			- If value matches a step, moves marker to that step.
			- If value is close to a step (float rounding), moves to that step.
			- If value is an integer index, moves marker to that index.
			- If value is out of bounds, clamps to nearest valid step.
			- If value is invalid type, resets to first step.
			- If no steps defined, behaves like a normal continuous slider.
		"""
		try:
			value = float(value)
		except (TypeError, ValueError):
			# If all else fails, reset to first step
			value = 0.0

		if not self._steps:
			self.real_widget.setValue(value)
			return

		try:
			index = self._steps.index(value)
		except ValueError:
			# The value may differ from a step only because of floating point
			# rounding (e.g. 1.2 vs 1.2000000000000002).
			index = next(
				(i for i, step in enumerate(self._steps)
				 if math.isclose(step, value, rel_tol=1e-9, abs_tol=1e-9)),
				None,
			)
			if index is None:
				if value.is_integer():
					# Old behavior: values used to be indices in [0, N], so
					# clamp them to the valid index range.
					index = max(0, min(int(value), len(self._steps) - 1))
				else:
					# Snap a raw value to the nearest discrete step.
					index = min(
						range(len(self._steps)),
						key=lambda i: abs(self._steps[i] - value),
					)

		self.real_widget.setValue(float(index))

	value = property(_get_value, _set_value)
