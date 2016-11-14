# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from fife.extensions.pychan.widgets import Icon, ImageButton as FifeImageButton
from fife.extensions.pychan.widgets.common import Attr


class ImageButton(FifeImageButton):
	"""Extends ImageButton functionality by providing a new path= attribute.
	Unless manually overridden, specifying path="path/to/file" (note: no .png
	extension) will interpret that as these attributes:

	      up_image = "content/gui/path/to/file.png"
	    down_image = "content/gui/path/to/file_d.png"
	   hover_image = "content/gui/path/to/file_h.png"
	inactive_image = "content/gui/path/to/file_bw.png" ("black/white")

	Other possible names also checked are
	      up_image = "content/gui/path/to/file_u.png" ("up", for tabwidget)
	inactive_image = "content/gui/path/to/file_gr.png" ("grayscale")

	If some of those files could not be found, we use up_image instead.
	Sets is_focusable to False unless overridden.

	You can set the button active or inactive (only in code for now).
	Setting to inactive will change *all* images (up, down and hover) to the
	inactive image. If you set it active again, everything will be reset.
	"""
	ATTRIBUTES = FifeImageButton.ATTRIBUTES + [Attr('path'), Attr('inactive_image')]
	IMAGE = "content/gui/{path}{{mode}}.png"
	# These two constants are used to describe the toggle state of the widget.
	ACTIVE = 0
	INACTIVE = 1

	def __init__(self, path='', inactive_image=None, is_focusable=False, **kwargs):
		super(ImageButton, self).__init__(is_focusable=is_focusable, **kwargs)
		self.old_images = (None, None, None)
		if path:
			# initializing from python, not xml, so path is available here
			# and should be set
			self.path = path
		if inactive_image:
			self.inactive_image = inactive_image
		self.state = self.ACTIVE

	def toggle(self):
		if self.is_active:
			self.set_inactive()
		else:
			self.set_active()

	def set_active(self):
		"""Sets the button active. Restores up, down and hover image to
		previous state."""
		if self.is_active:
			return
		self.up_image, self.down_image, self.hover_image = self.old_images
		self.state = self.ACTIVE

	def set_inactive(self):
		"""Sets the button inactive. Overrides up, down and hover image with
		inactive image."""
		if not self.is_active:
			# running this with inactive state would overwrite all elements
			# of old_images with inactive_image
			return
		# store old images to be reloaded when button is set active again
		self.old_images = (self.up_image, self.down_image, self.hover_image)
		self.up_image = self.down_image = self.hover_image = self.inactive_image
		self.state = self.INACTIVE

	@property
	def is_active(self):
		return (self.state == self.ACTIVE)

	def _get_path(self):
		return self.__path

	def _set_path(self, path):
		self.__path = path
		image_path = self.IMAGE.format(path=path)
		try:
			self.up_image = image_path.format(mode='')
		except RuntimeError:
			# RuntimeError: _[NotFound]_ , Something was searched, but not found
			#TODO Temporarily try to find _u for the tabwidget
			self.up_image = image_path.format(mode='_u')
		try:
			self.hover_image = image_path.format(mode='_h')
		except RuntimeError:
			# By default, guichan/pychan will set hover_image to be the same as
			# up_image even if it is not explicitly set here (the following line
			# just reading `pass` instead of setting hover_image to up_image).
			# This however is stored internally in a way that would segfault FIFE
			# when trying to restore images from self.old_images that were set
			# like that implicitly (see #2000).
			self.hover_image = self.up_image
		try:
			self.down_image = image_path.format(mode='_d')
		except RuntimeError:
			self.down_image = self.up_image

		# Since inactive_image is no image attribute in pychan, it would
		# not be validated upon setting self.inactive_image (which works
		# for ImageButton.{up,down,hover}_image and Icon.image).
		# Instead, we try to load an Icon with that image and manually
		# set inactive_image to the path that worked, if there is any.
		try:
			image = image_path.format(mode='_bw')
			Icon(image=image).hide() # hide will remove Icon from widgets of pychan.internals.manager
			self.inactive_image = image
		except RuntimeError:
			try:
				image = image_path.format(mode='_gr')
				Icon(image=image).hide() # hide will remove Icon from widgets of pychan.internals.manager
				self.inactive_image = image
			except RuntimeError:
				self.inactive_image = self.up_image

	path = property(_get_path, _set_path)


class OkButton(ImageButton):
	"""The OkButton is a shortcut for an ImageButton with our OK / apply icon.
	Its default attributes are:
	name="okButton" path="images/buttons/ok"
	"""
	DEFAULT_NAME = 'okButton'
	def __init__(self, name=None, **kwargs):
		if name is None:
			name = self.__class__.DEFAULT_NAME
		size = (34, 40)
		super(OkButton, self).__init__(
			name=name, is_focusable=False,
			max_size=size, min_size=size, size=size, **kwargs)
		self.path = "images/buttons/ok"
		self.inactive_image = "content/gui/images/buttons/close.png"

class CancelButton(ImageButton):
	"""The CancelButton is a shortcut for an ImageButton with our cancel / close
	icon. Its default attributes are:
	name="cancelButton" path="images/buttons/close"
	"""
	DEFAULT_NAME = 'cancelButton'
	def __init__(self, name=None, **kwargs):
		if name is None:
			name = self.__class__.DEFAULT_NAME
		size = (34, 40)
		super(CancelButton, self).__init__(
			name=name, is_focusable=False,
			max_size=size, min_size=size, size=size, **kwargs)
		self.path = "images/buttons/close"

class DeleteButton(ImageButton):
	"""The DeleteButton is a shortcut for an ImageButton with our delete / tear
	icon. Its default attributes are:
	name="deleteButton" path="images/buttons/delete"
	"""
	DEFAULT_NAME = 'deleteButton'
	def __init__(self, name=None, **kwargs):
		if name is None:
			name = self.__class__.DEFAULT_NAME
		size = (34, 40)
		super(DeleteButton, self).__init__(
			name=name, is_focusable=False,
			max_size=size, min_size=size, size=size, **kwargs)
		self.path = "images/buttons/delete"


class MainmenuButton(ImageButton):
	"""For use in main menu. bw: whether to use greyscale or color."""

	ATTRIBUTES = ImageButton.ATTRIBUTES + [Attr('icon')]
	ICON = "content/gui/icons/mainmenu/{icon}{bw}.png"

	def __init__(self, icon='door', **kwargs):
		super(MainmenuButton, self).__init__(is_focusable=False, **kwargs)
		self.icon = icon

	def _get_icon(self):
		return self.__icon

	def _set_icon(self, icon):
		self.__icon = icon
		self.up_image = self.ICON.format(icon=icon, bw='_bw')
		self.hover_image = self.down_image = self.ICON.format(icon=icon, bw='')

	icon = property(_get_icon, _set_icon)
