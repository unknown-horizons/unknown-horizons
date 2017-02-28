#!/usr/bin/env python2

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

import getopt
import os
import sys

from horizons import network
from horizons.network.server import Server


def fork():
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		sys.stderr.write("Unable to fork: ({:d}) {}\n".format(e.errno, e.strerror))
		sys.exit(1)

	os.umask(0)
	os.setsid()

	# fork again to remove a possible session leadership gained after setsid()
	try:
		pid = os.fork( )
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		sys.stderr.write("Unable to fork: ({:d}) {}\n".format(e.errno, e.strerror))
		sys.exit(1)
	return os.getpid()

def redirect(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
	for f in sys.stdout, sys.stderr:
		f.flush()
	ifd = file(stdin,  'r')
	ofd = file(stdout, 'a+')
	efd = ofd if (stdout == stderr) else file(stderr, 'a+')
	os.dup2(ifd.fileno(), sys.stdin.fileno())
	os.dup2(ofd.fileno(), sys.stdout.fileno())
	os.dup2(efd.fileno(), sys.stderr.fileno())

def usage(fd=sys.stdout):
	fd.write("Usage: {}".format(sys.argv[0]))
	if os.name == "posix":
		fd.write(" [-d]")
	fd.write(" -h host [-p port] [-s statistic_file]")
	if os.name == "posix":
		fd.write(" [-l logfile] [-P pidfile] ")
	fd.write("\n")

host = None
port = 2002
statfile = None
daemonize = False
logfile = None
pidfile = None

try:
	options = 'h:p:s:'
	if os.name == "posix":
		options += 'dl:P:'
	opts, args = getopt.getopt(sys.argv[1:], options)
except getopt.GetoptError as err:
	sys.stderr.write(str(err))
	usage()
	sys.exit(1)

try:
	for (key, value) in opts:
		if key == '-h':
			host = value
		if key == '-p':
			port = int(value)
		if key == '-s':
			statfile = value
		if os.name == "posix":
			if key == '-d':
				daemonize = True
			if key == '-l':
				logfile = value
			if key == '-P':
				pidfile = value
except (ValueError, IndexError):
	port = 0

if host is None or port is None or port <= 0:
	usage()
	sys.exit(1)

if pidfile and os.path.isfile(pidfile):
	sys.stderr.write("Error: Pidfile '{}' already exists.\n".format(pidfile))
	sys.stderr.write("Please make sure no other server is running and remove this file\n")
	sys.exit(1)

pid = os.getpid()
if daemonize:
	pid = fork()
	# daemon must redirect!
	if logfile is None:
		logfile = '/dev/null'

if logfile is not None:
	redirect('/dev/null', logfile, logfile)

if pidfile:
	file(pidfile, 'w').write(str(pid))

try:
	server = Server(host, port, statfile)
	server.run()
except network.NetworkException as e:
	sys.stderr.write("Error: {}\n".format(e))
	sys.exit(2)

if pidfile:
	os.unlink(pidfile)
