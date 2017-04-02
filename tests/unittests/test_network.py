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

import subprocess
import sys
import time


def test_run_server():
	"""Test if the multiplayer server can be started.

	Runs the server for 2 seconds and checks if anything was printed on stderr.
	"""
	proc = subprocess.Popen([sys.executable, "server.py", "-h", "127.0.0.1"],
	                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	time.sleep(2)
	proc.terminate()

	# By default logging prints to stderr, which makes it difficult to detect
	# errors. This solution isn't great, but works for now.
	stderr = proc.stderr.read()
	if stderr and b'Traceback' in stderr:
		raise Exception("\n\n" + stderr)
