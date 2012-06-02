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


from fife.extensions import pychan


class StepSlider(pychan.widgets.Slider):

	def __init__(self, *args, **kwargs):
		"""The StepSlider automatically snaps the steps suggested by stepsize."""
		self.__callbacks_by_group = {} # super init calls capture, so we need this here

		super(StepSlider, self).__init__(*args, **kwargs)

		self.__last_step_value = None # for recognising new steps, self.value is overwritten in the base class sometimes
		self.capture(None)

	def capture(self, callback, event_name="action", group_name="default"):
		if event_name == "action":
			super(StepSlider, self).capture(self.__update, event_name, group_name="stepslider")
			self.__callbacks_by_group[group_name] = callback
		else:
			super(StepSlider, self).capture(callback, event_name, group_name)

	def __update(self):
		value = round(self.value / self.step_length) * self.step_length
		if value != self.__last_step_value:
			self.__last_step_value = value
			self.value = value # has be overwritten before this has been called
			for callback in self.__callbacks_by_group.itervalues():
				callback()