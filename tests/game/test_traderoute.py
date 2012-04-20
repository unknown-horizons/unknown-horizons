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


from horizons.component.namedcomponent import NamedComponent
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import RES

from tests.game import game_test


@game_test(use_fixture='traderoute')
def test_traderoute_basic(s):
	"""
	Check if traderoutes do anything.
	"""
	settlements = s.world.player.settlements
	assert len(settlements) == 2

	# 2 settlements, one produces food, the other one boards
	# a traderoute is there to exchange the res

	has_food = settlements[0] if 'food' in settlements[0].get_component(NamedComponent).name else settlements[1]
	has_wood = settlements[0] if settlements[0] != has_food else settlements[1]

	food_inv = has_food.get_component(StorageComponent).inventory
	wood_inv = has_wood.get_component(StorageComponent).inventory

	assert food_inv[RES.FOOD] > 0
	assert wood_inv[RES.BOARDS] > 0

	while food_inv[RES.BOARDS] == 0: # first ensure wood to food
		s.run()
	while wood_inv[RES.FOOD] == 0: # traderoute also goes other way around
		s.run()

	while food_inv.get_free_space_for(RES.BOARDS) > 0: # also fill up
		s.run()
	while wood_inv.get_free_space_for(RES.FOOD) > 0: # also fill up
		s.run()

	# when the whiles pass, it is ensured that traderoutes somewhat work
