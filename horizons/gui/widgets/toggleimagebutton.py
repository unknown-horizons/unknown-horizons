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
from fife.extensions.pychan.widgets.common import Attr, UnicodeAttr


class ToggleImageButton(pychan.widgets.ImageButton):
	"""The ToggleImageButton is an extended ImageButton (Think decorator pattern).
	It adds one extra attribute inactive_image. You can then set the button active
	or inactive (only in code for now). Setting the ToggleImageButton to inactive
	will change all images (up, down and hover) to the inactive image. If you
	set it active again, everything will be reset.

	@param inactive_image The image that is to be used as inactive image.
	"""

	ATTRIBUTES = pychan.widgets.ImageButton.ATTRIBUTES + [Attr('inactive_image')]

	# These two constants are used to describe the state of the widget.
	ACTIVE = 0
	INACTIVE = 1

	def __init__(self, inactive_image = "", **kwargs):
		self.state = None
		super(ToggleImageButton, self).__init__(**kwargs)
		self.state = self.ACTIVE
		self.inactive_image = inactive_image

	def toggle(self):
		if self.state == self.ACTIVE:
			self.set_inactive()
		else:
			self.set_active()

	def set_active(self):
		"""Sets the button active. Restores up, down and hover image to
		previous state."""
		if self.state != self.ACTIVE:
			self.up_image, self.down_image, self.hover_image = self.old_images
			self.state = self.ACTIVE

	def set_inactive(self):
		"""Sets the button inactive. Overrides up, down and hover image with
		inactive image."""
		if self.state != self.INACTIVE:
			self.old_images = (self.up_image, self.down_image, self.hover_image)
			self.up_image = self.inactive_image
			self.down_image = self.inactive_image
			self.hover_image = self.inactive_image
			self.state = self.INACTIVE

	def _get_inactive_image(self):
		return self.__inactiveimage

	def _set_inactive_image(self, inactive_image):
		self.__inactiveimage = inactive_image

	inactive_image = property(_get_inactive_image, _set_inactive_image)

