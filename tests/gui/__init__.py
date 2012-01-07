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


class GuiHelper(object):

	def __init__(self, pychan):
		self._pychan = pychan
		self._manager = self._pychan.manager

	@property
	def active_widgets(self):
		return self._manager.allWidgets.keys()

	def find(self, name):
		"""Find a container by name."""
		for w in self.active_widgets:
			if w.name == name:
				return w
		return None

	def trigger(self, root, event):
		"""Trigger a widget event in a container.

		root  - container that holds the widget
		event - string describing the event
		"""
		widget_name, event_name, group_name = event.split('/')
		widget = root.findChild(name=widget_name)
		callback = widget.event_mapper.callbacks[group_name][event_name]
		callback()


def test_mainmenu(gui):
	yield # test needs to be a generator for now

	# Main menu
	assert len(gui.active_widgets) == 1
	main_menu = gui.active_widgets[0]
	gui.trigger(main_menu, 'startSingle/action/default')

	# Single-player menu
	assert len(gui.active_widgets) == 1
	singleplayer_menu = gui.active_widgets[0]
	# Start a game
	gui.trigger(singleplayer_menu, 'okay/action/default')

	# Hopefully we're ingame now
	assert len(gui.active_widgets) == 4
	# Check gold display
	gold_display = gui.find(name='status_gold')
	assert gold_display.findChild(name='gold_1').text == '30000'

	# Open game menu
	hud = gui.find(name='mainhud')
	gui.trigger(hud, 'gameMenuButton/action/default')
	game_menu = gui.find(name='menu')

	# canceling the game opens a dialog, which breaks our code..
	# Cancel current game
	# gui.trigger(game_menu, 'quit/action/default')
	# Back at the main menu
	# assert len(gui.active_widgets) == 1


class TestRunner(object):
	"""
	I assumed it would be necessay to run the test 'in parallel' to the
	engine, e.g. click a button, let the engine run, click another button.
	That's why the TestRunner installs its _tick method into engine.pump, to
	be called once in a while. The test is a generator to make use of yield
	to allow the test to give up control to the engine.

	For the above example it is not necessary, but it might be needed later on,
	so let's leave it that way for now.
	"""
	def __init__(self, engine):
		self._engine = engine

		test = test_mainmenu
		self._test_name = test.__name__
		self._test = test(GuiHelper(self._engine.pychan))
		self.start()

	def start(self):
		print "Test '%s' started" % self._test_name
		self._engine.pump.append(self._tick)

	def stop(self):
		self._engine.pump.remove(self._tick)
		self._engine.quit()

	def _tick(self):
		try:
			self._test.next()
		except StopIteration:
			print "Test finished"
			self.stop()
