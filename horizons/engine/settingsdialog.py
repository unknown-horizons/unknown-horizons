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


from fife.extensions.fife_settings import Setting

import horizons.main

from horizons.engine import UH_MODULE
from horizons.constants import LANGUAGENAMES
from horizons.gui.widgets.pickbeltwidget import OptionsPickbeltWidget

class SettingsDialog(Setting):
	"""
	Localized settings dialog by using load_uh_widget() instead of
	plain load_xml().
	"""
	def _loadWidget(self, dialog):
		# NOTE: in the fife superclass, this is used for the main widget
		# as well as the require-restart message. Here, we allow us to ignore
		# the parameter since _showChangeRequireRestartDialog() is overwritten as well

		wdg = OptionsPickbeltWidget().get_widget()
		# HACK: fife settings call stylize, which breaks our styling on widget load
		no_restyle_str = "do_not_restyle_this"
		self.setGuiStyle(no_restyle_str)
		def no_restyle(style):
			if style != no_restyle_str:
				wdg.stylize(style)
		wdg.stylize = no_restyle

		# on_escape HACK at the interface between fife gui and uh gui.
		# show_dialog of gui.py would handle this nicely, but to be able to
		# reuse the fife code, we have do something here.

		if horizons.main._modules.session is not None:
			gui = horizons.main._modules.session.ingame_gui
		else:
			gui = horizons.main._modules.gui

		# overwrite hide of widget to reset on_escape to old value when the settings
		# dialog has been hidden
		old_on_escape = gui.on_escape
		old_hide = wdg.hide
		def on_hide():
			old_hide()
			gui.on_escape = old_on_escape
			return True # event is handled

		# use it for escape and hide to cover all cases
		gui.on_escape = on_hide
		wdg.hide = on_hide

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
		return super(SettingsDialog, self).set(module, name, val, extra_attrs)

