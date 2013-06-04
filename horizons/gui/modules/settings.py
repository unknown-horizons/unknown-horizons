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

import horizons.globals
from horizons.gui.windows import Window


class SettingsDialog(Window):
	"""Wrapper around fife's settings dialog to make it work with the WindowManager."""

	def show(self):
		horizons.globals.fife.show_settings()

		fife_setting = horizons.globals.fife._setting
		if not hasattr(fife_setting, '_optionsDialog'):
			#TODO fifechan / FIFE 0.3.5+ compat
			# this is the old API
			widget = fife_setting.OptionsDlg
		else:
			widget = fife_setting._optionsDialog
		# Patch original dialog
		if not hasattr(widget, '__patched__'):
			# replace hide method so we take control over how the dialog
			# is hidden
			self._original_hide = widget.hide
			widget.hide = self._windows.close

			widget.mapEvents({
				'cancelButton': widget.hide
			})

			widget.__patched__ = True

	def hide(self):
		self._original_hide()
