# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

	def __init__(self, **kwargs):
		"""Represents the image in the ingame gui, with a bar to show how full the inventory is for that resource
		Derives from pychan.widgets.Container, but also takes the args of the pychan.widgets.Imagebutton,
		in order to display the image. The container is only used, because ImageButtons can't have children.
		This is meant to be used with the Inventory widget."""
		super(StepSlider, self).__init__(**kwargs)
		self.__callback = None
		self.capture(None)

	def capture(self, callback, **kwargs):
		super(StepSlider, self).capture(self.__update, **kwargs)
		self.__callback = callback

	def __update(self):
		value = round( self.getValue() / self.getStepLength()) * self.getStepLength()
		self.setValue(value)
		if self.__callback is not None:
			self.__callback()
