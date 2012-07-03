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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
# ###################################################

import subprocess
import sys

from nose.plugins.skip import SkipTest

from horizons.constants import VERSION
from horizons.network.client import Client
from horizons.network.networkinterface import NetworkInterface
from horizons.network import find_enet_module
from horizons.extscheduler import ExtScheduler
from horizons.ext.dummy import Dummy


try:
	import gevent
except ImportError:
	gevent = None

def setup_package():
	"""Sets the network module up.

	Host class' service method waits for service to start.
	"""
	ExtScheduler.create_instance(Dummy())
	enet = find_enet_module()

	class Host(enet.Host):
		def service(self, *args, **kwargs):
			gevent.sleep(0)
			return super(Host, self).service(*args, **kwargs)

	enet.Host = Host


def _create_interface(name, address):
	"""Creates network interface and sets the client up.
	"""
	def setup_client(self):
		self._client = Client(name, VERSION.RELEASE_VERSION, ['127.0.0.1', 2002], address)
	NetworkInterface._NetworkInterface__setup_client = setup_client

	NetworkInterface.destroy_instance()
	NetworkInterface.create_instance()
	return NetworkInterface()


def run_server():
	"""Starts a server using subprocess.

	If server closes, subprocess is also terminating.
	"""
	try:
		p = subprocess.Popen([sys.executable, 'server.py', '-h', '127.0.0.1'])
		while True:
			gevent.sleep(0)
			p.poll()
			if p.returncode:
				break
	finally:
		p.terminate()


def new_client(name, address):
	"""Creates a new client using name and address.
	"""
	p = _create_interface(name, address)
	p.connect()
	return p


def test_general():
	"""General test for multiplayer game.

	Starts a new server and connects 2 clients to it.
	Requires python-gevent package. If not exists
	pass this test
	"""
	if not gevent:
		raise SkipTest

	def clients(server):
		p1 = new_client(u'Client1', ['127.0.0.1', 4123])

		assert p1.get_active_games() == []

		p1.change_name(u'NewClient1')

		game = p1.creategame(u'development', 2, u'Game1')

		assert game.get_player_count() == 1

		p2 = new_client(u'Client2', ['127.0.0.1', 4234])
		p3 = new_client(u'Client3', ['127.0.0.1', 4345])

		assert len(p2.get_active_games()) == 1

		p2.joingame(p2.get_active_games()[0].uuid)

		assert p2.isjoined() == True

		assert p3.get_active_games() == []

		assert p1.get_game().uuid == p2.get_game().uuid

		assert p1.get_game().get_player_count() == 2

		p1.disconnect()
		p2.disconnect()
		p3.disconnect()

		server.kill()

	setup_package()

	s = gevent.spawn(run_server)
	c = gevent.spawn_later(3, clients, s)
	gevent.joinall([c, s])
