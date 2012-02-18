# -*- coding: utf-8 -*-
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
from horizons.gui.style import STYLES

def init_pychan():
	"""General pychan initiation for uh"""

	# register custom widgets

	from horizons.gui.widgets.inventory import Inventory
	from horizons.gui.widgets.buysellinventory import BuySellInventory
	from horizons.gui.widgets.imagefillstatusbutton import  ImageFillStatusButton
	from horizons.gui.widgets.progressbar import ProgressBar
	from horizons.gui.widgets.toggleimagebutton import ToggleImageButton
	from horizons.gui.widgets.tooltip import TooltipIcon, TooltipButton, TooltipLabel, TooltipProgressBar
	from horizons.gui.widgets.imagebutton import CancelButton, DeleteButton, OkButton
	from horizons.gui.widgets.icongroup import TabBG
	from horizons.gui.widgets.stepslider import StepSlider
	from horizons.gui.widgets.unitoverview import HealthWidget, StanceWidget, WeaponStorageWidget
	from horizons.gui.widgets.container import AutoResizeContainer

	widgets = [OkButton, CancelButton, DeleteButton,
			   Inventory, BuySellInventory, ImageFillStatusButton,
			   ProgressBar, StepSlider, TabBG, ToggleImageButton,
			   TooltipIcon, TooltipButton, TooltipLabel, TooltipProgressBar,
			   HealthWidget, StanceWidget, WeaponStorageWidget,
	       AutoResizeContainer]

	for widget in widgets:
		pychan.widgets.registerWidget(widget)

	# style
	for name, stylepart in STYLES.iteritems():
		pychan.manager.addStyle(name, stylepart)

