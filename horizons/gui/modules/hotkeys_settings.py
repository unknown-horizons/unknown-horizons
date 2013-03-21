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

		self.actions = ['LEFT', 'RIGHT', 'UP', 'DOWN', 'SPEED_UP']
		self.special_key_names = {fife.Key.LEFT_SHIFT : 'Shift', fife.Key.LEFT_CONTROL : 'Ctrl', fife.Key.LEFT_ALT : 'Alt'}

		self.keyconf = KeyConfig()
		self.HELPSTRING_LAYOUT = None
		self._is_displayed = False
		self._build_interface()

		self.detecting = False
		self.current_button = None
		self.current_index = None
		self.last_combination = []

		self.widget.mapEvents({self.widget.name + '/keyPressed' : self._detect_keypress})

		self.keys = self.keyconf.get_keys_by_value()

		# self.widget.findChild(name=OkButton.DEFAULT_NAME).capture(self._windows.close)

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

	def _create_label(self, action):
			text = _('lbl_{action_name}'.format(action_name=action))
			label = Label(text=text)
			label.max_size = (130,42)
			return label

	def _create_button(self, action, prefix, index):
			keyname = _(self.keyconf.get_current_keys(action)[0])
			button = Button(text=keyname)
			button.name = str(index)
			button.max_size = (130,19)
			return button

	def _detect_click_on_button(self, button):
			self.detecting = True
			self.current_button = button
			self.current_index = int(button.name)
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

	def apply_change(self):
			key = self.last_combination[0]
			dct = self.keyconf.keyval_action_mappings
			if not dct.get(key.getValue()):
					horizons.globals.fife.set_key_for_action(self.actions[self.current_index], self.keyName(key))
					print 'Binded ' + self.keyName(key) + ' to ' + self.actions[self.current_index]
					horizons.globals.fife.save_settings()
			else:
					print 'ID: ' + str(dct.get(key.getValue()))
					# oldaction = dct.get(key.getValue())
					# horizons.globals.fife.set_key_for_action(oldaction, "LEFT")
					# horizons.globals.fife.set_key_for_action(self.actions[self.current_index], self.keyName(key))
			self.current_button.text = _(self.keyName(self.last_combination[0]))
			self.last_combination = []

	def show(self):
			self.widget.show()

	def hide(self):
			self.widget.hide()
