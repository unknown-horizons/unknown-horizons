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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
# ###################################################

from typing import Optional

from horizons.component.tradepostcomponent import TradePostComponent
from horizons.constants import RES
from horizons.scheduler import Scheduler
from horizons.world.storage import GenericStorage


class TestTradePostComponent:
    """
    TODO: buy_resource, sell_resource (needs ships and player concept)
    """

    def setup_method(self):
        self.inventory = GenericStorage()
        self.owner_inventory = GenericStorage()

        class Instance:
            def __init__(self, comp):
                self.comp = comp
                self.owner = None  # type: Optional["Instance"]

            def get_component(self, _):
                class Comp:
                    inventory = self.comp

                return Comp()

        self.tradepost = TradePostComponent()
        self.tradepost.instance = Instance(self.inventory)
        self.tradepost.instance.owner = Instance(self.owner_inventory)
        self.tradepost.initialize()

        class Timer:
            def add_call(self, _):
                pass

            def get_ticks(self, _):
                return 100

        Scheduler.create_instance(timer=Timer())

    def teardown_method(self):
        Scheduler.destroy_instance()

    def test_buy(self):
        self.owner_inventory.alter(RES.GOLD, 1)

        assert not self.tradepost.buy(1, 1, 1, 100)

        self.tradepost.set_slot(0, 1, False, 2)

        assert self.tradepost.buy(1, 1, 1, 100)
        assert self.tradepost.buy_expenses == 1

        Scheduler().cur_tick += 1

        # ran out of money
        assert not self.tradepost.buy(1, 1, 1, 100)

        self.owner_inventory.alter(RES.GOLD, 2)

        assert self.tradepost.buy(1, 1, 1, 100)

        Scheduler().cur_tick += 1

        # only wanted to buy 2
        assert not self.tradepost.buy(1, 1, 1, 100)

        self.inventory.alter(1, -2)

        assert self.tradepost.buy(1, 1, 1, 100)

        self.tradepost.clear_slot(0, True)

        # not buying any more
        assert not self.tradepost.buy(1, 1, 1, 100)

        assert self.tradepost.buy_expenses == 3
        assert self.tradepost.total_expenses == 3

    def test_sell(self):
        self.inventory.alter(1, 1)

        assert not self.tradepost.sell(1, 1, 1, 100)

        self.tradepost.set_slot(0, 1, True, 0)  # sell until 0

        assert self.tradepost.sell(1, 1, 1, 100)
        assert self.tradepost.sell_income == 1

        Scheduler().cur_tick += 1

        # ran out of resources
        assert not self.tradepost.sell(1, 1, 1, 100)

        Scheduler().cur_tick += 1

        self.inventory.alter(1, 1)

        assert self.tradepost.sell(1, 1, 1, 100)

        self.tradepost.clear_slot(0, True)

        # not selling any more
        assert not self.tradepost.sell(1, 1, 1, 100)

        assert self.tradepost.sell_income == 2
        assert self.tradepost.total_earnings == 2
