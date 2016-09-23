# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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

from __future__ import print_function

from horizons.command.uioptions import SetTradeSlot
from horizons.component.storagecomponent import StorageComponent
from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import RES
from tests.gui import gui_test
from tests.gui.helper import get_player_ship, move_ship
from tests.utils import mark_expected_failure


@mark_expected_failure
@gui_test(use_fixture='ai_settlement', timeout=60)
def test_trade(gui):
	"""
	"""

	ship = get_player_ship(gui.session)
	gui.select([ship])

	# ally players so they can trade
	world = gui.session.world
	for player in world.players:
		if player is not ship.owner:
			world.diplomacy.add_ally_pair( ship.owner, player )

	# move ship near foreign warehouse and wait for it to arrive
	move_ship(gui, ship, (68, 23))

	# click trade button
	gui.trigger('overview_trade_ship', 'trade')

	# trade widget visible
	assert gui.find(name='buy_sell_goods')

	ship_inv = ship.get_component(StorageComponent).inventory
	settlement = gui.session.world.islands[0].settlements[0]
	settlement_inv = settlement.get_component(StorageComponent).inventory

	# transfer 1 t
	gui.trigger('buy_sell_goods', 'size_1')

	old_ship_value = ship_inv[RES.BOARDS]
	old_settlement_value = settlement_inv[RES.BOARDS]

	# of boards (will be bought)
	gui.trigger('buy_sell_goods', 'inventory_entry_0')

	assert old_settlement_value + 1 == settlement_inv[RES.BOARDS]
	assert old_ship_value - 1 == ship_inv[RES.BOARDS]

	old_ship_value = ship_inv[RES.CANNON]
	old_settlement_value = settlement_inv[RES.CANNON]

	# now cannons (won't be bought)
	gui.trigger('buy_sell_goods', 'inventory_entry_3')

	assert old_settlement_value == settlement_inv[RES.CANNON]
	assert old_ship_value == ship_inv[RES.CANNON]

	# the ai has to want more boards
	trade_post = settlement.get_component(TradePostComponent)
	assert settlement_inv[RES.BOARDS] < trade_post.slots[trade_post.buy_list[RES.BOARDS]].limit

	# transfer 50 t of boards
	gui.trigger('buy_sell_goods', 'size_5')
	gui.trigger('buy_sell_goods', 'inventory_entry_0')

	# now it has enough
	assert settlement_inv[RES.BOARDS] == trade_post.slots[trade_post.buy_list[RES.BOARDS]].limit

	old_ship_value = ship_inv[RES.BOARDS]

	# so another click won't do anything
	gui.trigger('buy_sell_goods', 'inventory_entry_0')

	assert old_ship_value == ship_inv[RES.BOARDS]

	# no matter how small the amount
	gui.trigger('buy_sell_goods', 'size_1')
	gui.trigger('buy_sell_goods', 'inventory_entry_0')

	assert old_ship_value == ship_inv[RES.BOARDS]

	# make room on ship inventory
	ship_inv.alter(RES.BOARDS, - ship_inv[RES.BOARDS])

	# test sell now, give settlement something to sell
	SetTradeSlot(trade_post, 2, RES.ALVEARIES, True, 5)(settlement.owner)
	settlement.get_component(StorageComponent).inventory.alter(RES.ALVEARIES, 10)

	# this gives us 5 alevaries
	assert ship_inv[RES.ALVEARIES] == 0
	# first transfer one
	gui.trigger('buy_sell_goods', 'size_1')
	gui.trigger('buy_sell_goods', 'buy_sell_inventory_True_entry_1')

	print(ship_inv[RES.ALVEARIES])
	assert ship_inv[RES.ALVEARIES] == 1
	assert settlement_inv[RES.ALVEARIES] == 9

	# now transfer 5, should actually transfer 4
	gui.trigger('buy_sell_goods', 'size_2')
	gui.trigger('buy_sell_goods', 'buy_sell_inventory_True_entry_1')
	assert ship_inv[RES.ALVEARIES] == 5
	assert settlement_inv[RES.ALVEARIES] == 5
