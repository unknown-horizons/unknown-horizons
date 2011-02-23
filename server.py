#!/usr/bin/env python

# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

#!/usr/bin/python

import getopt
import sys
from horizons import network
from horizons.network.server import Server

def usage():
	print "Usage: %s -h host [-p port]" % (sys.argv[0])

host = None
port = 2001

try:
	opts, args = getopt.getopt(sys.argv[1:], 'h:p:')
except getopt.GetoptError, err:
	print str(err)
	usage()
	sys.exit(1)

try:
	for (key, value) in opts:
		if key == '-h':
			host = value
		if key == '-p':
			port = int(value)
except ValueError, IndexError:
	port = 0

if host == None or port == None or port <= 0:
	usage()
	sys.exit(1)

try:
	server = Server(host, port)
	server.run()
except network.NetworkException, e:
	print "Error: %s" % (e)
	sys.exit(2)

