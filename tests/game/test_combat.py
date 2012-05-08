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

import tempfile
import os

from horizons.util import Color, WorldObject
from horizons.util.worldobject import WorldObjectNotFound
from horizons.command.unit import CreateUnit, Attack
from horizons.command.diplomacy import AddEnemyPair, AddNeutralPair, AddAllyPair
from horizons.command.uioptions import EquipWeaponFromInventory, UnequipWeaponToInventory
from horizons.component.storagecomponent import StorageComponent
from horizons.world.player import Player
from horizons.constants import UNITS, WEAPONS
from horizons.component.healthcomponent import HealthComponent

from tests.game import game_test, new_session, load_session

def setup_combat(s, ship):
	worldid = 10000000

	p0 = Player(s, worldid, "p1", Color[1])
	p1 = Player(s, worldid+1, "p2", Color[2])

	for p in (p0, p1):
		p.initialize(None)
		s.world.players.append(p)

	s0 = CreateUnit(p0.worldid, ship, 0, 0)(issuer=p0)
	s1 = CreateUnit(p1.worldid, ship, 3, 3)(issuer=p1)

	return ((p0, s0), (p1, s1))

def health(thing):
	return thing.get_component(HealthComponent).health
def max_health(thing):
	return thing.get_component(HealthComponent).max_health
def one_dead(wid1, wid2):
	for wid in (wid1, wid2):
		at_least_one_dead = False
		try:
			WorldObject.get_object_by_id(wid)
		except WorldObjectNotFound:
			at_least_one_dead = True
	return at_least_one_dead




@game_test
def test_noncombat_units(s, p):
	return

	(p0, s0), (p1, s1) = setup_combat(s, UNITS.HUKER_SHIP)

	# healthy before
	assert health(s0) == max_health(s0)
	assert health(s1) == max_health(s1)

	assert len(s.world.ships) == 3 # trader also has a ship
	Attack(s0, s1).execute(s)

	s.run(seconds=60)

	# healthy after
	assert health(s0) == max_health(s0)
	assert health(s1) == max_health(s1)

@game_test
def test_equip(s, p):
	return

	assert WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM > 0, "This test only makes sense with default cannons. Adapt this if you don't want default cannons."

	(p0, s0), (p1, s1) = setup_combat(s, UNITS.FRIGATE)

	assert s0.get_component(StorageComponent).inventory[ WEAPONS.CANNON ] == 0
	assert s0.get_weapon_storage()[ WEAPONS.CANNON ] == WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM

	# we don't have daggers
	not_equip = EquipWeaponFromInventory(s0, WEAPONS.DAGGER, 1).execute(s)
	assert not_equip == 1
	assert s0.get_component(StorageComponent).inventory[ WEAPONS.DAGGER ] == 0
	assert s0.get_weapon_storage()[ WEAPONS.DAGGER ] == 0

	# test equip
	s0.get_component(StorageComponent).inventory.alter( WEAPONS.CANNON, 2 )

	# this has to work
	not_equip = EquipWeaponFromInventory(s0, WEAPONS.CANNON, 1).execute(s)
	assert not_equip == 0

	assert s0.get_component(StorageComponent).inventory[ WEAPONS.CANNON ] == 1
	assert s0.get_weapon_storage()[WEAPONS.CANNON] == WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM + 1

	# too many
	not_equip = EquipWeaponFromInventory(s0, WEAPONS.CANNON, 2).execute(s)

	assert not_equip == 1
	assert s0.get_component(StorageComponent).inventory[ WEAPONS.CANNON ] == 0
	assert s0.get_weapon_storage()[WEAPONS.CANNON] == WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM + 2

	# no daggers
	not_equip = UnequipWeaponToInventory(s0, WEAPONS.DAGGER, 2).execute(s)
	assert not_equip == 2

	not_equip = UnequipWeaponToInventory(s0, WEAPONS.CANNON, 2).execute(s)
	assert not_equip == 0
	assert s0.get_component(StorageComponent).inventory[ WEAPONS.CANNON ] == 2
	assert s0.get_weapon_storage()[WEAPONS.CANNON] == WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM

	not_equip = UnequipWeaponToInventory(s0, WEAPONS.CANNON, WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM).execute(s)
	assert not_equip == 0

	assert s0.get_component(StorageComponent).inventory[ WEAPONS.CANNON ] == 2 + WEAPONS.DEFAULT_FIGHTING_SHIP_WEAPONS_NUM
	assert s0.get_weapon_storage()[WEAPONS.CANNON] == 0

@game_test
def test_diplo0(s, p):

	(p0, s0), (p1, s1) = setup_combat(s, UNITS.FRIGATE)

	Attack(s0, s1).execute(s)
	# attack without war

	s.run(seconds=60)

	assert health(s0) == max_health(s0)
	assert health(s1) == max_health(s1)

	# declare war
	AddEnemyPair(p0, p1).execute(s)

	s.run(seconds=60)

	assert health(s0) < max_health(s0)
	assert health(s1) < max_health(s1)

	# it's not specified which one should lose
	assert health(s0) == 0 or health(s1) == 0

@game_test
def test_dying(s, p):
	"""
	Check if units actually are gone when they have died
	"""
	(p0, s0), (p1, s1) = setup_combat(s, UNITS.FRIGATE)

	AddEnemyPair(p0, p1).execute(s)
	Attack(s0, s1).execute(s)

	s.run(seconds=60)

	assert health(s0) < max_health(s0)
	assert health(s1) < max_health(s1)

	# it's not specified which one should lose
	assert one_dead(s0.worldid, s1.worldid)

@game_test
def test_diplo1(s, p):

	(p0, s0), (p1, s1) = setup_combat(s, UNITS.FRIGATE)

	assert health(s0) == max_health(s0)
	assert health(s1) == max_health(s1)

	# declare war
	AddEnemyPair(p0, p1).execute(s)
	# declare peace
	AddAllyPair(p0, p1).execute(s)

	s.run(seconds=60)

	assert health(s0) == max_health(s0)
	assert health(s1) == max_health(s1)

	# declare war
	AddEnemyPair(p0, p1).execute(s)
	# declare peace
	AddNeutralPair(p0, p1).execute(s)

	s.run(seconds=60)

	assert health(s0) == max_health(s0)
	assert health(s1) == max_health(s1)

	# declare war
	AddEnemyPair(p0, p1).execute(s)
	s.run(seconds=60)

	assert health(s0) != max_health(s0)
	assert health(s1) != max_health(s1)

@game_test
def test_unfair(s, p):
	(p0, s0), (p1, s1) = setup_combat(s, UNITS.FRIGATE)

	# two against one

	s0_1 = CreateUnit(p0.worldid, UNITS.FRIGATE, 5, 5)(issuer=p0)

	AddEnemyPair(p0, p1).execute(s)

	Attack(s0, s1).execute(s)
	Attack(s0_1, s1).execute(s)

	s.run(seconds=60)

	assert health(s1) == 0
	assert health(s0) > 0
	assert health(s0_1) > 0

# TODO: stances

@game_test(manual_session=True)
def test_combat_save_load():
	"""
	create a savegame with combat units and actual combat, then save/load it
	"""

	session, player = new_session()
	(p0, s0), (p1, s1) = setup_combat(session, UNITS.FRIGATE)

	s0_worldid, s1_worldid = s0.worldid, s1.worldid

	session.run(seconds=1)

	# saveload
	fd, filename = tempfile.mkstemp()
	os.close(fd)
	assert session.save(savegamename=filename)
	session.end(keep_map=True)
	session = load_session(filename)

	s0 = WorldObject.get_object_by_id(s0_worldid)
	s1 = WorldObject.get_object_by_id(s1_worldid)

	# fight

	AddEnemyPair(p0, p1).execute(session)

	Attack(s0, s1).execute(session)
	Attack(s1, s0).execute(session)

	session.run(seconds=20)

	# saveload
	fd, filename = tempfile.mkstemp()
	os.close(fd)
	assert session.save(savegamename=filename)
	session.end(keep_map=True)
	session = load_session(filename)

	assert one_dead(s0_worldid, s1_worldid)

	session.end()
