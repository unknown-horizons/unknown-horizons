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

from unittest import mock

import pytest

from horizons.network import enet
from run_server import main

pytestmark = pytest.mark.skipif(enet is None, reason='No enet bindings available')


@pytest.fixture
def server_mock(mocker):
	mocker.patch('horizons.network.server.enet')
	return mocker.patch('run_server.Server')


def test_start(server_mock):
	main(['127.0.0.1'])
	server_mock.assert_has_calls([
		mock.call('127.0.0.1', 2002, None)
	])


def test_start_port(server_mock):
	main(['-p', '6789', '127.0.0.1'])
	server_mock.assert_has_calls([
		mock.call('127.0.0.1', 6789, None)
	])
