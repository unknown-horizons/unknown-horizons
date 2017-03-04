# -*- coding: utf-8 -*-
# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from __future__ import print_function

import functools
import traceback

from fife.extensions import pychan

import horizons.globals
from horizons.gui.style import STYLES
from horizons.gui.widgets.imagebutton import ImageButton
from horizons.messaging import GuiAction, GuiCancelAction, GuiHover
from horizons.util.python.callback import Callback


class RenameLabel(pychan.widgets.Label):
	"""A regular label that signals that it will display a rename dialog when clicked upon (by changing the cursor)"""
	pass # implementation added dynamically below
class RenameImageButton(ImageButton):
	pass # as above

def handle_gcn_exception(e, msg=None):
	"""Called for RuntimeErrors after gcn::exceptions that smell like guichan bugs.
	@param e: RuntimeError (python, not pychan)
	@param msg: additional info as string
	"""
	traceback.print_stack()
	print('Caught RuntimeError on gui interaction, assuming irrelevant gcn::exception.')
	if msg:
		print(msg)

def init_pychan():
	"""General pychan initiation for uh"""
	global STYLES

	# quick hack to allow up_image/down_image values to be unicode
	# TODO solve this problem in a better way (e.g. passing str explicitly)
	# or waiting for a fix of http://github.com/fifengine/fifengine/issues/701
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
	from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
	from horizons.gui.widgets.progressbar import ProgressBar, TilingProgressBar
	# additionally, ImageButton is imported from widgets.imagebutton above
	from horizons.gui.widgets.imagebutton import CancelButton, DeleteButton, MainmenuButton, OkButton
	from horizons.gui.widgets.icongroup import TabBG, TilingHBox, hr
	from horizons.gui.widgets.stepslider import StepSlider
	from horizons.gui.widgets.unitoverview import HealthWidget, StanceWidget, WeaponStorageWidget
	from horizons.gui.widgets.tooltip import _Tooltip

	widgets = [OkButton, CancelButton, DeleteButton, MainmenuButton,
	           Inventory, BuySellInventory, ImageFillStatusButton,
	           ProgressBar, StepSlider, TabBG,
	           HealthWidget, StanceWidget, WeaponStorageWidget,
	           RenameLabel, RenameImageButton,
	           TilingHBox, TilingProgressBar, hr,
			 # This overwrites the ImageButton provided by FIFE!
	           ImageButton]

	for widget in widgets:
		pychan.widgets.registerWidget(widget)

	# add uh styles
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

	from fife.extensions.pychan import ABox, HBox, Icon, Label, VBox
	# this is white list of widgets with tooltip.
	widgets_with_tooltip = [ABox, HBox, Icon, ImageButton, Label, VBox]

	for widget in widgets_with_tooltip:
		# Copy everything we need from the tooltip class (manual mixin).
		# TODO: Figure out if it is safe to use this instead:
		# widget.__bases__ += (_Tooltip, )
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

	# FIXME hack pychan's text2gui function, it does an isinstance check that breaks
	# the lazy string from horizons.i18n. we should be passing unicode to
	# widgets all the time, therefore we don't need the additional check.
	def text2gui(text):
		unicodePolicy = horizons.globals.fife.pychan.manager.unicodePolicy
		return text.encode("utf8",*unicodePolicy).replace("\t"," "*4).replace("[br]","\n")

	pychan.widgets.textfield.text2gui = text2gui
	pychan.widgets.basictextwidget.text2gui = text2gui


	setup_cursor_change_on_hover()

	setup_trigger_signals_on_action()

	setup_trigger_signals_on_hover()


def setup_cursor_change_on_hover():

	# set cursor to rename on hover for certain widgets
	def set_cursor():
		horizons.globals.fife.set_cursor_image("rename")
	def unset_cursor():
		horizons.globals.fife.set_cursor_image("default")

	def make_cursor_change_on_hover_class(cls):
		# this can't be a regular class since vanilla TextFields should have it by default
		def disable_cursor_change_on_hover(self):
			self.mapEvents({
				self.name+'/mouseEntered/cursor' : None,
				self.name+'/mouseExited/cursor' : None,
				})

		def enable_cursor_change_on_hover(self):
			self.mapEvents({
				self.name+'/mouseEntered/cursor' : set_cursor,
				self.name+'/mouseExited/cursor' : unset_cursor,
				# this changes the cursor if the widget is hidden while the
				# cursor is still above the textfield
				self.name+'/ancestorHidden/cursor': unset_cursor
				})

		def add_cursor_change_on_hover_init(func):
			@functools.wraps(func)
			def wrapper(self, *args, **kwargs):
				func(self, *args, **kwargs)
				enable_cursor_change_on_hover(self)
			return wrapper

		cls.__init__ = add_cursor_change_on_hover_init(cls.__init__)
		cls.disable_cursor_change_on_hover = disable_cursor_change_on_hover
		cls.enable_cursor_change_on_hover = enable_cursor_change_on_hover

	make_cursor_change_on_hover_class(pychan.widgets.WIDGETS['TextField'])
	make_cursor_change_on_hover_class(RenameLabel)
	make_cursor_change_on_hover_class(RenameImageButton)


def setup_trigger_signals_on_action():
	"""Make sure that every widget sends a signal when an action event occurs"""
	def make_action_trigger_a_signal(cls):
		def add_action_triggers_a_signal(func):
			@functools.wraps(func)
			def wrapper(self, *args, **kwargs):
				func(self, *args, **kwargs)
				if cls._getName(self) == "cancelButton":
					self.capture(Callback(GuiCancelAction.broadcast, self), "action", "action_listener")
				else:
					self.capture(Callback(GuiAction.broadcast, self), "action", "action_listener")
			return wrapper

		cls.__init__ = add_action_triggers_a_signal(cls.__init__)

	make_action_trigger_a_signal(pychan.widgets.Widget)

def setup_trigger_signals_on_hover():
	"""Make sure that the widgets specified below send a signal when a mouseOver event occurs"""
	def make_hover_trigger_a_signal(cls):
		def add_hover_triggers_a_signal(func):
			@functools.wraps(func)
			def wrapper(self, *args, **kwargs):
				func(self, *args, **kwargs)
				self.capture(Callback(GuiHover.broadcast, self), "mouseEntered", "action_listener")
			return wrapper

		cls.__init__ = add_hover_triggers_a_signal(cls.__init__)

	make_hover_trigger_a_signal(pychan.widgets.WIDGETS['OkButton'])
	make_hover_trigger_a_signal(pychan.widgets.WIDGETS['CancelButton'])
	make_hover_trigger_a_signal(pychan.widgets.WIDGETS['DeleteButton'])
	make_hover_trigger_a_signal(pychan.widgets.WIDGETS['MainmenuButton'])
	make_hover_trigger_a_signal(pychan.widgets.WIDGETS['ImageButton'])
