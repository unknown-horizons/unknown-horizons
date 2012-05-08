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


from unittest import TestCase

from horizons.constants import RES
from horizons.scheduler import Scheduler
from horizons.world.storage import GenericStorage
from horizons.component.tradepostcomponent import TradePostComponent

class TestTradePostComponent(TestCase):
	"""
	TODO: buy_resource, sell_resource (needs ships and player concept)
	"""

	def setUp(self):
		self.inventory = GenericStorage()
		self.owner_inventory = GenericStorage()

		class Instance(object):
			def __init__(self, comp):
				self.comp = comp
			def get_component(self, x):
				class Comp(object):
					inventory = self.comp
				return Comp()

		self.tradepost = TradePostComponent()
		self.tradepost.instance = Instance(self.inventory)
		self.tradepost.instance.owner = Instance(self.owner_inventory)
		self.tradepost.initialize()

		class Timer(object):
			def add_call(self, x):
				pass
			def get_ticks(self, x):
				return 100
		Scheduler.create_instance(timer=Timer())

	def tearDown(self):
		Scheduler.destroy_instance()

	def test_buy(self):
		self.owner_inventory.alter(RES.GOLD, 1)
		self.assertFalse( self.tradepost.buy(1, 1, 1, 100) )
		self.tradepost.add_to_buy_list(1, 2)
		self.assertTrue( self.tradepost.buy(1, 1, 1, 100) )
		self.assertEqual( self.tradepost.buy_expenses, 1 )

		Scheduler().cur_tick += 1

		# ran out of money
		self.assertFalse( self.tradepost.buy(1, 1, 1, 100) )

		self.owner_inventory.alter(RES.GOLD, 2)
		self.assertTrue( self.tradepost.buy(1, 1, 1, 100) )

		Scheduler().cur_tick += 1

		# only wanted to buy 2
		self.assertFalse( self.tradepost.buy(1, 1, 1, 100) )

		self.inventory.alter(1, -2)
		self.assertTrue( self.tradepost.buy(1, 1, 1, 100) )

		self.tradepost.remove_from_buy_list(1)
		# not buying any more
		self.assertFalse( self.tradepost.buy(1, 1, 1, 100) )
		self.assertEqual( self.tradepost.buy_expenses, 3 )
		self.assertEqual( self.tradepost.total_expenses, 3 )

	def test_sell(self):
		self.inventory.alter(1, 1)
		self.assertFalse( self.tradepost.sell(1, 1, 1, 100) )
		self.tradepost.add_to_sell_list(1, 0) # sell until 0
		self.assertTrue( self.tradepost.sell(1, 1, 1, 100) )
		self.assertEqual( self.tradepost.sell_income, 1 )

		Scheduler().cur_tick += 1

		# ran out of res
		self.assertFalse( self.tradepost.sell(1, 1, 1, 100) )

		Scheduler().cur_tick += 1

		self.inventory.alter(1, 1)
		self.assertTrue( self.tradepost.sell(1, 1, 1, 100) )


		self.tradepost.remove_from_sell_list(1)
		# not selling any more
		self.assertFalse( self.tradepost.sell(1, 1, 1, 100) )
		self.assertEqual( self.tradepost.sell_income, 2 )
		self.assertEqual( self.tradepost.total_earnings, 2 )





