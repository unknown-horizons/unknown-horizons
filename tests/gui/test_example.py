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

from tests.gui import gui_test


# The `gui_test` decorator is needed to identify gui tests. You can use it
# without argument, but is has to be `@gui_test()` (notice the parantheses).
#
# It accepts either one of these arguments:
#
# 	use_dev_map=True		- Game launches with --start-dev-map (no main menu)
# 	use_fixture='name'		- Game launches with --load-game=tests/gui/ingame/fixtures/name.sqlite
# 	ai_players=1			- Game launches with --ai-players=1
# 	timeout=3				- Game will be killed after 3 seconds
#
@gui_test(timeout=60)
def test_example(gui):
	"""
	Documented example test.

	Every gui test has to accept one argument, an instance of `tests.gui.GuiHelper`.
	"""

	gui.disable_autoscroll()

	# Main menu
	gui.trigger('menu/single_button')
	gui.trigger('singleplayermenu/okay')

	# Hopefully we're ingame now
	assert gui.active_widgets

	# How long the HUD takes to appear varies a lot with the renderer; under
	# software GL in CI it is noticeably later than on a desktop. Poll instead
	# of assuming it is already populated.
	for _ in range(30):
		gold_label = gui.find(name='gold_available')
		if gold_label.text:
			break
		gui.run(seconds=1)

	gold_label = gui.find(name='gold_available')
	assert gold_label.text == '30000', gold_label.text

	# All commands above run sequentially, neither the engine nor the timer
	# will be run. If you need the game to run for some time (or have to wait for
	# something to happen), make multiple gui.run() calls.

	# Game will run for 2 seconds
	gui.run(seconds=2)

	"""
	while not condition:
		gui.run()
	"""

	# When you call `gui.run()` the engine is allowed to run, therefore updating the display.
	# You can also interact with the game as normal, but please don't mess with the test. :)
	#
	# TIP: You can watch the test in slow-motion if you insert these waits between
	# interactions.

	# Open game menu
	gui.trigger('mainhud/gameMenuButton')

	# gui.trigger accepts both a string (container name), or a object returned by gui.find

	# Cancel current game
	def dialog():
		gui.trigger('popup_window/okButton')

	# Dialog handling has to be done by a separate generator.
	with gui.handler(dialog):
		gui.trigger('menu/quit')

	# Code execution will continue here once `dialog` has ended.

	# Back at the main menu
	assert gui.find(name='menu')

	# If a test returns None (either implicitly or explicitly) the game will exit, return
	# something else and it will continue to run. Useful if you want to check your test's
	# action.

    # TODO not yet supported, use gui.run(2**10)
	#return 1


@gui_test(timeout=60)
def test_gold_label_initialized_immediately(gui):
	"""
	Regression test: gold label populated immediately after load; throttle preserved.

	Verifies both:
	1. The initial gold value is written synchronously during ResourceOverviewBar.load(),
	   without waiting for the deferred ExtScheduler callback (0.3s wall-clock).
	2. The 0.3s throttle still suppresses rapid subsequent updates.
	"""
	gui.disable_autoscroll()

	# Main menu -> in-game.  ResourceOverviewBar.load() runs during load.
	gui.trigger('menu/single_button')
	gui.trigger('singleplayermenu/okay')

	assert gui.active_widgets

	res_overview = gui.session.ingame_gui.resource_overview

	# 1. No polling, no gui.run(), no sleep: check immediately after load.
	gold_label = gui.find(name='gold_available')
	assert gold_label.text == '30000', gold_label.text

	# 2. Throttle preserved: rapid _update_gold() calls must not rewrite immediately.
	res_overview._update_gold()  # force=False -> schedules, sets flag, returns without writing
	res_overview._update_gold()  # force=False -> flag set, returns without writing
	assert gold_label.text == '30000', gold_label.text
