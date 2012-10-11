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

import horizons.globals
from horizons.gui.window import Window


class Settings(Window):

	def show(self):
		horizons.globals.fife.show_settings()

		# Patch original dialog
		widget = horizons.globals.fife._setting.OptionsDlg
		if not hasattr(widget, '__patched__'):
			# replace hide method so we take control over how the dialog
			# is hided
			self._original_hide = widget.hide
			widget.hide = self.windows.close

			widget.mapEvents({
				'cancelButton': widget.hide
			})
			self._capture_escape(widget)

			widget.__patched__ = True

		self._focus(widget)

	def hide(self):
		self._original_hide()
