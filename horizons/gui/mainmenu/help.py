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

from fife import fife

from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.mainmenu import Dialog
from horizons.gui.widgets.imagebutton import OkButton


class Help(Dialog):
	widget_name = 'help'
	return_events = {OkButton.DEFAULT_NAME: True}

	def __init__(self, *args, **kwargs):
		super(Help, self).__init__(*args, **kwargs)
		build_help_strings(self._widget_loader[self.widget_name])

	def prepare(self, *args, **kwargs):
		# make game pause if there is a game and we're not in the main menu
		# TODO check missing if we're in the main menu
		if self._gui.session:
			PauseCommand().execute(self._gui.session)
			self._gui.session.ingame_gui.on_escape() # close dialogs that might be open

	def post(self, retval):
		if self._gui.session:
			UnPauseCommand().execute(self._gui.session)


def build_help_strings(widget):
	"""
	Loads the help strings from pychan object widgets (containing no key definitions)
	and adds 	the keys defined in the keyconfig configuration object in front of them.
	The layout is defined through HELPSTRING_LAYOUT and translated.
	"""
	#i18n this defines how each line in our help looks like. Default: '[C] = Chat'
	HELPSTRING_LAYOUT = _('[{key}] = {text}') #xgettext:python-format

	#HACK Ugliness starts; load actions defined through keys and map them to FIFE key strings
	actions = KeyConfig._Actions.__dict__
	reversed_keys = dict([[str(v),k] for k,v in fife.Key.__dict__.iteritems()])
	reversed_stringmap = dict([[str(v),k] for k,v in KeyConfig().keystring_mappings.iteritems()])
	reversed_keyvalmap = dict([[str(v), reversed_keys[str(k)]] for k,v in KeyConfig().keyval_mappings.iteritems()])
	actionmap = dict(reversed_stringmap, **reversed_keyvalmap)
	#HACK Ugliness ends here; These hacks can be removed once a config file exists which is nice to parse.

	labels = widget.getNamedChildren()
	# filter misc labels that do not describe key functions
	labels = dict( (name, lbl) for (name, lbl) in labels.iteritems() if name.startswith('lbl_') )

	# now prepend the actual keys to the function strings defined in xml
	for (name, lbl) in labels.items():
		try:
			keyname = '{key}'.format(key=actionmap[str(actions[name[4:]])])
		except KeyError:
			keyname = ' '
		lbl[0].text = HELPSTRING_LAYOUT.format(text=_(lbl[0].text), key=keyname.upper())

	author_label = widget.findChild(name='fife_and_uh_team')
	author_label.helptext = u"www.unknown-[br]horizons.org[br]www.fifengine.net"
