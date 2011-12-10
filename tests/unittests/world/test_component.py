#!/usr/bin/env python

# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from horizons.world.componentholder import ComponentHolder
from horizons.world.component.namedcomponent import NamedComponent, SettlementNameComponent, ShipNameComponent
from horizons.world.component.tradepostcomponent import TradePostComponent
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.world.component.healthcomponent import HealthComponent
from horizons.world.component.storagecomponent import StorageComponent
from horizons.world.production.producer import Producer
from horizons.entities import Entities
from horizons.constants import UNITS

class TestComponent(TestCase):

	def test_dependencysorting(self):
		storage = StorageComponent()
		producer = Producer()
		components = [ producer, AmbientSoundComponent(), storage]
		components.sort()
		self.assertTrue(components.index(producer) > components.index(storage))
		# Trigger __lt__
		self.assertFalse(producer < storage)
		# Trigger __gt__
		self.assertTrue(producer > storage)