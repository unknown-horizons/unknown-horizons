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

from collections import namedtuple

import horizons.globals

from horizons.constants import LANGUAGENAMES
from horizons.engine import UH_MODULE
from horizons.i18n import _lazy, find_available_languages
from horizons.gui.widgets.pickbeltwidget import PickBeltWidget
from horizons.gui.windows import Window


Setting = namedtuple('Setting', 'module name widget_name initial_data')


class SettingsDialog(PickBeltWidget, Window):
	"""Widget for Options dialog with pickbelt style pages"""

	widget_xml = 'settings.xml'
	sections = (('graphics_settings', _lazy('Graphics')),
			    ('game_settings', _lazy('Game')))

	def __init__(self, windows):
		Window.__init__(self, windows)
		PickBeltWidget.__init__(self)

		self._settings = horizons.globals.fife._setting

		self.widget.mapEvents({
			'okButton': self.apply_settings,
			'defaultButton': self.set_defaults,
			'cancelButton': self._windows.close,
		})

		languages = find_available_languages().keys()
		language_names = [LANGUAGENAMES[x] for x in sorted(languages)]

		self._options = [
			Setting(UH_MODULE, 'Language', 'uni_language', language_names)
		]

		self._fill_widgets()

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()

	def set_defaults(self):
		title = _("Restore default settings")
		msg = _("Restoring the default settings will delete all changes to the settings you made so far.") + \
				u" " + _("Do you want to continue?")

		if self._windows.show_popup(title, msg, show_cancel_button=True):
			self._settings.set_defaults()

	def apply_settings(self):
		for entry in self._options:
			widget = self.widget.findChild(name=entry.widget_name)
			data = widget.getData()

			if isinstance(entry.initial_data, list):
				data = entry.initial_data[data]
			elif isinstance(entry.initial_data, dict):
				data = entry.initial_data.keys()[data]

			self._settings.set(entry.module, entry.name, data)

		self._settings.apply()
		self._settings.save()
		self._windows.close()

	def _fill_widgets(self):
		for entry in self._options:
			value = self._settings.get(entry.module, entry.name)
			widget = self.widget.findChild(name=entry.widget_name)

			if entry.initial_data:
				if isinstance(entry.initial_data, dict):
					widget.setInitialData(entry.initial_data.values())
					value = entry.initial_data.keys().index(value)
				elif isinstance(entry.initial_data, list):
					widget.setInitialData(entry.initial_data)
					value = entry.initial_data.index(value)
				else:
					widget.setInitialData(entry.initial_data)

			widget.setData(value)
