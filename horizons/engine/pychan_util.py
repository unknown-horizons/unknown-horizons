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

import new

from fife.extensions import pychan
from horizons.gui.style import STYLES

def init_pychan():
	"""General pychan initiation for uh"""
	global STYLES

	# register custom widgets

	from horizons.gui.widgets.inventory import Inventory
	from horizons.gui.widgets.buysellinventory import BuySellInventory
	from horizons.gui.widgets.imagefillstatusbutton import  ImageFillStatusButton
	from horizons.gui.widgets.progressbar import ProgressBar
	from horizons.gui.widgets.toggleimagebutton import ToggleImageButton
	from horizons.gui.widgets.imagebutton import CancelButton, DeleteButton, OkButton
	from horizons.gui.widgets.icongroup import TabBG
	from horizons.gui.widgets.stepslider import StepSlider
	from horizons.gui.widgets.unitoverview import HealthWidget, StanceWidget, WeaponStorageWidget
	from horizons.gui.widgets.container import AutoResizeContainer
	from horizons.gui.widgets.tooltip import _Tooltip

	widgets = [OkButton, CancelButton, DeleteButton,
			   Inventory, BuySellInventory, ImageFillStatusButton,
			   ProgressBar, StepSlider, TabBG, ToggleImageButton,
			   HealthWidget, StanceWidget, WeaponStorageWidget,
	       AutoResizeContainer]

	for widget in widgets:
		pychan.widgets.registerWidget(widget)

	# add uh styles
	# NOTE: do this before adding tooltip feature, because pychan has a design issue
	# where it sometimes uses the class hierarchy and sometimes treats each class differently.
	for name, stylepart in STYLES.iteritems():
		pychan.manager.addStyle(name, stylepart)

	# patch default widgets to support tooltips via helptext attribute
	for name, widget in pychan.widgets.WIDGETS.items()[:]:
		if any( attr.name == "helptext" for attr in widget.ATTRIBUTES ):

			# create a new class with a custom __init__, so tooltips are initalized

			klass_name =  str(widget)+" with tooltip hack (see horizons/engine/pychan_util.py"
			klass = type(klass_name, (widget, ), {})

			def __init__(self, *args, **kwargs):
				# this is going to look a bit weird

				# remove all traces of this code ever existing (would confuse pychan badly, don't try to create own widgets)
				self.__class__ = self.__class__.__mro__[1]
				# manually copy everything we need from the tooltip class
				for key, value in _Tooltip.__dict__.iteritems():
					if not key.startswith("__"): # not the internals
						if callable( value ):
							value =  new.instancemethod(value, self)

					# put it in the instance dict, not the class dict
					self.__dict__[key] = value

				# call real init (no super, since we are already in the super class
				self.__init__(*args, **kwargs)

				self.init_tooltip()

			klass.__init__ = __init__

			# register this new class in pychan
			pychan.widgets.WIDGETS[name] = klass


	# NOTE: there is a bug with the tuple notation: http://fife.trac.cvsdude.com/engine/ticket/656
	# work around this here for now:
	def conv(d):
		entries = []
		for k, v in d.iteritems():
			if isinstance(v, dict): # recurse
				v = conv(v)
			if isinstance(k, tuple): # resolve tuple-notation, add separate keys
				for k_i in k:
					entries.append( (k_i, v) )
			else:
				entries.append( (k, v) )

		return dict(entries)

	# patch uh styles
	STYLES = conv(STYLES)

	# patch fife default styles
	pychan.manager.styles = conv(pychan.manager.styles)

