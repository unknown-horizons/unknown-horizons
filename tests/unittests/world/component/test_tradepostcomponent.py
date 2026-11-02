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


from horizons.component.tradepostcomponent import TRADE_ERROR_TYPE, TradePostComponent
from horizons.constants import RES
from horizons.scheduler import Scheduler
from horizons.util.worldobject import WorldObject
from horizons.world.storage import GenericStorage


class FakeDB:
    def get_res_value(self, resource_id):
        return 10


class FakeMessageWidget:
    def add_custom(self, *args, **kwargs):
        pass


class FakeIngameGUI:
    def __init__(self):
        self.message_widget = FakeMessageWidget()


class FakeSession:
    def __init__(self):
        self.db = FakeDB()
        self.ingame_gui = FakeIngameGUI()

class FakePlayer:
    def __init__(self):
        self.worldid = 100
        self.is_local_player = False
        self.storage = GenericStorage()

    def get_component(self, _):
        class Comp:
            pass

        c = Comp()
        c.inventory = self.storage
        return c

class FakeShip:
    def __init__(self, owner):
        self.owner = owner
        self.position = None
        self.storage = GenericStorage()

    def get_component(self, _):
        class Comp:
            pass

        c = Comp()
        c.inventory = self.storage
        return c

class TestTradePostComponent:

    def setup_method(self):
        self.inventory = GenericStorage()
        self.owner_inventory = GenericStorage()

        class Instance:
            def __init__(self, comp):
                self.comp = comp
                self.owner = None

            def get_component(self, _):
                class Comp:
                    inventory = self.comp

                return Comp()

        self.tradepost = TradePostComponent()
        self.tradepost.instance = Instance(self.inventory)
        self.tradepost.instance.owner = Instance(self.owner_inventory)

        session = FakeSession()
        self.tradepost.instance.session = session
        self.tradepost.instance.owner.session = session

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

    def test_get_free_slot(self):
        assert self.tradepost.get_free_slot(1) == 0

        self.tradepost.set_slot(0, 1, False, 10)

        # existing resource returns the same slot
        assert self.tradepost.get_free_slot(1) == 0

        # first free slot
        assert self.tradepost.get_free_slot(2) == 1

        self.tradepost.set_slot(1, 2, True, 5)
        self.tradepost.set_slot(2, 3, False, 5)

        # no free slots left
        assert self.tradepost.get_free_slot(4) is None

    def test_trade_history(self):
        self.owner_inventory.alter(RES.GOLD, 10)

        self.tradepost.set_slot(0, 1, False, 10)

        Scheduler().cur_tick = 5

        self.tradepost.buy(1, 2, 2, 100)

        assert len(self.tradepost.trade_history) == 1

        tick, player, res, amount, gold = self.tradepost.trade_history[0]

        assert tick == 5
        assert player == 100
        assert res == 1
        assert amount == 2
        assert gold == -2

    def test_buy_expenses_removes_old_entries(self):
        self.tradepost.buy_history = {
            1: (1, 1, 5),
            150: (1, 1, 10),
        }

        Scheduler().cur_tick = 200

        assert self.tradepost.buy_expenses == 10
        assert 1 not in self.tradepost.buy_history
        assert 150 in self.tradepost.buy_history

    def test_sell_income_removes_old_entries(self):
        self.tradepost.sell_history = {
            1: (1, 1, 5),
            150: (1, 1, 10),
        }

        Scheduler().cur_tick = 200

        assert self.tradepost.sell_income == 10
        assert 1 not in self.tradepost.sell_history
        assert 150 in self.tradepost.sell_history

    def test_buy_resource_success(self, monkeypatch):
        self.tradepost.set_slot(0, 1, False, 10)

        self.owner_inventory.alter(RES.GOLD, 100)

        seller = FakePlayer()

        ship = FakeShip(seller)
        ship.storage.alter(1, 5)

        monkeypatch.setattr(
            WorldObject,
            "get_object_by_id",
            lambda _: ship
        )

        self.tradepost.buy_resource(
            1,  # ship id
            1,  # resource
            3
        )

        assert self.inventory[1] == 3
        assert ship.storage[1] == 2

    def test_buy_resource_not_in_buy_list(self, monkeypatch):
        seller = FakePlayer()
        ship = FakeShip(seller)

        monkeypatch.setattr(
            WorldObject,
            "get_object_by_id",
            lambda _: ship
        )

        amount, error = self.tradepost.buy_resource(
            1,
            1,
            1,
            add_error_type=True
        )

        assert amount == 0
        assert error == TRADE_ERROR_TYPE.PERMANENT

    def test_sell_resource_limit_reached(self, monkeypatch):
        self.inventory.alter(1, 5)

        self.tradepost.set_slot(0, 1, True, 5)

        buyer = FakePlayer()
        buyer.storage.alter(RES.GOLD, 100)

        ship = FakeShip(buyer)

        monkeypatch.setattr(
            WorldObject,
            "get_object_by_id",
            lambda _: ship
        )

        amount, error = self.tradepost.sell_resource(
            1,
            1,
            2,
            add_error_type=True
        )

        assert amount == 0
        assert error == TRADE_ERROR_TYPE.TEMPORARY

    def test_total_expenses_uses_trade_price(self):
        self.owner_inventory.alter(RES.GOLD, 10)

        self.tradepost.set_slot(0, 1, False, 10)

        self.tradepost.buy(1, 2, 4, 100)

        assert self.tradepost.total_expenses == 4

    def test_total_income_uses_trade_price(self):
        self.inventory.alter(1, 2)

        self.tradepost.set_slot(0, 1, True, 0)

        self.tradepost.sell(1, 2, 4, 100)

        assert self.tradepost.total_income == 4
