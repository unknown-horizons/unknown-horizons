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

from fife import fife
from fife.extensions.pychan.widgets import Button, Label

import horizons.globals
from horizons.gui.keylisteners.ingamekeylistener import KeyConfig
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import OkButton
from horizons.gui.windows import Window
from horizons.messaging import LanguageChanged
from horizons.util.living import LivingObject
from horizons.util.python.callback import Callback

class HotkeyConfiguration(object):

	def __init__(self):
		super(HotkeyConfiguration, self).__init__()

		self.widget = load_uh_widget('hotkeys.xml')
		self.buttons = []
		self.secondary_buttons = []

		self.keyconf = KeyConfig()
		self.actions = self.keyconf.get_bindable_actions_by_name()
		self.keys = self.keyconf.get_keys_by_value()

		self.HELPSTRING_LAYOUT = None
		self._is_displayed = False
		self._build_interface()

		self.detecting = False
		self.current_button = None
		self.current_index = None
		self.last_combination = []
		self.last_column = 1

		# There are some keys which are not detected by the event widget/keyPressed
		# In that case, the key presses are detected by the listener, which calls _detect_keypress
		self.listener = HotkeysListener(self._detect_keypress)

		self.widget.mapEvents({self.widget.name + '/keyPressed' : self._detect_keypress})
		self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self.save_settings)
		self.widget.mapEvents({OkButton.DEFAULT_NAME : self.save_settings})
		self.widget.findChild(name="reset_to_default").capture(self.reset_to_default)

	def _build_interface(self):
		container = self.widget.findChild(name='keys_container')
		button_container = self.widget.findChild(name='button_container')
		sec_button_container = self.widget.findChild(name='sec_button_container')
		for i, action in enumerate(self.actions):
			button = self._create_button(action, 0, i)
			button2 = self._create_button(action, 1, i)
			button.mapEvents({button.name + '/mouseClicked' : Callback(self._detect_click_on_button, button, 1)})
			button2.mapEvents({button.name + '/mouseClicked' : Callback(self._detect_click_on_button, button2, 2)})
			button_container.addChild(button)
			sec_button_container.addChild(button2)
			self.buttons.append(button)
			self.secondary_buttons.append(button2)
			self.update_buttons_text()

	def _create_button(self, action, action_index, index):
		current_binding = self.keyconf.get_current_keys(action)

		if len(current_binding) <= action_index:
				# if there are less bindings than buttons
				keyname = "-"
		else:
				keyname = current_binding[action_index]

		#xgettext:python-format
		button = Button()
		button.name = str(index)
		button.max_size = (130,18)
		return button

	def _detect_click_on_button(self, button, column):
		self.detecting = True
		self.current_button = button
		self.current_index = int(button.name)
		self.current_column = column
		#xgettext:python-format
		button.text = _("Press desired key")

	def _detect_keypress(self, event):
		if self.detecting:
			key = event.getKey()
			# if the key is not supported, act as if it was not detected
			if not self.keyName(key):
				return
			self.last_combination.append(key)
			self.detecting = False
			self.apply_change()

	def update_buttons_text(self):
		for i, button in enumerate(self.buttons):
			action = self.actions[i]
			bindings = self.keyconf.get_current_keys(action)
			for j in range(len(bindings)):
				if bindings[j] == 'UNASSIGNED':
					bindings[j] = '-'
			secondary_button = self.secondary_buttons[i]
			button.text = _(bindings[0])
			if len(bindings) > 1:
				secondary_button.text = _(bindings[1])
			else:
				secondary_button.text = _("-")

	def apply_change(self):
		key = self.last_combination[0]
		key_name = self.keyName(key)
		action = self.actions[self.current_index]
		column = self.current_column

		if key_name == 'ESCAPE':
			key_name = 'UNASSIGNED'

		elif self.key_is_set(key):
			oldaction = self.get_action_name(key)
			#xgettext:python-format
			message = _("{key} is already set to {action}. Whould you like to overwrite it?").format(
					                      key=key_name, action=oldaction)
			#if self._windows.show_popup(_("Confirmation for overwriting"), message, show_cancel_button=True, modal=False):
			#	horizons.globals.fife.replace_key_for_action(oldaction, key_name, "UNASSIGNED")
			#else:
			#	self.update_buttons_text()
			#	self.last_combination = []
			#	return

		bindings = self.keyconf.get_current_keys(action)
		if column == 1:
			bindings[0] = key_name
		if column == 2:
			if len(bindings) < 2:
				bindings.append(key_name)
			else:
				bindings[1] = key_name

		horizons.globals.fife.set_key_for_action(action, bindings)

		self.update_buttons_text()
		self.last_combination = []

	def keyName(self, key):
		value = key.getValue()
		return self.keys.get(value)

	def key_is_set(self, key):
		key_name = self.keyName(key)
		custom_key_actions = horizons.globals.fife.get_hotkey_settings()
		for k in custom_key_actions.itervalues():
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
		key_name = self.keyName(key)
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

		self.update_buttons_text()

	def save_settings(self):
		horizons.globals.fife.save_settings()
		self.keyconf.loadKeyConfiguration()
		#self._windows.close()

	def show(self):
		self.widget.show()
		self.listener.activate()

	def hide(self):
		self.widget.hide()
		self.listener.deactivate()


class HotkeysListener(fife.IKeyListener):
	"""HotkeysListener Class to process events of hotkeys binding interface"""

	def __init__(self, detect_keypress):
		super(HotkeysListener, self).__init__()
		fife.IKeyListener.__init__(self)

		self.detect = detect_keypress

	def activate(self):
		horizons.globals.fife.eventmanager.addKeyListenerFront(self)

	def deactivate(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)

	def end(self):
		horizons.globals.fife.eventmanager.removeKeyListener(self)
		super(HotkeysListener, self).end()

	def keyPressed(self, evt):
		self.detect(evt)
		evt.consume()

	def keyReleased(self, evt):
		pass
