# ###################################################
# Copyright (C) 2013 The Unknown Horizons Team
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


from horizons.constants import BUILDINGS
from horizons.world.disaster.blackdeathdisaster import BlackDeathDisaster

from tests.game import game_test


# FIXTURE is settlement in tier settlers with min 16 inhabitants

@game_test(use_fixture='blackdeath')
def test_blackdeath_destroy(s):
	"""
	Check if the black death destroys all settlers
	"""
	dis_man = s.world.disaster_manager
	settlement = s.world.player.settlements[0]

	# need this so that disaster  can break out
	s.world.player.settler_level = 4

	assert settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL ]
	old_num = len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL ])

	assert old_num > BlackDeathDisaster.MIN_INHABITANTS_FOR_BREAKOUT

	while not dis_man._active_disaster:
		dis_man.run() # try to seed until we have the black death

	# wait until the black death is over
	while dis_man._active_disaster:
		s.run()

	# it's not defined how bad the black death is, but some buildings should be destroyed in any case
	assert len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL ]) < old_num

