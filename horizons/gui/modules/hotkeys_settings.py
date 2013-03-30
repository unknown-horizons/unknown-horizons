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
from fife import fife
from horizons.command.game import PauseCommand, UnPauseCommand
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.windows import Window
from horizons.messaging import LanguageChanged
from horizons.util.python.callback import Callback
from fife.extensions.pychan.widgets import Button, Label


class HotkeyConfiguration(Window):

	def __init__(self, windows, session=None):
		super(HotkeyConfiguration, self).__init__(windows)

		self._session = session
		self.widget = load_uh_widget('hotkeys.xml')
		self.buttons = []

		self.actions = sorted([action for action in horizons.globals.fife.get_hotkey_settings()])

		self.keyconf = KeyConfig()
		self.HELPSTRING_LAYOUT = None
		self._is_displayed = False
		self._build_interface()

		self.detecting = False
		self.current_button = None
		self.current_index = None
		self.last_combination = []

		self.keys = self.keyconf.get_keys_by_value()

		self.widget.mapEvents({self.widget.name + '/keyPressed' : self._detect_keypress})
		self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)
		self.widget.findChild(name="reset_to_default").capture(self.reset_to_default)

	def _build_interface(self):
		container = self.widget.findChild(name='keys_container')
		button_container = self.widget.findChild(name='button_container')
		for i in range(len(self.actions)):
 			action = self.actions[i]
			label = self._create_label(action)
			button = self._create_button(action, 'prim', i)
			button.mapEvents({button.name + '/mouseClicked' : Callback(self._detect_click_on_button, button)})
			container.addChild(label)
			button_container.addChild(button)
			self.buttons.append(button)

	def _create_label(self, action):
		#xgettext:python-format
		text = _('{action_name}'.format(action_name=action))
		label = Label(text=text)
		label.max_size = (130,42)
		return label

	def _create_button(self, action, prefix, index):
		#xgettext:python-format
		keyname = _(self.keyconf.get_current_keys(action)[0])
		button = Button(text=keyname)
		button.name = str(index)
		button.max_size = (130,18)
		return button

	def _detect_click_on_button(self, button):
		self.detecting = True
		self.current_button = button
		self.current_index = int(button.name)
		#xgettext:python-format
		button.text = _("Press desired key")

	def _detect_keypress(self, event):
		print event.getKey().getValue()
		if self.detecting:
			self.last_combination.append(event.getKey())
			self.detecting = False
			self.apply_change()

	def keyName(self, key):
		value = key.getValue()
		return self.keys[value]

	def key_is_set(self, key):
		keys_mappings = self.keyconf.keyval_action_mappings
		if keys_mappings.get(key.getValue()):
				return True
		return False

	def get_action_name(self, key):
		key_name = self.keyName(key)
		print 'looking for ', key_name
		custom_key_actions = horizons.globals.fife.get_hotkey_settings()
		for action in custom_key_actions:
			k = custom_key_actions[action]
			if key_name in k:
				return action
		print "Action name not found. Key name must be wrong. This is not supposed to ever happen"

	def reset_to_default(self):
		for action in self.actions:
			default_key = horizons.globals.fife.get_keys_for_action(action, default=True)
			horizons.globals.fife.set_key_for_action(action, default_key)
		horizons.globals.fife.save_settings()

		self.update_buttons_text()

	def update_buttons_text(self):
		for i in range(len(self.buttons)):
			button = self.buttons[i]
			action = self.actions[i]
			keyname = _(self.keyconf.get_current_keys(action)[0])
			button.text = keyname

	def apply_change(self):
		key = self.last_combination[0]
		action = self.actions[self.current_index]
		key_name = self.keyName(key)

		if not self.key_is_set(key):
			horizons.globals.fife.set_key_for_action(action, key_name)
		else:
			oldaction = self.get_action_name(key)
			# Here we should ask whether the user wants to change the old binding
			# TODO define remove_key() in engine.py
			horizons.globals.fife.set_key_for_action(oldaction, 'Q')
			horizons.globals.fife.set_key_for_action(action, key_name)
		horizons.globals.fife.save_settings()

		self.current_button.text = _(self.keyName(self.last_combination[0]))
		self.last_combination = []

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()
