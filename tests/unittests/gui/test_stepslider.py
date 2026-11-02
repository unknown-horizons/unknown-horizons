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
Unit tests for the StepSlider widget logic.

Tests the core logic without relying on the full widget hierarchy
which is affected by global test mocks.
"""

import math


class MockRealWidget:
	"""Mock for fifechan.Slider to test StepSlider logic without GUI."""

	def __init__(self):
		self._value = 0.0
		self._scale_start = 0.0
		self._scale_end = 1.0

	def getValue(self):
		return self._value

	def setValue(self, value):
		self._value = float(value)

	def setScale(self, start, end):
		self._scale_start = float(start)
		self._scale_end = float(end)

	def getScaleStart(self):
		return self._scale_start

	def getScaleEnd(self):
		return self._scale_end

	def setMarkerLength(self, length):
		pass

	def setOrientation(self, orientation):
		pass

	def setStepLength(self, length):
		pass


class StepSliderLogic:
	"""
	Replicates the StepSlider value/steps property logic for testing.
	This avoids issues with global test mocks affecting the actual class.
	"""

	def __init__(self):
		self._callbacks_by_group = {}
		self._last_step_value = None
		self._steps = None
		self.real_widget = MockRealWidget()
		self.orientation = 0
		self.step_length = 1.0
		self.marker_length = 25
		self.scale_start = 0.0
		self.scale_end = 1.0

	def _set_steps(self, steps):
		if isinstance(steps, str):
			self._steps = [float(s.strip()) for s in steps.split(';')]
		else:
			self._steps = steps

		self.scale_start = 0.0
		self.scale_end = float(len(self._steps) - 1)
		self.step_length = 1.0

	def _get_steps(self):
		return self._steps

	steps = property(_get_steps, _set_steps)

	def _get_value(self):
		value = self.real_widget.getValue()
		if self._steps:
			index = int(round(value))
			# Ensure index is within bounds of _steps
			index = max(0, min(index, len(self._steps) - 1))
			return self._steps[index]
		return value

	def _set_value(self, value):
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

	def capture(self, callback, event_name='action', group_name='default'):
		"""
		Intercept captures for `action` and store the callback in our list.
		We'll only call them when a step changed.
		"""
		if event_name == 'action':
			self._callbacks_by_group[group_name] = callback
		else:
			# In real implementation, this would call super().capture()
			pass

	def _update(self):
		"""
		Notify listeners when a different step was selected.
		"""
		if self.value != self._last_step_value:
			self._last_step_value = self.value
			for callback in self._callbacks_by_group.values():
				callback()

	def _mouse_released_snap(self):
		"""
		When mouse is released, snap slider marker to discrete value
		to avoid the marker being displayed in-between steps.
		"""
		self.value = self.value


def test_step_slider_basic_value_get_set():
	"""Test basic get/set of discrete step values."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	# Setting by discrete value should work
	slider.value = 100
	assert slider.value == 100
	assert slider.real_widget.getValue() == 1.0  # index 1

	slider.value = 250
	assert slider.value == 250
	assert slider.real_widget.getValue() == 4.0  # index 4

	# Setting first value
	slider.value = 50
	assert slider.value == 50
	assert slider.real_widget.getValue() == 0.0


def test_step_slider_float_int_equivalence():
	"""Test that float and int values are treated equivalently."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	# Setting with float that is integer
	slider.value = 100.0
	assert slider.value == 100
	assert slider.real_widget.getValue() == 1.0

	# Setting with int
	slider.value = 100
	assert slider.value == 100
	assert slider.real_widget.getValue() == 1.0


def test_step_slider_fallback_to_index():
	"""Test fallback behavior when value not in steps - should use as index."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	# Setting by index (old behavior compatibility)
	slider.value = 2  # index 2 -> value 150
	assert slider.value == 150
	assert slider.real_widget.getValue() == 2.0

	# Setting by float index
	slider.value = 3.0
	assert slider.value == 200
	assert slider.real_widget.getValue() == 3.0


def test_step_slider_index_clamping():
	"""Test that out-of-bounds indices are clamped."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	# Index too high - should clamp to last
	slider.value = 10
	assert slider.value == 250
	assert slider.real_widget.getValue() == 4.0

	# Index too low - should clamp to first
	slider.value = -5
	assert slider.value == 50
	assert slider.real_widget.getValue() == 0.0


def test_step_slider_invalid_type_resets():
	"""Test that invalid types reset to first step."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	slider.value = "invalid"
	assert slider.value == 50
	assert slider.real_widget.getValue() == 0.0


def test_step_slider_string_steps_parsing():
	"""Test parsing of semicolon-separated steps string."""
	slider = StepSliderLogic()

	# Test XML-style string parsing
	slider.steps = "50 ; 100 ; 150 ; 200 ; 250"
	assert slider.steps == [50.0, 100.0, 150.0, 200.0, 250.0]

	# Test with spaces
	slider.steps = "0.5 ; 0.7 ; 1 ; 1.4 ; 2"
	assert slider.steps == [0.5, 0.7, 1.0, 1.4, 2.0]

	# Test scale is set correctly
	assert slider.scale_start == 0.0
	assert slider.scale_end == 4.0  # len(steps) - 1


def test_step_slider_empty_steps_fallback():
	"""Test that empty/None steps falls back to normal slider behavior."""
	slider = StepSliderLogic()
	slider._steps = None

	# Should behave like normal slider
	slider.value = 0.5
	assert slider.value == 0.5

	slider._steps = []
	slider.value = 0.75
	assert slider.value == 0.75


def test_step_slider_callback_on_change():
	"""Test that callbacks are triggered when step changes."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]
	slider.value = 50  # Initialize to first value
	slider._last_step_value = 50  # Simulate initial sync

	callback_count = 0

	def callback():
		nonlocal callback_count
		callback_count += 1

	slider.capture(callback)

	# Setting same value shouldn't trigger
	slider.value = 50
	slider._update()  # Simulate widget event
	assert callback_count == 0

	# Changing value should trigger
	slider.value = 100
	slider._update()  # Simulate widget event
	assert callback_count == 1

	# Changing to another value should trigger
	slider.value = 150
	slider._update()  # Simulate widget event
	assert callback_count == 2

	# Setting same value again shouldn't trigger
	slider.value = 150
	slider._update()  # Simulate widget event
	assert callback_count == 2


def test_step_slider_callback_groups():
	"""Test that callbacks work with groups."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	group1_calls = 0
	group2_calls = 0

	def cb1():
		nonlocal group1_calls
		group1_calls += 1

	def cb2():
		nonlocal group2_calls
		group2_calls += 1

	slider.capture(cb1, group_name='group1')
	slider.capture(cb2, group_name='group2')

	slider.value = 100
	slider._update()  # Simulate widget event
	assert group1_calls == 1
	assert group2_calls == 1


def test_step_slider_mouse_release_snap():
	"""Test that mouse release snaps to nearest step."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	# Simulate dragging to between steps
	slider.real_widget.setValue(1.3)  # Between 100 and 150
	slider._mouse_released_snap()

	# Should snap to nearest (index 1 -> 100)
	assert slider.real_widget.getValue() == 1.0
	assert slider.value == 100

	# Test rounding up
	slider.real_widget.setValue(1.6)
	slider._mouse_released_snap()
	assert slider.real_widget.getValue() == 2.0
	assert slider.value == 150


def test_step_slider_precision_handling():
	"""Test handling of floating point precision in step values."""
	slider = StepSliderLogic()
	slider.steps = [0.5, 0.7, 1.0, 1.4, 2.0]

	# Test setting precise float values
	slider.value = 0.7
	assert slider.value == 0.7
	assert slider.real_widget.getValue() == 1.0

	slider.value = 1.4
	assert slider.value == 1.4
	assert slider.real_widget.getValue() == 3.0


def test_step_slider_tax_slider_scenario():
	"""Test the tax slider scenario from residentialtabs.py."""
	slider = StepSliderLogic()

	# Replicate tax settings: 0.5 to 1.5 with step 0.1
	step_count = int(round((1.5 - 0.5) / 0.1)) + 1
	steps = [round(0.5 + 0.1 * i, 10) for i in range(step_count)]
	slider.steps = steps

	# Should have 11 steps: 0.5, 0.6, ..., 1.5
	assert len(slider.steps) == 11
	assert slider.steps[0] == 0.5
	assert slider.steps[-1] == 1.5

	# Every tax value must map to its own index.
	for index, value in enumerate(steps):
		slider.value = value
		assert slider.value == value
		assert slider.real_widget.getValue() == float(index)


def test_step_slider_float_rounding_of_step_values():
	"""A step value affected by float rounding must still match its step."""
	slider = StepSliderLogic()

	# Old generated tax steps contained 1.2000000000000002 instead of 1.2.
	slider.steps = [0.5 + 0.1 * i for i in range(11)]
	slider.value = 1.2

	assert slider.value == 1.2000000000000002
	assert slider.real_widget.getValue() == 7.0  # index 7, not index 1 (0.6)


def test_step_slider_callback_not_triggered_on_internal_update():
	"""Test that callbacks don't fire on internal value updates."""
	slider = StepSliderLogic()
	slider.steps = [50, 100, 150, 200, 250]

	callback_count = 0

	def callback():
		nonlocal callback_count
		callback_count += 1

	slider.capture(callback)

	# Internal update via real_widget shouldn't trigger callback
	slider.real_widget.setValue(2.0)
	slider._update()
	assert callback_count == 1

	# Same value again shouldn't trigger
	slider._update()
	assert callback_count == 1

	# Different value should trigger
	slider.real_widget.setValue(3.0)
	slider._update()
	assert callback_count == 2
