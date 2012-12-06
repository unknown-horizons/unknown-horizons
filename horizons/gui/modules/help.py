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

from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.widgets.imagebutton import OkButton
from horizons.messaging import LanguageChanged


class HelpDialog(object):

	def __init__(self, mainmenu):
		self.mainmenu = mainmenu
		self.widgets = mainmenu.widgets

		self.keyconf = KeyConfig() # before _build_strings
		self.HELPSTRING_LAYOUT = None
		self._build_strings()
		self._is_displayed = False

		LanguageChanged.subscribe(lambda msg: self._build_strings())

	def _build_strings(self):
		"""
		Loads the help strings from pychan object widgets (containing no key definitions)
		and adds the keys defined in the keyconfig configuration object in front of them.
		The layout is defined through HELPSTRING_LAYOUT and translated.
		"""
		#i18n this defines how each line in our help looks like. Default: '[C] = Chat'
		self.HELPSTRING_LAYOUT = _('[{key}] = {text}') #xgettext:python-format

		widgets = self.widgets['help']
		labels = widgets.getNamedChildren()
		# filter misc labels that do not describe key functions
		labels = dict( (name[4:], lbl[0]) for (name, lbl) in labels.iteritems()
								    if name.startswith('lbl_') )

		# now prepend the actual keys to the function strings defined in xml
		for (name, lbl) in labels.items():
			if name == 'SHIFT':
				#TODO #HACK hardcoded shift key
				keyname = 'SHIFT'
			else:
				#TODO Display all keys per action, not just the first
				keyname = self.keyconf.get_current_keys(name)[0]
			lbl.explanation = _(lbl.text)
			lbl.text = self.HELPSTRING_LAYOUT.format(text=lbl.explanation, key=keyname)

	def toggle(self):
		"""Called on help action.
		Toggles help screen via static variable *help_is_displayed*.
		Can be called both from main menu and in-game interface.
		"""
		help_dlg = self.widgets['help']
		if not self._is_displayed:
			self._is_displayed = True
			# make game pause if there is a game and we're not in the main menu
			if self.mainmenu.session is not None and self.mainmenu.current != self.widgets['ingamemenu']:
				PauseCommand().execute(self.mainmenu.session)
			if self.mainmenu.session is not None:
				self.mainmenu.session.ingame_gui.on_escape() # close dialogs that might be open
			self.mainmenu.show_dialog(help_dlg, {OkButton.DEFAULT_NAME : True})
			self.toggle() # toggle state
		else:
			self._is_displayed = False
			if self.mainmenu.session is not None and self.mainmenu.current != self.widgets['ingamemenu']:
				UnPauseCommand().execute(self.mainmenu.session)
			help_dlg.hide()
