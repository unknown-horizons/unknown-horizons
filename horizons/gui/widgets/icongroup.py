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
from fife.extensions.pychan.widgets.common import IntAttr

from horizons.gui.widgets.tooltip import TooltipIcon

class TabBG(pychan.widgets.VBox):
	"""The TabBG is a shortcut for several TooltipIcons combined to one group.
	Intended to be used for any tab we display.
	Uses content/gui/images/tabwidget/main_bg_*.png. Default attributes are:
	name="background_icons"
	amount="0"
	padding="0"
	border_size="0"

	@param amount: amount of 50px tiles in between top and bottom icon
	"""
	ATTRIBUTES = pychan.widgets.VBox.ATTRIBUTES + [IntAttr('amount')]
	def __init__(self, amount = 0, **kwargs):
		self.amount = amount
		print " self %s" % self.amount
		super(TabBG, self).__init__(
			name='background_icons',
			padding=0,
			border_size=0,
			**kwargs)
		header_path = "content/gui/images/tabwidget/main_bg_top.png"
		mid_path = "content/gui/images/tabwidget/main_bg_fill.png"
		footer_path = "content/gui/images/tabwidget/main_bg_bottom.png"
		self.addChild(TooltipIcon(image=header_path, name='background_icon_' + '0'))
		print " amount = %s" % self.amount
		for i in xrange(0,self.amount):
			print " i = %s" % i
			mid = TooltipIcon(image=mid_path, name='background_icon_' + unicode(i+1))
			self.addChild(mid)
		self.addChild(TooltipIcon(image=footer_path, name='background_icon_' + unicode(self.amount+1)))
		print self.children
