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

from tests.gui import gui_test
from tests.gui.helper import *

from horizons.command.uioptions import SetTradeSlot
from horizons.component.storagecomponent import StorageComponent
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import RES

from mock import Mock

# The `gui_test` decorator is needed to identify gui tests. You can use it
# without argument, but is has to be `@gui_test()` (notice the parantheses).
#
# It accepts either one of these arguments:
#
# 	use_dev_map=True		- Game launches with --start-dev-map (no main menu)
# 	use_fixture='name'		- Game launches with --load-game=tests/gui/ingame/fixtures/name.sqlite
# 	ai_players=1			- Game launches with --ai-players=1
# 	timeout=3			- Game will be killed after 3 seconds
#
@gui_test(additional_cmdline=['--start-map', 'mp-dev'])
def test_traderoute(gui):
	"""
	"""

	ship = get_player_ship(gui.session)
	gui.select([ship])

	# Create the first settlement
	found_settlement(gui, (36, 34), (38, 39))

	# Give the resources back to the ship
	# Click the trade button
	gui.trigger('overview_trade_ship', 'trade')

	# Get the default amount (50 t, which is more than all available) of everything
	gui.trigger('buy_sell_goods', 'inventory_entry_0')
	gui.trigger('buy_sell_goods', 'inventory_entry_1')
	gui.trigger('buy_sell_goods', 'inventory_entry_2')
	gui.trigger('buy_sell_goods', 'inventory_entry_3')

	# Create the second settlement
	found_settlement(gui, (27, 28), (28, 22))

	# Open the configure trade route widget
	gui.trigger('overview_trade_ship', 'configure_route')

	# The trade route widget is visible
	assert gui.find(name='configure_route')

	# Select the first waypoint for the trade route
	event = Mock()
	event.getButton = Mock(return_value=fife.MouseEvent.LEFT)
	event.map_coords = 38, 39
	gui.session.ingame_gui._old_menu.current_tab.route_menu.on_click(event, False)

	# Select the other waypoint for the trade route
	event = Mock()
	event.getButton = Mock(return_value=fife.MouseEvent.LEFT)
	event.map_coords = 28, 22
	gui.session.ingame_gui._old_menu.current_tab.route_menu.on_click(event, False)

	# Set the resources to be loaded from settlement on the left and the amount
	gui.trigger('configure_route/container_1/slot_0', 'button', mouse='left') # Select the second warehouse's first slot
	gui.trigger('configure_route', 'resource_5') # Select meat
	gui.find('configure_route/container_1/slot_0/slider').slide(120)

	# Check if the ship obeys the state of "Wait at load" and "Wait at unload"
	assert not ship.route.wait_at_load
	gui.trigger('configure_route', 'wait_at_load')
	assert ship.route.wait_at_load
	assert not ship.route.wait_at_unload
	gui.trigger('configure_route', 'wait_at_unload')
	assert ship.route.wait_at_unload
	assert len(ship.route.waypoints) == 2
	assert Point(38, 39) in ship.route.waypoints[0]['warehouse'].position
	assert Point(28, 22) in ship.route.waypoints[1]['warehouse'].position
	assert ship.route.waypoints[1]['resource_list'] == {5: 120}
