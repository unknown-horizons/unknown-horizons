# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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
	def __init__(self, amount, base_path, start_img, tile_img, end_img, **kwargs):
		super(TilingBackground, self).__init__()
		# Note: Don't set the tile amount in the constructor,
		# as it will not layout correctly, blame pychan for it :-)
		self.__tile_amount = amount
		self.start_img = base_path + start_img
		self.tile_img = base_path + tile_img
		self.end_img = base_path + end_img

	def _get_tile_amount(self):
		return self.__tile_amount

	def _set_tile_amount(self, amount):
		if amount == self.__tile_amount and amount > 0:
			# Default amount of 0 should still add top/bottom graphics once
			return
		self.__tile_amount = amount
		self.removeAllChildren()
		start_img = Icon(image=self.start_img, name=self.name + '0')
		self.addChild(start_img)
		for i in xrange(self.amount):
			mid = Icon(image=self.tile_img, name=self.name + str(i+1))
			self.addChild(mid)
		self.addChild(Icon(image=self.end_img, name=self.name + str(self.amount+1)))

	amount = property(_get_tile_amount, _set_tile_amount)


class TooltipBG(VBox):
	""" Don't look at me like this... """
	def __init__(self):
		super(TooltipBG, self).__init__(name='tooltip_background', padding=0)
		path = 'content/gui/images/background/tooltip/%s_%s.png'
		self.tiles = {
			'top': {
				'start_img': path % ('top', 'left'),
				'tile_img': path % ('top', 'mid'),
				'end_img': path % ('top', 'right'),
			},
			'mid': {
				'start_img': path % ('mid', 'left'),
				'tile_img': path % ('mid', 'mid'),
				'end_img': path % ('mid', 'right'),
			},
			'bot': {
				'start_img': path % ('bot', 'left'),
				'tile_img': path % ('bot', 'mid'),
				'end_img': path % ('bot', 'right'),
			},
		}
		# Remember that we inherit from VBox, so these
		# can not be called "width" and "height".
		self.height_tiles = 0
		# For compat: this is 40px steps, old width was 125.
		self.width_tiles = 3

	def _add_tiles(self, widget, how_many_tiles, start_img, tile_img, end_img):
		first = Icon(image=start_img)
		widget.addChild(first)
		for i in xrange(how_many_tiles):
			mid = Icon(image=tile_img)
			widget.addChild(mid)
		last = Icon(image=end_img)
		widget.addChild(last)

	def relayout(self):
		self.removeAllChildren()
		# Top row
		box = HBox(padding=0)
		self._add_tiles(box, self.width_tiles, **self.tiles['top'])
		self.addChild(box)

		# Middle rows (tiling)
		for i in xrange(self.height_tiles):
			box = HBox(padding=0)
			self._add_tiles(box, self.width_tiles, **self.tiles['mid'])
			self.addChild(box)

		# Bottom row
		box = HBox(padding=0)
		self._add_tiles(box, self.width_tiles, **self.tiles['bot'])
		self.addChild(box)


class TabBG(VBox, TilingBackground):
	"""Intended to be used for any tab we display.
	Uses content/gui/images/tabwidget/main_bg_*.png.
	@param amount: amount of 50px tiles/panels in between top and bottom icon
	"""
	ATTRIBUTES = VBox.ATTRIBUTES + [IntAttr('amount')]
	def __init__(self, **kwargs):
		VBox.__init__(self, name='tab_background_icons', padding=0)
		TilingBackground.__init__(self,
			amount=0,
			base_path="content/gui/images/tabwidget/main_bg_",
			start_img="top.png", tile_img="fill.png", end_img="bottom.png",
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
			amount=0,
			base_path="content/gui/images/background/widgets/cityinfo_",
			start_img="left.png", tile_img="fill.png", end_img="right.png",
			**kwargs)


class hr(Icon):
	def __init__(self, **kwargs):
		super(hr, self).__init__(image="content/gui/images/background/hr.png", **kwargs)
