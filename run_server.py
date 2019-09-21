#!/usr/bin/env python3

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

import argparse
import os
import sys

from horizons import network
from horizons.network.server import Server


def daemonize() -> int:
	"""
	POSIX compliant daemonize.
	"""
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError as e:
		sys.stderr.write("Unable to fork: ({:d}) {}\n".format(e.errno, e.strerror))
		sys.exit(1)

	os.umask(0)
	os.setsid()

	# fork again to remove a possible session leadership gained after setsid()
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError as e:
		sys.stderr.write("Unable to fork: ({:d}) {}\n".format(e.errno, e.strerror))
		sys.exit(1)
	return os.getpid()


def redirect(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
	"""
	TODO: No clue what this is about.
	"""
	for f in sys.stdout, sys.stderr:
		f.flush()

	ifd = open(stdin,  'r')
	ofd = open(stdout, 'a+')
	efd = ofd if (stdout == stderr) else open(stderr, 'a+')

	os.dup2(ifd.fileno(), sys.stdin.fileno())
	os.dup2(ofd.fileno(), sys.stdout.fileno())
	os.dup2(efd.fileno(), sys.stderr.fileno())


def port(value: str) -> int:
	"""
	Check whether the given string is a valid port.
	"""
	port = int(value)
	max_port = 2**16

	if not (1 <= port < max_port):
		raise argparse.ArgumentTypeError(
			'{} is not between 1 and {}'.format(port, max_port))
	return port


def main(args=None):
	"""
	Main entry point of the script. Parses command line options and starts the server.
	"""
	if not network.enet:
		sys.stderr.write('Could not find enet module.\n')
		sys.exit(1)

	parser = argparse.ArgumentParser()
	parser.add_argument('host', help='Host to listen on')
	parser.add_argument('-p', dest='port', type=port,
	                    help='Port to listen on, default 2002', default=2002)
	parser.add_argument('-s', dest='statistic_file', default=None)

	if os.name == 'posix':
		parser.add_argument('-d', dest='daemonize', action='store_true',
		                    help='Daemonize the server.', default=False)
		parser.add_argument('-l', dest='log_file', default=None)
		parser.add_argument('-P', dest='pid_file', default=None)

	config = parser.parse_args(args)

	if config.pid_file and os.path.isfile(config.pid_file):
		sys.stderr.write("Error: Pidfile '{}' already exists.\n".format(config.pid_file))
		sys.stderr.write("Please make sure no other server is running and remove this file\n")
		sys.exit(1)

	pid = os.getpid()
	if config.daemonize:
		pid = daemonize()
		# daemon must redirect!
		if config.log_file is None:
			config.log_file = '/dev/null'

	if config.log_file:
		redirect('/dev/null', config.log_file, config.log_file)

	if config.pid_file:
		with open(config.pid_file, 'w') as f:
			f.write(str(pid))

	try:
		server = Server(config.host, config.port, config.statistic_file)
		server.run()
	except network.NetworkException as e:
		sys.stderr.write("Error: {}\n".format(e))
		sys.exit(2)

	if config.pid_file:
		os.unlink(config.pid_file)


if __name__ == '__main__':
	main()
