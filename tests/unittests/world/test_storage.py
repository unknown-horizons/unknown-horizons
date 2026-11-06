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

import sys

from horizons.world.storage import (
    GenericStorage,
    GlobalLimitStorage,
    PositiveSizedNumSlotStorage,
    PositiveSizedSlotStorage,
    PositiveStorage,
    PositiveTotalStorage,
    SizedSpecializedStorage,
    SpecializedStorage,
    TotalStorage,
)


class TestGenericStorage:
    def test_alter(self):
        s = GenericStorage()

        assert s.alter(1, 5) == 0
        assert s.alter(2, 3) == 0
        assert s[1] == 5
        assert s[2] == 3

        assert s.alter(1, 10) == 0
        assert s[1] == 15

    def test_reset(self):
        s = GenericStorage()

        s.alter(1, 5)
        s.alter(2, 3)

        s.reset(1)

        assert s[1] == 0
        assert s[2] == 3

    def test_reset_all(self):
        s = GenericStorage()

        s.alter(1, 5)
        s.alter(2, 3)

        s.reset_all()

        assert s[1] == 0
        assert s[2] == 0

    def test_limit(self):
        s = GenericStorage()

        assert s.get_limit() == sys.maxsize
        assert s.get_limit(1) == sys.maxsize

    def test_sum_of_stored_resources(self):
        s = GenericStorage()

        s.alter(1, 5)
        s.alter(2, 3)

        assert s.get_sum_of_stored_resources() == 8

    def test_get_item(self):
        s = GenericStorage()

        s.alter(1, 5)

        assert s[1] == 5
        assert s[2] == 0

    def test_get_dump_returns_copy(self):
        s = GenericStorage()

        s.alter(1, 5)

        dump = s.get_dump()
        dump[1] = 999

        assert s[1] == 5

    def test_iterslots(self):
        s = GenericStorage()

        s.alter(1, 5)
        s.alter(2, 3)

        assert set(s.iterslots()) == {1, 2}

    def test_itercontents(self):
        s = GenericStorage()

        s.alter(1, 5)
        s.alter(2, 3)

        assert dict(s.itercontents()) == {1: 5, 2: 3}

    def test_reset_missing_resource(self):
        s = GenericStorage()

        s.reset(999)

        assert s[999] == 0

    def test_alter_triggers_change_listener(self):
        s = GenericStorage()

        called = []

        def listener():
            called.append(True)

        s.add_change_listener(listener)

        s.alter(1, 5)

        assert called == [True]


class TestSpecializedStorages:
    def test_specialized(self):
        s = SpecializedStorage()

        assert s.alter(1, 3) == 3
        assert s.alter(1, -3) == -3

        assert not s.has_resource_slot(1)

        s.add_resource_slot(1)

        assert s.has_resource_slot(1)

        assert s.alter(1, 3) == 0
        assert s.alter(1, -3) == 0

    def test_sized_specialized(self):
        s = SizedSpecializedStorage()

        assert s.alter(1, 3) == 3
        assert s.alter(1, -3) == -3
        assert s.get_limit(1) == 0

        assert not s.has_resource_slot(1)

        s.add_resource_slot(1, 10)

        assert s.has_resource_slot(1)
        assert s.get_limit(1) == 10

        assert s.get_free_space_for(1) == 10

        assert s.alter(1, 3) == 0
        assert s.get_free_space_for(1) == 7

        assert s.alter(1, -3) == 0
        assert s.get_free_space_for(1) == 10

        assert s.alter(1, 12) == 2

    def test_add_resource_slot_twice(self):
        s = SpecializedStorage()

        s.add_resource_slot(1)
        s.add_resource_slot(1)

        assert s.has_resource_slot(1)


class TestGlobalLimitStorage:
    def test_adjust_limit(self):
        s = GlobalLimitStorage(10)

        assert s.get_limit() == 10

        s.alter(1, 10)

        assert s[1] == 10

        s.adjust_limit(-5)

        assert s.get_limit() == 5
        assert s[1] == 5

        s.adjust_limit(-10)

        assert s.get_limit() == 0


class TestOtherStorages:
    def test_total(self):
        s = TotalStorage(10)

        assert s.get_limit() == 10
        assert s.get_limit(1) == 10
        assert s.get_free_space_for(1) == 10
        assert s.get_free_space_for(2) == 10

        assert s.alter(2, 2) == 0

        assert s.get_limit() == 10
        assert s.get_limit(1) == 10
        assert s.get_free_space_for(1) == 8
        assert s.get_free_space_for(2) == 8

        assert s.alter(2, 10) == 2

        assert s.get_free_space_for(1) == 0
        assert s.get_free_space_for(2) == 0

    def test_positive(self):
        s = PositiveStorage()

        assert s.alter(1, -2) == -2
        assert s.alter(1, 2) == 0
        assert s.alter(1, -2) == 0
        assert s.alter(1, -1) == -1

    def test_positive_total(self):
        s = PositiveTotalStorage(10)

        assert s.alter(1, -2) == -2
        assert s.alter(1, 2) == 0
        assert s.alter(1, -2) == 0
        assert s.alter(1, -1) == -1

        assert s.get_limit() == 10
        assert s.get_limit(1) == 10
        assert s.get_free_space_for(1) == 10
        assert s.get_free_space_for(2) == 10

        assert s.alter(2, 2) == 0

        assert s.get_limit() == 10
        assert s.get_limit(1) == 10
        assert s.get_free_space_for(1) == 8
        assert s.get_free_space_for(2) == 8

        assert s.alter(2, 10) == 2

        assert s.get_free_space_for(1) == 0
        assert s.get_free_space_for(2) == 0

    def test_sized_slotted(self):
        s = PositiveSizedSlotStorage(10)

        assert s.alter(1, 6) == 0
        assert s.alter(1, 6) == 2
        assert s.alter(1, -20) == -10

    def test_positive_sized_num_slot(self):
        s = PositiveSizedNumSlotStorage(10, 3)

        assert s.get_limit() == 10
        assert s.get_limit(1) == 10

        assert s.alter(1, 10) == 0
        assert s.alter(1, 2) == 2

        assert s.alter(2, 0) == 0

        assert s.alter(2, 5) == 0
        assert s.alter(3, 5) == 0

        assert s.alter(4, 1) == 1
