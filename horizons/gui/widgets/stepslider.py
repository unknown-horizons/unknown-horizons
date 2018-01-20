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

from fife.extensions.pychan.attrs import IntAttr, UnicodeAttr
from fife.extensions.pychan.widgets import Slider, Widget


class StepSlider(Slider):
	"""The StepSlider automatically snaps the steps suggested by stepsize."""

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
		When mouse is released, snap slider marker to discrete value to avoid the marker
		being displayed in-between steps.
		"""
		# Retrieve the value of the step that is closest to marker's current position
		# (`_get_value`), and set that value on the slider to move the marker (`_set_value`).
		self.value = self.value

	def capture(self, callback, event_name='action', group_name='default'):
		"""
		Intercept captures for `action` and store the callback in our list. We'll only
		call them when a step changed.
		"""
		if event_name == 'action':
			self._callbacks_by_group[group_name] = callback
		else:
			super().capture(callback, event_name, group_name)

	def _update(self):
		"""
		Notify listeners when a different step was selected.
		"""
		if self.value != self._last_step_value:
			self._last_step_value = self.value
			for callback in self._callbacks_by_group.values():
				callback()

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
		value = int(round(self.real_widget.getValue()))
		return self._steps[value]

	def _set_value(self, value):
		try:
			value = float(self._steps.index(value))
		except ValueError:
			# Invalid value, probably a value before the changes to stepslider.
			# The values of affected step sliders used to be in [0, N], where N is the
			# number of steps, so we use the value as index.
			try:
				value = self._steps[int(value)]
			except IndexError:
				# If that didn't work, reset the slider.
				value = self._steps[0]

		self.real_widget.setValue(value)

	value = property(_get_value, _set_value)
