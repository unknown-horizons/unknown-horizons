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

import functools

from fife.extensions import pychan
from horizons.gui.style import STYLES

import horizons.main

def handle_gcn_exception(e, msg=None):
	"""Called for RuntimeErrors after gcn::exceptions that smell like guichan bugs.
	@param e: RuntimeError (python, not pychan)
	@param msg: additional info as string
	"""
	import traceback
	traceback.print_stack()
	print 'Caught RuntimeError on gui interaction, assuming irrelevant gcn::exception.'
	if msg:
		print msg

def init_pychan():
	"""General pychan initiation for uh"""
	global STYLES

	# quick hack to allow up_image/down_image values to be unicode
	# TODO solve this problem in a better way (e.g. passing str explicitly)
	# or waiting for a fix of http://fife.trac.cvsdude.com/engine/ticket/701
	from fife.extensions.pychan.properties import ImageProperty

	def patch_imageproperty(func):
		def wrapper(self, obj, image):
			if isinstance(image, unicode):
				image = str(image)
			return func(self, obj, image)
		return wrapper

	ImageProperty.__set__ = patch_imageproperty(ImageProperty.__set__)

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

	# patch default widgets
	for name, widget in pychan.widgets.WIDGETS.items():

		def catch_gcn_exception_decorator(func):
			@functools.wraps(func)
			def wrapper(*args, **kwargs):
				try:
					# only apply usable args, else it would crash when called through fife timers
					pychan.tools.applyOnlySuitable(func, *args, **kwargs)
				except RuntimeError as e:
					handle_gcn_exception(e)
			return wrapper

		widget.hide = catch_gcn_exception_decorator(widget.hide)

		# support for tooltips via helptext attribute
		if any( attr.name == "helptext" for attr in widget.ATTRIBUTES ):
			# Copy everything we need from the tooltip class (manual mixin).
			# TODO Figure out if it is safe to use this instead:
			#widget.__bases__ += (_Tooltip, )
			for key, value in _Tooltip.__dict__.iteritems():
				if not key.startswith("__"):
					setattr(widget, key, value)

			def add_tooltip_init(func):
				@functools.wraps(func)
				def wrapper(self, *args, **kwargs):
					func(self, *args, **kwargs)
					self.init_tooltip()
				return wrapper

			widget.__init__ = add_tooltip_init(widget.__init__)

			# these sometimes fail with "No focushandler set (did you add the widget to the gui?)."
			# see #1597 and #1647
			widget.requestFocus = catch_gcn_exception_decorator(widget.requestFocus)

	# set cursor to rename on hover for certain widgets
	def add_cursor_change_on_hover_init(func):
		@functools.wraps(func)
		def wrapper(self, *args, **kwargs):
			func(self, *args, **kwargs)
			def set_cursor():
				horizons.main.fife.set_cursor_image("rename")
			def unset_cursor():
				horizons.main.fife.set_cursor_image("default")
			self.mapEvents({
			  self.name+'/mouseEntered/cursor' : set_cursor,
			  self.name+'/mouseExited/cursor' : unset_cursor,
			  })
		return wrapper

	TextField = pychan.widgets.WIDGETS['TextField']
	TextField.__init__ = add_cursor_change_on_hover_init(TextField.__init__)

	# TODO: if the widget is hidden while the cursor is above it,
	# there is no exited event. A possible workaround would be to check
	# in short intervals whether the widget is still visible, possible also
	# whether the mouse is still above it (the later would be necessary in
	# case another widget is drawn above the original widget)
	# Since that would be quite ugly, it should only be done when consulting
	# pychan-savvy people yields no success.


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



def get_button_event(button):
	"""Returns the callback that is triggered when the button is clicked on.
	@param button: pychan Button"""
	try:
		# try dialog action
		return button.event_mapper.callbacks['__execute__']['action']
	except KeyError:
		try:
			# try mapped event
			return button.event_mapper.callbacks['default']['action']
		except KeyError:
			return None
