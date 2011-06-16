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


from horizons.command.building import Build
from horizons.constants import RES

from tests.game import new_settlement, game_test


@game_test
def test_example(s, p):
	"""
	Build a farm and 2 pastures. Confirm raw wool is produced at the
	pastures and used by the farm to produce wool.
	"""
	PASTURE, FARM = 18, 20

	settlement, island = new_settlement(s)
	settlement.inventory.alter(RES.GOLD_ID, 5000)
	settlement.inventory.alter(4, 50)
	settlement.inventory.alter(6, 50)

	farm = Build(FARM, 30, 30, island, settlement=settlement)(p)
	assert farm

	# Pause the production, we want to start it explicitly later.
	production = farm._get_production(7)
	production.pause()

	# Farm has no raw wool or wool.
	assert farm.inventory[2] == 0
	assert farm.inventory[10] == 0

	# Build pastures, let the game run for 31 seconds. Pastures currently need
	# 30s to produce wool.
	p1 = Build(PASTURE, 27, 30, island, settlement=settlement)(p)
	p2 = Build(PASTURE, 33, 30, island, settlement=settlement)(p)
	assert p1 and p2

	s.run(seconds=31)

	assert p1.inventory[2]
	assert p2.inventory[2]

	# Give farm collectors a chance to get the wool from the pastures.
	s.run(seconds=5)

	assert farm.inventory[2]

	# Resume the production, let the game run for a second. The farm should have
	# produced wool now.
	production.pause(pause=False)
	s.run(seconds=1)
	assert farm.inventory[10]

