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

from horizons.extscheduler import ExtScheduler
from horizons.gui.util import load_uh_widget
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.util.pychanchildfinder import PychanChildFinder
from horizons.util.python.callback import Callback


@metaChangeListenerDecorator('remove')
class TabInterface:
	"""
	The TabInterface should be used by all classes that represent Tabs for the
	TabWidget.

	By default the code will the widget from a file given by `widget`. If you
	want to run code after the widget has been loaded, override `init_widget`.
	To handle widget loading yourself, override `get_widget` and return the new
	widget.
	In both cases the widget is accessible at `self.widget`.

	If you want to override the TabButton image used for the tab, you also have
	to set the button_image_{up,down,hover} variables.

	Use the refresh() method to implement any redrawing of the widget. The
	TabWidget will call this method based on callbacks. If you set any callbacks
	yourself, make sure you get them removed when the widget is deleted.

	@param widget: Filename of widget to load.
	@param icon_path: Where to look for ImageButton icons. Note: this is a `path` attribute!
	"""

	# Whether to load the tab only when it's shown.
	# If True, self.widget will only be valid after _lazy_loading_init, which
	# is guaranteed to be executed before show(), refresh() and the like.
	# Usually, you will want to overwrite _lazy_loading_init and call the super impl as first step.
	# Note: to prevent memory leak due to unshown tabs registered with WidgetManager, always set it
	# to be true by default
	# set it false only in its subclass if have special reason to disable lazy_loading
	lazy_loading = True

	# Override these in your subclass either as class attribute, or by passing it
	# to the constructor. The value of the constructor has preference over the
	# class attribute.
	widget = None # type: str
	icon_path = 'images/tabwidget/tab'

	scheduled_update_delay = 0.4 # seconds, update after this time when an update is scheduled

	def __init__(self, widget=None, icon_path=None, **kwargs):
		"""
		@param widget: filename of a widget. Set this to None if you create your
		               widget in `get_widget`.
		"""
		super().__init__()
		if widget or self.__class__.widget:
			self.widget = widget or self.__class__.widget
			if not self.__class__.lazy_loading:
				self._setup_widget()
		else:
			# set manually by child
			self.widget = None

		# Regular `image` paths for Icon
		self.button_background_image = 'content/gui/images/tabwidget/tab_dark.png'
		self.button_background_image_active = 'content/gui/images/tabwidget/tab_active_xxl.png'

		# `path` attribute for ImageButton, i.e. without 'content/gui/' and '.png'
		self.path = icon_path or self.__class__.icon_path
		# the active tab image has no special down or hover images, so this works with `path` too
		self.path_active = self.path + '_a'

		self._refresh_scheduled = False

	def _setup_widget(self):
		"""Gets the widget and sets up some attributes and helper.

		This is called when the Tab is created, or, when lazy loading is
		active once the tab is about to be shown.
		"""
		self.widget = self.get_widget()
		self.widget.child_finder = PychanChildFinder(self.widget)
		self.init_widget()

	def get_widget(self):
		"""Loads the filename in self.widget.

		Override this in your subclass if you want to handle widget
		loading/creation yourself.
		"""
		return load_uh_widget(self.widget)

	def init_widget(self):
		"""Initialize widget after it was loaded.

		Override this in your subclass if you have custom post-load code.
		"""
		pass

	def show(self):
		"""Shows the current widget"""
		self.ensure_loaded()
		self.widget.show()

	def hide(self):
		"""Hides the current widget"""
		self.ensure_loaded()
		self.widget.hide()

		if self._refresh_scheduled:
			ExtScheduler().rem_all_classinst_calls(self)
			self._refresh_scheduled = False

	def is_visible(self):
		self.ensure_loaded()
		# naming convention clash: python vs c++
		return self.widget.isVisible()

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		pass

	def _schedule_refresh(self):
		"""Schedule a refresh soon, dropping all other refresh request, that appear until then.
		This saves a lot of CPU time, if you have a huge island, or play on high speed."""
		if not self._refresh_scheduled:
			self._refresh_scheduled = True
			def unset_flag():
				# set the flag here and not in refresh() since we can't be sure whether
				# refresh() of this class will be reached or a subclass will not call super()
				self._refresh_scheduled = False
			ExtScheduler().add_new_object(Callback.ChainedCallbacks(unset_flag, self.refresh),
			                              self, run_in=self.__class__.scheduled_update_delay)

	@classmethod
	def shown_for(cls, instance):
		"""Method for fine-grained control of which tabs to show.
		@return: whether this tab should really be shown for this instance"""
		return True

	def ensure_loaded(self):
		"""Called when a tab is shown, acts as hook for lazy loading"""
		if self.__class__.lazy_loading and not hasattr(self, "_lazy_loading_loaded"):
			self._setup_widget()
			self._lazy_loading_loaded = True # this is to prevent more setups if called multiple times

	def _get_position(self):
		self.ensure_loaded()
		return self.widget.position

	def _set_position(self, value):
		"""Sets the widgets position to tuple *value*"""
		self.ensure_loaded()
		self.widget.position = value

	# Shortcut to set and retrieve the widget's current position.
	position = property(_get_position, _set_position)
