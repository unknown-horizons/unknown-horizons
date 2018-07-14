# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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
from fife.extensions.pychan.widgets import Button

import horizons.globals
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.i18n import gettext as T
from horizons.util.python.callback import Callback


class HotkeyConfiguration:

	def __init__(self):
		super().__init__() # TODO: check whether this call is needed

		self.widget = load_uh_widget('hotkeys.xml')
		self.buttons = []
		self.secondary_buttons = []

		self.keyconf = KeyConfig()
		self.actions = self.keyconf.get_bindable_actions_by_name()
		self.keys = self.keyconf.get_keys_by_value()

		self.HELPSTRING_LAYOUT = None
		self._build_interface()

		# When `detecting` is True, the interface detects keypresses and binds them to actions
		self.detecting = False
		self.current_button = None
		self.current_index = None
		self.last_combination = []
		# Stores whether the last button pressed was for a primary or secondary binding (1 or 2)
		self.last_column = 1

		# This used to go though the widget's key events, but fifechan has different keynames
		# Using a fife keylistener ensures that the in-game keys always match
		self.listener = HotkeysListener(self._detect_keypress)

		self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self.save_settings)
		self.widget.mapEvents({OkButton.DEFAULT_NAME: self.save_settings})
		self.widget.findChild(name="reset_to_default").capture(self.reset_to_default)

	def _build_interface(self):
		button_container = self.widget.findChild(name='button_container')
		sec_button_container = self.widget.findChild(name='sec_button_container')
		for i, action in enumerate(self.actions):
			button = self._create_button(action, i)
			sec_button = self._create_button(action, i)
			button.mapEvents({button.name + '/mouseClicked': Callback(self._detect_click_on_button, button, 1)})
			sec_button.mapEvents({button.name + '/mouseClicked': Callback(self._detect_click_on_button, sec_button, 2)})
			button_container.addChild(button)
			sec_button_container.addChild(sec_button)
			self.buttons.append(button)
			self.secondary_buttons.append(sec_button)
		self.update_buttons_text()

	def _create_button(self, action, index):
		"""Important! The button name is set to index so that when a button is pressed, we know its index"""
		button = Button(is_focusable=False)
		button.name = str(index)
		button.max_size = button.min_size = (100, 18)
		return button

	def _detect_click_on_button(self, button, column):
		"""Starts the listener and remembers the position and index of the pressed button"""
		self.detecting = True
		self.current_button = button
		self.current_index = int(button.name)
		self.current_column = column
		self.listener.activate()
		self.update_buttons_text()
		button.font = 'default'
		button.text = T("Press key…")

	def _detect_keypress(self, event):
		if not self.detecting:
			return
		key = event.getKey()
		# if the key is not supported, act as if it was not detected
		if not self.key_name(key):
			return
		self.last_combination.append(key)
		self.detecting = False
		self.listener.deactivate()
		self.apply_change()

	def update_buttons_text(self):
		for i, button in enumerate(self.buttons):
			button.font = 'default_bold'
			action = self.actions[i]
			bindings = self.keyconf.get_current_keys(action)
			for j in range(len(bindings)):
				if bindings[j] == 'UNASSIGNED':
					bindings[j] = ''
			secondary_button = self.secondary_buttons[i]
			button.text = str(bindings[0])
			if len(bindings) > 1:
				secondary_button.font = 'default_bold'
				secondary_button.text = str(bindings[1])
			else:
				secondary_button.text = ''

	def apply_change(self):
		"""Binds the last keypress to the corresponding action and resets the interface to the state where it is listening for clicks on buttons"""
		key = self.last_combination[0]
		key_name = self.key_name(key)
		action = self.actions[self.current_index]

		# Escape is used to unassign bindings
		if key_name == 'ESCAPE':
			key_name = 'UNASSIGNED'

		# If *key* is already set, replace the entry for *key* with UNASSIGNED for the last action.
		# This is done to avoid binding one key for two actions.
		elif self.key_is_set(key):
			oldaction = self.get_action_name(key)
			if action == oldaction and key_name in self.keyconf.get_current_keys(action):
				self.update_buttons_text()
				self.last_combination = []
				return

			message = T("{key} is already set to {action}.").format(key=key_name, action=oldaction)
			message += " " + T("Would you like to overwrite it?")
			confirmed = horizons.main.gui.open_popup(T("Confirmation for overwriting"), message, show_cancel_button=True)
			if confirmed:
				horizons.globals.fife.replace_key_for_action(oldaction, key_name, "UNASSIGNED")
			else:
				self.update_buttons_text()
				self.last_combination = []
				return

		bindings = self.keyconf.get_current_keys(action)
		if self.current_column == 1:
			bindings[0] = key_name
		elif self.current_column == 2:
			if len(bindings) < 2:
				bindings.append(key_name)
			else:
				bindings[1] = key_name

		horizons.globals.fife.set_key_for_action(action, bindings)

		self.update_buttons_text()
		self.last_combination = []

	def key_name(self, key):
		value = key.getValue()
		return self.keys.get(value)

	def key_is_set(self, key):
		key_name = self.key_name(key)
		custom_key_actions = horizons.globals.fife.get_hotkey_settings()
		for k in custom_key_actions.values():
			if key_name in k:
				return True
		return False

	def get_current_bindings(self):
		""" Returns a dict mapping action -> list of keys """
		bindings = {}
		for action in self.actions:
			keys = self.keyconf.get_current_keys(action)
			bindings[action] = keys
		return bindings

	def get_action_name(self, key):
		key_name = self.key_name(key)
		custom_key_actions = horizons.globals.fife.get_hotkey_settings()
		for action in custom_key_actions:
			k = custom_key_actions[action]
			if key_name in k:
				return action
		print("Action name not found. Key name (" + key_name + ") must be wrong. This is not supposed to ever happen")

	def reset_to_default(self):
		"""Resets all bindings to default"""
		for action in self.actions:
			default_key = horizons.globals.fife.get_keys_for_action(action, default=True)
			horizons.globals.fife.set_key_for_action(action, default_key)

		self.update_buttons_text()

	def save_settings(self):
		"""Saves the settings and reloads the keyConfiguration so that the settings take effect without a restart"""
		horizons.globals.fife.save_settings()
		self.keyconf.loadKeyConfiguration()

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()


class HotkeysListener(fife.IKeyListener):
	"""HotkeysListener Class to process events of hotkeys binding interface"""

	def __init__(self, detect_keypress):
		super().__init__()
		fife.IKeyListener.__init__(self)

		self.detect = detect_keypress

	def activate(self):
		horizons.globals.fife.eventmanager.addKeyListenerFront(self)

	def deactivate(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)

	def end(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)
		super().end()

	def keyPressed(self, evt):
		self.detect(evt)
		evt.consume()

	def keyReleased(self, evt):
		pass
