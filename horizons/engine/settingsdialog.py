# -*- coding: utf-8 -*-
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


try:
	#TODO fifechan / FIFE 0.3.5+ compat
	from fife.extensions.pychan.fife_pychansettings import FifePychanSettings
except ImportError:
	# this is the old (0.3.4 and earlier) API
	from fife.extensions.fife_settings import Setting as FifePychanSettings

import horizons.main

from horizons.constants import LANGUAGENAMES
from horizons.engine import UH_MODULE
from horizons.gui.modules.hotkeys_settings import HotkeyConfiguration
from horizons.gui.widgets.pickbeltwidget import OptionsPickbeltWidget
from horizons.messaging import SettingChanged

class SettingsDialog(FifePychanSettings):
	"""
	Localized settings dialog by using load_uh_widget() instead of
	plain load_xml().
	"""
	def _loadWidget(self, dialog):
		# NOTE: in the fife superclass, this is used for the main widget
		# as well as the require-restart message. Here, we allow us to ignore
		# the parameter since _showChangeRequireRestartDialog() is overwritten as well

		optionsPickbelt = OptionsPickbeltWidget()
		wdg = optionsPickbelt.get_widget()
		hk = HotkeyConfiguration()
		number = optionsPickbelt.__class__.sections.index(('hotkeys_settings', _('Hotkeys')))
		optionsPickbelt.page_widgets[number].addChild(hk.widget)

		self.hotkeyInterface = hk

		# HACK: fife settings call stylize, which breaks our styling on widget load
		no_restyle_str = "do_not_restyle_this"
		self.setGuiStyle(no_restyle_str)
		def no_restyle(style):
			if style != no_restyle_str:
				wdg.stylize(style)
		wdg.stylize = no_restyle

		return wdg

	def _showChangeRequireRestartDialog(self):
		"""Overwrites FIFE dialog call to use no xml file but a show_popup."""
		headline = _("Restart required")
		message = _("Some of your changes require a restart of Unknown Horizons.")
		horizons.main._modules.gui.show_popup(headline, message)

	def setDefaults(self):
		title = _("Restore default settings")
		msg = _("Restoring the default settings will delete all changes to the settings you made so far.") + \
			u" " + _("Do you want to continue?")
		try:
			confirmed = horizons.main._modules.gui.show_popup(title, msg,
						                                      show_cancel_button=True)
		except AttributeError: #no gui available, called by e.g. cmd line param
			confirmed = True
		if confirmed:
			try:
				super(SettingsDialog, self).setDefaults()
				self.hotkeyInterface.reset_to_default()
			except AttributeError as err: #weird stuff happens in settings module reset
				print "A problem occured while updating: %s" % err + "\n" + \
					  "Please contact the developers if this happens more than once."

	def get(self, module, name, defaultValue=None):
		# catch events for settings that should be displayed in another way than they should be saved
		v = super(SettingsDialog, self).get(module, name, defaultValue)
		if module == UH_MODULE and name == "Language":
			if v is None: # the entry is None for empty strings
				v = ""
			v = LANGUAGENAMES[v]
		return v

	def set(self, module, name, val, extra_attrs=None):
		if extra_attrs is None:
			extra_attrs = {} # that's bad to have as default value
		# catch events for settings that should be displayed in another way than they should be saved
		if module == UH_MODULE and name == "Language":
			val = LANGUAGENAMES.get_by_value(val)

		SettingChanged.broadcast(self, name, self.get(module, name), val)
		return super(SettingsDialog, self).set(module, name, val, extra_attrs)

	def applySettings(self):
		self.hotkeyInterface.save_settings()
		super(SettingsDialog, self).applySettings()
