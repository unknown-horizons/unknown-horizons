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

from unittest.mock import Mock

from fife import fife

from horizons.constants import RES
from horizons.manager import MPManager
from horizons.util.shapes import Point
from tests.gui import gui_test
from tests.gui.helper import found_settlement, get_player_ship


@gui_test(additional_cmdline=['--start-map', 'mp-dev'])
def test_traderoute(gui):
	"""Check that a ship's route is configured correctly after setting it up using the GUI."""

	ship = get_player_ship(gui.session)
	gui.select([ship])

	# Create the first settlement
	found_settlement(gui, (36, 34), (38, 39))

	# Give the resources back to the ship
	# Click the trade button
	gui.trigger('overview_trade_ship/trade')

	# Get the default amount (50 t, which is more than all available) of everything
	gui.trigger('buy_sell_goods/inventory_entry_0')
	gui.trigger('buy_sell_goods/inventory_entry_1')
	gui.trigger('buy_sell_goods/inventory_entry_2')
	gui.trigger('buy_sell_goods/inventory_entry_3')

	# Create the second settlement
	found_settlement(gui, (14, 30), (18, 28))

	# Open the configure trade route widget
	# NOTE gui of traderoute is initialized with a delay, wait a bit, see `RouteConfig.__init__`
	gui.run(MPManager.EXECUTIONDELAY + 3)
	gui.trigger('overview_trade_ship/configure_route')

	# The trade route widget is visible
	assert gui.find(name='configure_route/minimap')
	route_widget = gui.session.ingame_gui._old_menu.current_tab.route_menu

	assert not ship.route.wait_at_load
	assert not ship.route.wait_at_unload
	assert not ship.route.waypoints

	# Select the first waypoint for the trade route
	event = Mock(map_coords=(38, 39))
	event.getButton.return_value = fife.MouseEvent.LEFT
	route_widget.on_map_click(event, False)

	# Select the other waypoint for the trade route
	event = Mock(map_coords=(18, 28))
	event.getButton.return_value = fife.MouseEvent.LEFT
	route_widget.on_map_click(event, False)

	# need to give control to the rest of the code, these clicks will trigger new gui widgets
	# to be added
	gui.run()

	# Set the resources to be loaded from settlement on the left and the amount
	gui.trigger('configure_route/container_1/slot_0/button', mouse='left') # Select the second warehouse's first slot
	gui.trigger('configure_route/resources/resource_{:d}'.format(RES.FOOD))
	gui.find('configure_route/container_1/slot_0/slider').slide(120)

	# Check if the ship obeys the state of "Wait at load" and "Wait at unload"
	gui.trigger('configure_route/wait_options/wait_at_load')
	gui.trigger('configure_route/wait_options/wait_at_unload')

	assert ship.route.wait_at_load
	assert ship.route.wait_at_unload
	assert len(ship.route.waypoints) == 2
	assert Point(38, 39) in ship.route.waypoints[0]['warehouse'].position
	assert Point(18, 28) in ship.route.waypoints[1]['warehouse'].position
	assert ship.route.waypoints[1]['resource_list'] == {RES.FOOD: 120}

	# Since this test is rather complex, we test bug #2525 as well

	# open pause menu and quit
	gui.trigger('mainhud/gameMenuButton')

	def func1():
		gui.trigger('popup_window/okButton')

	with gui.handler(func1):
		gui.trigger('menu/closeButton')
