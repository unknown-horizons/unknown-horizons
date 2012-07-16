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

from fife.extensions.pychan.widgets import ImageButton

from horizons.util import Callback
from horizons.gui.util import get_res_icon_path

class ImageFillStatusButton(pychan.widgets.Container):

	CELL_SIZE = (54, 50) # 32x32 icon, fillbar to the right, label below, padding

	def __init__(self, up_image, down_image, hover_image, text, res_id, helptext="",
	             filled=0, uncached=False, **kwargs):
		"""Represents the image in the ingame gui, with a bar to show how full the inventory is for that resource
		Derives from pychan.widgets.Container, but also takes the args of the pychan.widgets.Imagebutton,
		in order to display the image. The container is only used, because ImageButtons can't have children.
		This is meant to be used with the Inventory widget."""
		super(ImageFillStatusButton, self).__init__(**kwargs)
		self.up_image, self.down_image, self.hover_image, self.text = up_image, down_image, hover_image, text
		self.helptext = _(helptext)
		# res_id is used by the TradeTab for example to determine the resource this button represents
		self.res_id = res_id
		self.text_position = (9, 30)
		self.uncached = uncached # force no cache. needed when the same icon has to appear several times at the same time
		self.filled = filled # <- black magic at work! this calls _draw()

	@classmethod
	def init_for_res(cls, db, res, amount=0, filled=0, use_inactive_icon=True, uncached=False):
		"""Inites the button to display the icons for res
		@param db: dbreader to get info about res icon.
		@param res: resource id
		@param amount: int amount of res (used to decide inactiveness and as text)
		@param filled: percent of fill status (values are ints in [0, 100])
		@param use_inactive_icon: whether to use inactive icon if amount == 0
		@param uncached: force no cache. see __init__()
		@return: ImageFillStatusButton instance"""
		greyscale = use_inactive_icon and amount == 0
		image = get_res_icon_path(res, 32, greyscale)
		helptext = db.get_res_name(res)
		return cls(up_image=image, down_image=image, hover_image=image,
		           text=unicode(amount),
		           helptext=helptext,
		           size=cls.CELL_SIZE,
		           res_id=res,
		           filled=filled,
		           uncached=uncached)

	def _set_filled(self, percent):
		""""@param percent: int percent that fillstatus will be green"""
		self._filled = percent
		self._draw()

	def _get_filled(self):
		return self._filled

	filled = property(_get_filled, _set_filled)

	__widget_cache = {}
	def _draw(self):
		"""Draws the icon + bar."""
		# hash buttons by creation function call
		# NOTE: there may be problems with multiple buttons with the same
		# images and helptext at the same time
		create_btn = Callback(ImageButton, up_image=self.up_image,
		                      down_image=self.down_image, hover_image=self.hover_image,
		                      helptext=self.helptext)
		self.button = None
		if self.uncached:
			self.button = create_btn()
		else:
			self.button = self.__widget_cache.get(create_btn, None)
			if self.button is None: # create button
				self.__widget_cache[create_btn] = self.button = create_btn()
			else: # disconnect button from earlier layout
				if self.button.parent:
					self.button.parent.removeChild(self.button)

		# can't cache the other instances, because we need multiple instances
		# with the same data active at the same time
		self.label = pychan.widgets.Label(text=self.text)
		self.label.position = self.text_position
		self.fill_bar = pychan.widgets.Icon(image="content/gui/images/tabwidget/green_line.png")
		fill_level = (self.button.height * self.filled) // 100
		self.fill_bar.size = ((2 * self.fill_bar.size[0]) // 3, fill_level)
		# move fillbar down after resizing, since its origin is top aligned
		self.fill_bar.position = (self.button.width, self.button.height - fill_level)
		self.addChildren(self.button, self.fill_bar, self.label)
