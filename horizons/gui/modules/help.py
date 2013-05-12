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

from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.windows import Window
from horizons.messaging import LanguageChanged


class HelpDialog(Window):

	def __init__(self, windows, session=None):
		super(HelpDialog, self).__init__(windows)

		self._session = session
		self.widget = load_uh_widget('help.xml')

		self.keyconf = KeyConfig() # before _build_strings
		self.HELPSTRING_LAYOUT = None
		self._build_strings()
		self._is_displayed = False

		self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)

		LanguageChanged.subscribe(lambda msg: self._build_strings())

	def _build_strings(self):
		"""
		Loads the help strings from pychan object widgets (containing no key definitions)
		and adds the keys defined in the keyconfig configuration object in front of them.
		The layout is defined through HELPSTRING_LAYOUT and translated.
		"""
		#i18n this defines how each line in our help looks like. Default: '[C] = Chat'
		self.HELPSTRING_LAYOUT = _('[{key}] = {text}') #xgettext:python-format

		labels = self.widget.getNamedChildren()
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

	def show(self):
		self.widget.show()
		if self._session:
			PauseCommand().execute(self._session)

	def hide(self):
		if self._session:
			UnPauseCommand().execute(self._session)
		self.widget.hide()
