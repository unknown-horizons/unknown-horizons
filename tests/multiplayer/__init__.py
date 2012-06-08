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

import gevent
import subprocess
import sys

from horizons.constants import VERSION
from horizons.network.client import Client
from horizons.network.networkinterface import NetworkInterface
from horizons.network import find_enet_module
from horizons.extscheduler import ExtScheduler
from horizons.ext.dummy import Dummy

def setup_package():
	ExtScheduler.create_instance(Dummy())
	enet = find_enet_module()

	class Host(enet.Host):
		def service(self, *args, **kwargs):
			gevent.sleep(0)
			return super(Host, self).service(*args, **kwargs)

	enet.Host = Host

def _create_interface(name, address):
	def setup_client(self):
		self._client = Client(name, VERSION.RELEASE_VERSION, ['127.0.0.1', 2002], address)
	NetworkInterface._NetworkInterface__setup_client = setup_client

	NetworkInterface.destroy_instance()
	NetworkInterface.create_instance()
	return NetworkInterface()

def run_server():
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
	p = _create_interface(name, address)
	p.connect()
	return p

def clients(server):
	p1 = new_client("Client1", ['127.0.0.1', 4123])
	assert p1.get_active_games() == []
	p1.disconnect()
	server.kill()

def test_general():
	setup_package()

	s = gevent.spawn(run_server)
	c = gevent.spawn_later(3, clients, s)
	gevent.joinall([c, s])
