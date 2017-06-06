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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

from io import StringIO
from unittest import mock

from horizons.network.common import Game
from horizons.network.server import print_statistic


def test_stats_empty_server():
	f = StringIO()
	print_statistic([], [], f)

	assert f.getvalue() == '''
Games.Total: 0
Games.Playing: 0
Players.Total: 0
Players.Lobby: 0
Players.Playing: 0
'''.strip()


def test_stats_busy_server(mocker):
	p1 = mock.Mock()
	p2 = mock.Mock()
	p2.game = mock.Mock()
	p3 = mock.Mock()
	p3.game = mock.Mock(state=Game.State.Running)

	g1 = mock.Mock()
	g2 = mock.Mock(state=Game.State.Running)

	f = StringIO()
	print_statistic([p1, p2, p3], [g1, g2], f)
	assert f.getvalue() == '''
Games.Total: 2
Games.Playing: 1
Players.Total: 3
Players.Lobby: 2
Players.Playing: 1
'''.strip()
