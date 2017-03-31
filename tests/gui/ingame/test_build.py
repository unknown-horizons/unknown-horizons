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

import time

from horizons.component.collectingcomponent import CollectingComponent
from horizons.constants import BUILDINGS
from horizons.world.units.collectors.collector import Collector
from tests.gui import gui_test
from tests.gui.helper import found_settlement


@gui_test(use_fixture='plain', timeout=60)
def test_found_settlement(gui):
	"""
	Found a settlement.
	"""

	player = gui.session.world.player
	assert not player.settlements

	found_settlement(gui, (68, 10), (64, 12))

	assert len(player.settlements) == 1

	# activate the build menu
	ground_map = gui.session.world.islands[0].ground_map
	gui.trigger('mainhud/build')

	# build a lumberjack
	gui.trigger('tab/button_03')
	gui.cursor_click(55, 5, 'left')
	assert(ground_map[(55, 5)].object.id == BUILDINGS.LUMBERJACK)

	# build a storage
	gui.trigger('tab/button_11')
	gui.cursor_click(55, 15, 'left')
	storage = ground_map[(55, 15)].object
	assert(storage.id == BUILDINGS.STORAGE)

	# connect the lumberjack and storage using a road
	gui.trigger('tab/button_21')
	for y in range(7, 15):
		gui.cursor_click(55, y, 'left')
		assert(ground_map[(55, y)].object.id == BUILDINGS.TRAIL)
	gui.cursor_click(55, y, 'right')

	# select the storage
	gui.cursor_click(55, 15, 'left')
	gui.trigger('tab_base/0')
	assert gui.find('tab_account')
	collectors = storage.get_component(CollectingComponent).get_local_collectors()

	while True:
		if any(collector.state is Collector.states.moving_to_target for collector in collectors):
			break
		gui.run()

	# remove the storage, trigger ticket 1441
	def func():
		assert gui.find('popup_window') is not None
		gui.trigger('popup_window/okButton')

	with gui.handler(func):
		gui.press_key(gui.Key.DELETE)

	start = time.time()
	# wait 0.5 seconds
	while time.time() - start < 0.5:
		gui.run()
	assert ground_map[(55, 15)].object is None

	# open build menu again
	gui.trigger('mainhud/build')

	# build a fisher
	gui.trigger('tab/button_23')
	gui.cursor_click(60, 4, 'left')
	fisher = ground_map[(60, 4)].object
	assert(fisher.id == BUILDINGS.FISHER)

	# connect the lumberjack and fisher using a road
	gui.trigger('tab/button_21')
	for x in range(57, 60):
		gui.cursor_click(x, 5, 'left')
		assert(ground_map[(x, 5)].object.id == BUILDINGS.TRAIL)
	gui.cursor_click(x, 5, 'right')

	# trigger ticket 1767
	# build a signal fire
	gui.trigger('tab/button_22')
	gui.cursor_click(58, 5, 'left')
	gui.cursor_click(58, 4, 'left')
