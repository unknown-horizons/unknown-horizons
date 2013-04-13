# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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

from horizons.i18n import _lazy
from horizons.gui.widgets.pickbeltwidget import PickBeltWidget
from horizons.gui.windows import Window


class SettingsDialog(PickBeltWidget, Window):
	"""Widget for Options dialog with pickbelt style pages"""

	widget_xml = 'settings.xml'
	sections = (('graphics_settings', _lazy('Graphics')),
			    ('game_settings', _lazy('Game')))

	def __init__(self, windows):
		Window.__init__(self, windows)
		PickBeltWidget.__init__(self)

		self.widget.mapEvents({
			'okButton': self.apply_settings,
			'defaultButton': self.set_defaults,
			'cancelButton': self._windows.close,
		})

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()

	def set_defaults(self):
		title = _("Restore default settings")
		msg = _("Restoring the default settings will delete all changes to the settings you made so far.") + \
				u" " + _("Do you want to continue?")

		if self._windows.show_popup(title, msg, show_cancel_button=True):
			horizons.globals.fife._setting.set_defaults()

	def apply_settings(self):
		horizons.globals.fife._setting.save()
		self._windows.close()
