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

from horizons.component.namedcomponent import NamedComponent
from tests.gui import gui_test
from tests.gui.helper import get_player_ship


@gui_test(use_dev_map=True, timeout=60)
def test_change_name(gui):
	"""Rename a ship."""

	ship = get_player_ship(gui.session)
	old_name = ship.get_component(NamedComponent).name

	assert not gui.find(name='change_name_dialog_window')
	gui.select([ship])

	def rename():
		gui.find('new_name').write('Dagobert')
		assert gui.find(name='change_name_dialog_window')
		gui.trigger('change_name_dialog_window/okButton')

	with gui.handler(rename):
		gui.trigger('overview_trade_ship/name')

	assert not gui.find(name='change_name_dialog_window')
	new_name = ship.get_component(NamedComponent).name
	assert old_name != new_name
	assert new_name == 'Dagobert'


@gui_test(use_dev_map=True, timeout=60)
def test_change_name_empty_not_allowed(gui):
	"""Make sure an object's name can't be changed to some empty string.

	See issue #1978.
	"""
	ship = get_player_ship(gui.session)
	old_name = ship.get_component(NamedComponent).name

	gui.select([ship])

	# try empty name
	def rename_empty():
		gui.find('new_name').write('')
		gui.trigger('change_name_dialog_window/okButton')

	with gui.handler(rename_empty):
		gui.trigger('overview_trade_ship/name')

	new_name = ship.get_component(NamedComponent).name
	assert old_name == new_name

	# try name with just spaces
	def rename_spaces():
		gui.find('new_name').write('   ')
		gui.trigger('change_name_dialog_window/okButton')

	with gui.handler(rename_spaces):
		gui.trigger('overview_trade_ship/name')

	new_name = ship.get_component(NamedComponent).name
	assert old_name == new_name


@gui_test(use_dev_map=True, timeout=60)
def test_chat(gui):
	"""Opens chat dialog.

	NOTE: Doesn't test if anything was send, just checking that nothing
	crashes.
	"""

	assert not gui.find(name='chat_dialog_window')

	def func1():
		assert gui.find(name='chat_dialog_window')
		gui.trigger('chat_dialog_window/cancelButton')

	with gui.handler(func1):
		gui.press_key(gui.Key.C)

	assert not gui.find(name='chat_dialog_window')

	def func2():
		assert gui.find(name='chat_dialog_window')
		gui.find('msg').write('Hello World')
		gui.trigger('chat_dialog_window/okButton')

	with gui.handler(func2):
		gui.press_key(gui.Key.C)

	assert not gui.find(name='chat_dialog_window')
