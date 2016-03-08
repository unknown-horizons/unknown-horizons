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

from fife.extensions.pychan.widgets import HBox, Icon, VBox
from fife.extensions.pychan.widgets.common import IntAttr

class TilingBackground(object):
	"""The TilingBackground is a shortcut for several Icons combined to one group.
	It usually serves as auxiliary widget if a tiling background image is desired,
	but the layout also requires some kind of border around those tiling panels.
	Default attributes are set in the widgets inheriting from TilingBackground.
	"""
	def __init__(self, x_width_amount, y_tile_amount, base_path, start_img, tiles_img, final_img, **kwargs):
		super(TilingBackground, self).__init__()
		# Note: Don't set the tile amount in the constructor,
		# as it will not layout correctly, blame pychan for it :-)
		self.__x_width_amount = x_width_amount
		self.__y_tile_amount = y_tile_amount
		self.start_img = base_path + start_img
		self.tiles_img = base_path + tiles_img
		self.final_img = base_path + final_img
		self._make_background()

	def _get_x_width_amount(self):
		return self.__x_width_amount

	def _get_y_tile_amount(self):
		return self.__y_tile_amount

	def _set_x_width_amount(self, x_width_amount):
		self.__x_width_amount = x_width_amount
		self._make_background()
		return

	def _set_y_tile_amount(self, y_tile_amount):
		if y_tile_amount == self.__y_tile_amount and y_tile_amount > 0:
			# Default amount of 0 should still add top/bottom graphics once
			self._make_background()
			return
		self.__y_tile_amount = y_tile_amount
		self._make_background()
		return

	# load the image to an icon, scale it to x_width, attach it to the vBox, move to the next image and so forth
	def _make_background(self):
		self.removeAllChildren()
		start_img = Icon(image=self.start_img, name=self.name + '0')
		start_img.width = self.__x_width_amount
		self.addChild(start_img)
		for i in xrange(self.__y_tile_amount):
			mid = Icon(image=self.tiles_img, name=self.name + str(i+1))
			mid.width = self.__x_width_amount
			self.addChild(mid)
		final_img = Icon(image=self.final_img, name=self.name + str(self.__y_tile_amount+1))
		final_img.width = self.__x_width_amount
		self.addChild(final_img)

	amount = property(_get_y_tile_amount, _set_y_tile_amount)
	x_width_amount = property(_get_x_width_amount,_set_x_width_amount)

class TooltipBG(VBox, TilingBackground):
	"""Not usable from xml!"""
	def __init__(self, **kwargs):
		VBox.__init__(self, name='tooltip_background', padding=0)
		TilingBackground.__init__(self,
			x_width_amount=0,
			y_tile_amount=0,
			base_path="content/gui/images/background/widgets/tooltip_bg_",
			start_img="top.png", tiles_img="middle.png", final_img="bottom.png",
			**kwargs)

class TabBG(VBox, TilingBackground):
	"""Intended to be used for any tab we display.
	Uses content/gui/images/tabwidget/main_bg_*.png.
	@param amount: amount of 50px tiles/panels in between top and bottom icon
	"""
	ATTRIBUTES = VBox.ATTRIBUTES + [IntAttr('amount')]
	def __init__(self, **kwargs):
		VBox.__init__(self, name='tab_background_icons', padding=0)
		TilingBackground.__init__(self,
			# quite a hack here as the x_width is not set anywhere. Should eventually be set in the xml
			x_width_amount=251,
			y_tile_amount=0,
			base_path="content/gui/images/tabwidget/main_bg_",
			start_img="top.png", tiles_img="fill.png", final_img="bottom.png",
			**kwargs)

class TilingHBox(HBox, TilingBackground):
	"""Currently mostly used by cityinfo, thus using its arguments as defaults.

	Another use case is the TilingProgressBar.
	@param amount: amount of 10px tiles/panels in between left and right icon
	"""
	ATTRIBUTES = HBox.ATTRIBUTES + [IntAttr('amount')]
	def __init__(self, **kwargs):
		HBox.__init__(self, name='city_info_background', padding=0)
		TilingBackground.__init__(self,
			# quite a hack here as the x_width is not set anywhere. Should eventually be set in the xml
			x_width_amount=10,
			y_tile_amount=0,
			base_path="content/gui/images/background/widgets/cityinfo_",
			start_img="left.png", tiles_img="fill.png", final_img="right.png",
			**kwargs)


class hr(Icon):
	def __init__(self, **kwargs):
		super(hr, self).__init__(image="content/gui/images/background/hr.png", **kwargs)
