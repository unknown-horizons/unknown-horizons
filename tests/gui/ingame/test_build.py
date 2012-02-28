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

import time

from horizons.constants import BUILDINGS
from horizons.command.unit import Act
from horizons.world.units.collectors.collector import Collector
from horizons.gui.mousetools.buildingtool import BuildingTool
from horizons.gui.mousetools.cursortool import CursorTool
from horizons.world.component.collectingcompontent import CollectingComponent
from tests.gui import TestFinished, gui_test
from tests.gui.helper import get_player_ship


@gui_test(use_dev_map=True, timeout=60)
def test_found_settlement(gui):
	"""
	Found a settlement.
	"""
	yield # test needs to be a generator for now

	player = gui.session.world.player
	target = (68, 10)
	gui.session.view.center(*target)

	assert len(player.settlements) == 0

	ship = get_player_ship(gui.session)
	Act(ship, *target)(player)

	# wait until ship arrives
	while (ship.position.x, ship.position.y) != target:
		yield

	gui.select([ship])
	gui.trigger('overview_trade_ship', 'found_settlement/action/default')

	assert isinstance(gui.cursor, BuildingTool)
	gui.cursor_move(64, 12)
	gui.cursor_click(64, 12, 'left')

	assert isinstance(gui.cursor, CursorTool)
	assert len(player.settlements) == 1

	# activate the build menu
	ground_map = gui.session.world.islands[0].ground_map
	gui.trigger('mainhud', 'build/action/default')

	# build a lumberjack
	gui.trigger('tab', 'button_5/action/default')
	gui.cursor_click(55, 5, 'left')
	assert(ground_map[(55, 5)].object.id == BUILDINGS.LUMBERJACK_CLASS)

	# build a storage
	gui.trigger('tab', 'button_2/action/default')
	gui.cursor_click(55, 15, 'left')
	storage = ground_map[(55, 15)].object
	assert(storage.id == BUILDINGS.STORAGE_CLASS)

	# connect the lumberjack and storage using a road
	gui.trigger('tab', 'button_21/action/default')
	for y in xrange(7, 15):
		gui.cursor_click(55, y, 'left')
		assert(ground_map[(55, y)].object.id == BUILDINGS.TRAIL_CLASS)
	gui.cursor_click(55, y, 'right')

	# select the storage
	gui.cursor_click(55, 15, 'left')
	assert gui.find('warehouse_and_storage_overview')
	collectors = storage.get_component(CollectingComponent).get_local_collectors()

	while True:
		if any(collector.state is Collector.states.moving_to_target for collector in collectors):
			break
		yield

	# remove the storage, trigger ticket 1441
	gui.press_key(gui.Key.DELETE)
	start = time.time()
	# wait 0.5 seconds
	while time.time() - start < 0.5:
		yield
	assert ground_map[(55, 15)].object is None

	yield TestFinished
