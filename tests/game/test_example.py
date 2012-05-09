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


from horizons.command.building import Build
from horizons.constants import RES, BUILDINGS, PRODUCTIONLINES
from horizons.component.storagecomponent import StorageComponent
from horizons.world.production.producer import Producer

from tests.game import game_test, settle


@game_test
def test_example(s, p):
	"""
	Build a farm and 2 pastures. Confirm raw wool is produced at the
	pastures and used by the farm to produce wool.
	"""
	settlement, island = settle(s)

	farm = Build(BUILDINGS.FARM, 30, 30, island, settlement=settlement)(p)
	assert farm

	# Pause the production, we want to start it explicitly later.
	production = farm.get_component(Producer)._get_production(PRODUCTIONLINES.WOOL)
	production.pause()

	# Farm has no raw wool or wool.
	assert farm.get_component(StorageComponent).inventory[RES.LAMB_WOOL] == 0
	assert farm.get_component(StorageComponent).inventory[RES.WOOL] == 0

	# Build pastures, let the game run for 31 seconds. Pastures currently need
	# 30s to produce wool.
	p1 = Build(BUILDINGS.PASTURE, 27, 30, island, settlement=settlement)(p)
	p2 = Build(BUILDINGS.PASTURE, 33, 30, island, settlement=settlement)(p)
	assert p1 and p2

	s.run(seconds=31)

	assert p1.get_component(StorageComponent).inventory[RES.LAMB_WOOL]
	assert p2.get_component(StorageComponent).inventory[RES.LAMB_WOOL]

	# Give farm collectors a chance to get the wool from the pastures.
	s.run(seconds=5)

	assert farm.get_component(StorageComponent).inventory[RES.LAMB_WOOL]

	# Resume the production, let the game run for a second. The farm should have
	# produced wool now.
	production.pause(pause=False)
	s.run(seconds=1)
	assert farm.get_component(StorageComponent).inventory[RES.WOOL]

