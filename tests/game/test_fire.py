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


from horizons.constants import RES, BUILDINGS
from horizons.command.building import Build, Tear
from horizons.world.component.storagecomponent import StorageComponent

from tests.game import game_test


# FIXTURE is settlement with some food, main square and ~8 settlers
# a lumberjack is placed somewhere, where a fire station would be useful

@game_test(use_fixture='fire')
def test_fire_destroy(s):
	"""
	Check if a fire destroys all settlers
	"""
	dis_man = s.world.disaster_manager
	settlement = s.world.player.settlements[0]

	# need this so that fires can break out
	s.world.player.settler_level = 1

	assert len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL_CLASS ]) > 0
	old_num = len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL_CLASS ])

	while not dis_man._active_disaster:
		dis_man.run() # try to seed until we have a fire

	# wait until fire is over
	while dis_man._active_disaster:
		s.run()

	# it's not defined how bad a fire is, but some buildings should be destroyed in any case
	assert len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL_CLASS ]) < old_num


@game_test(use_fixture='fire')
def test_fire_station(s):
	"""
	Check if a fire station stops fires.
	"""
	dis_man = s.world.disaster_manager
	settlement = s.world.player.settlements[0]
	# need this so that fires can break out
	s.world.player.settler_level = 1

	inv = settlement.get_component(StorageComponent).inventory
	# res for fire station
	inv.alter(RES.BOARDS_ID, 10)
	inv.alter(RES.TOOLS_ID, 10)
	inv.alter(RES.BRICKS_ID, 10)

	# second lj is the pos we need
	lj = settlement.buildings_by_id[ BUILDINGS.LUMBERJACK_CLASS ][1]
	pos = lj.position.origin
	owner = lj.owner
	island = lj.island

	Tear(lj)(owner)
	assert Build(BUILDINGS.FIRE_STATION_CLASS, pos.x, pos.y, island, settlement=settlement)(owner)

	assert len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL_CLASS ]) > 0
	old_num = len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL_CLASS ])

	for i in xrange(5): # 5 fires
		while not dis_man._active_disaster:
			dis_man.run() # try to seed until we have a fire

		# wait until fire is over
		while dis_man._active_disaster:
			s.run()

	# in this simple case, the fire station should be 100% effective
	assert len(settlement.buildings_by_id[ BUILDINGS.RESIDENTIAL_CLASS ]) == old_num
