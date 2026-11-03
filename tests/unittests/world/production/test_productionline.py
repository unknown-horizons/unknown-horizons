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

from horizons.world.production.productionline import ProductionLine


class TestProductionLineData:
    def test_init(self):
        # NOTE: this has been broken by optimizations and will soon be
        # moved to yaml, therefore not fixing it now.

        data = {
            "enabled_by_default": False,
            "time": 90,
            "level": [0, 1, 2],
            "changes_animation": False,
            "produces": [[14, 1]],
            "consumes": [[19, -1]],
        }

        line = ProductionLine(1, data)

        assert line.time == 90
        assert line.changes_animation is False
        assert line.production == {14: 1, 19: -1}
        assert line.produced_res == {14: 1}
        assert line.consumed_res == {19: -1}

        # assert line.unit_production == {10: 4, 12: 8}


class TestProductionLine:
    def test_alter_production_time(self):
        data = {"time": 10}
        line = ProductionLine(1, data)

        assert line.time == 10

        line.alter_production_time(2)
        assert line.time == 20

        # Test that it modifies the original value (10)
        line.alter_production_time(2)
        assert line.time == 20

        line.alter_production_time(1.5)
        assert line.time == 15.0

        # should this throw an error?
        # line.alter_production_time(0)

    def test_change_amount(self):
        data = {
            "time": 10,
            "produces": [[2, 3]],
            "consumes": [[4, -5]],
        }

        line = ProductionLine(1, data)

        line.change_amount(2, 10)
        assert line.production == {2: 10, 4: -5}
        assert line.produced_res == {2: 10}
        assert line.consumed_res == {4: -5}

        line.change_amount(4, -1)
        assert line.production == {2: 10, 4: -1}
        assert line.produced_res == {2: 10}
        assert line.consumed_res == {4: -1}

        # should these throw an error?
        # line.change_amount(X, 0)
        # line.change_amount(2, -3) - produced becomes consumed
        # line.change_amount(4, 3)  - consumed becomes produced
