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

from fife.extensions import pychan

from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.messaging import LanguageChanged
from horizons.util.python.callback import Callback


class HelpDialog(object):

	def __init__(self, mainmenu):
		self.mainmenu = mainmenu
		self.widgets = mainmenu.widgets

		#i18n this defines how each line in our help looks like. Default: '[C] = Chat'
		self.HELPSTRING_LAYOUT = _('[{key}] = {text}') #xgettext:python-format

		self.keyconf = KeyConfig() # before _build_strings
		self._build_strings()
		self._is_displayed = False

		LanguageChanged.subscribe(lambda msg: self._build_strings())

	def _build_strings(self):
		"""
		Loads the help strings from pychan object widgets (containing no key definitions)
		and adds the keys defined in the keyconfig configuration object in front of them.
		The layout is defined through HELPSTRING_LAYOUT and translated.
		"""
		# retranslate the layout
		self.HELPSTRING_LAYOUT = _('[{key}] = {text}') #xgettext:python-format

		widgets = self.widgets['help']
		labels = widgets.getNamedChildren()
		# filter misc labels that do not describe key functions
		labels = dict( (name[4:], lbl[0]) for (name, lbl) in labels.iteritems()
								    if name.startswith('lbl_') )

		# now prepend the actual keys to the function strings defined in xml
		actionmap = self.keyconf.get_actionname_to_keyname_map()
		for (name, lbl) in labels.items():
			keyname = actionmap.get(name, 'SHIFT') #TODO #HACK hardcoded shift key
			lbl.explanation = _(lbl.text)
			lbl.text = self.HELPSTRING_LAYOUT.format(text=lbl.explanation, key=keyname)
			lbl.capture(Callback(self.show_hotkey_change_popup, name, lbl, keyname))

	def show_hotkey_change_popup(self, action, lbl, keyname):
		def apply_new_key(newkey=None):
			if not newkey:
				newkey = free_keys[listbox.selected]
			else:
				listbox.selected = listbox.items.index(newkey)
			self.keyconf.save_new_key(action, newkey=newkey)
			update_hotkey_info(action, newkey)
			lbl.text = self.HELPSTRING_LAYOUT.format(text=lbl.explanation, key=newkey)
			lbl.capture(Callback(self.show_hotkey_change_popup, action, lbl, newkey))
			lbl.adaptLayout()

		def update_hotkey_info(action, keyname):
			default = self.keyconf.get_default_key_for_action(action)
			popup.message.text = (lbl.explanation +
			#xgettext:python-format
			                      u'\n' + _('Current key: [{key}]').format(key=keyname) +
			#xgettext:python-format
			                      u'\t' + _('Default key: [{key}]').format(key=default))
			popup.message.helptext = _('Click to reset to default key')
			reset_to_default = Callback(apply_new_key, default)
			popup.message.capture(reset_to_default)

		#xgettext:python-format
		headline = _('Change hotkey for {action}').format(action=action)
		message = ''
		if keyname in ('SHIFT', 'ESCAPE'):
			message = _('This key can not be reassigned at the moment.')
			self.mainmenu.show_popup(headline, message, {OkButton.DEFAULT_NAME: True})
			return

		popup = self.mainmenu.build_popup(headline, message, size=2, show_cancel_button=True)
		update_hotkey_info(action, keyname)
		keybox = pychan.widgets.ScrollArea()
		listbox = pychan.widgets.ListBox(is_focusable=False, name="available_keys")
		keybox.max_size = listbox.max_size = \
		keybox.min_size = listbox.min_size = \
		keybox.size = listbox.size = (200, 200)
		keybox.position = listbox.position = (90, 110)
		prefer_short = lambda k: (len(k) > 1, len(k) > 3, k)
		is_valid, default_key = self.keyconf.is_valid_and_get_default_key(keyname, action)
		if not is_valid:
			headline = _('Invalid key')
			message = _('The default key for this action has been selected.')
			self.mainmenu.show_popup(headline, message, {OkButton.DEFAULT_NAME: True})
		valid_key = keyname if is_valid else default_key
		free_key_dict = self.keyconf.get_keys_by_name(only_free_keys=True,
		                                              force_include=[valid_key])
		free_keys = sorted(free_key_dict.keys(), key=prefer_short)
		listbox.items = free_keys
		listbox.selected = listbox.items.index(valid_key)
		#TODO backwards replace key names in keyconfig.get_fife_key_names in the list
		# (currently this stores PLUS and PERIOD instead of + and . in the settings)
		keybox.addChild(listbox)
		popup.addChild(keybox)
		if not is_valid:
			apply_new_key()
		listbox.capture(apply_new_key)
		button_cbs = {OkButton.DEFAULT_NAME: True, CancelButton.DEFAULT_NAME: False}
		self.mainmenu.show_dialog(popup, button_cbs, modal=True)

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
