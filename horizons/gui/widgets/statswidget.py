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

from horizons.util.gui import load_uh_widget
from horizons.util.python import decorators

class StatsWidget(object):
	"""A widget that creates a large table with statistics."""

	widget_file_name = None # name of the widget's XML file

	def __init__(self, session):
		super(StatsWidget, self).__init__()
		self.session = session
		self._initialised = False
		self._hiding_widget = False # True if and only if the widget is currently in the process of being hidden

	def refresh(self):
		self._clear_entries()

	def _refresh_tick(self):
		if self._initialised and self.is_visible():
			self.refresh()

	def show(self):
		if not self._initialised:
			self._initialised = True
			self._init_gui()
		self._gui.show()

	def hide(self):
		if not self._initialised:
			return # can happen if the logbook calls hide on all statswidgets
		if not self._hiding_widget:
			self._hiding_widget = True
			self._gui.hide()
			self._hiding_widget = False

	def is_visible(self):
		if not self._initialised:
			return False
		return self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()
			self.refresh()

	def _init_gui(self):
		self._gui = load_uh_widget(self.widget_file_name)
		self._gui.position_technique = 'center:center+25'
		self._content_vbox = self._gui.findChild(name = 'content_vbox')
		self.refresh()

	def _clear_entries(self):
		self._content_vbox.removeAllChildren()

decorators.bind_all(StatsWidget)
