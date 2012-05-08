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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import signal

from nose.plugins import Plugin
from nose.util import ln

# check if SIGALRM is supported, this is not the case on Windows
# we might provide an alternative later, but for now, this will do
try:
	from signal import SIGALRM
	SUPPORTED = True
except ImportError:
	SUPPORTED = False


class Timer(object):
	"""
	Example

		def handler(signum, frame):
			print 'Timer triggered'

		t = Timer(handler)
		# handler will be called after 2 seconds
		t.start(2)

		# if 2 seconds have not passed, this will stop the timer
		t.stop()

	Note: if SIGALRM is not supported, this class does nothing
	"""

	def __init__(self, handler):
		"""Install the passed function as handler that is called when the signal
		triggers.
		"""
		if not SUPPORTED:
			return

		signal.signal(signal.SIGALRM, handler)

	def start(self, timeout):
		"""Start the timer. A timeout of 0 means that the signal will never trigger."""
		if not SUPPORTED or timeout == 0:
			return

		signal.alarm(timeout)

	@classmethod
	def stop(self):
		"""Stop the timer. This can be called on both the instance and class (when you
		have no access to the instance for example).
		"""
		if not SUPPORTED:
			return

		signal.alarm(0)


class ReRunInfoPlugin(Plugin):
	"""Print information on how to rerun a test after each failed test.

	Code to add additional output taken from the Collect plugin.
	"""
	name = 'reruninfo'
	enabled = True

	def configure(self, options, conf):
		pass

	def formatError(self, test, err):
		_, module, call = test.address()

		output = ['python', 'run_tests.py', u'%s:%s' % (module, call)]

		# add necessary flags
		if 'tests.gui' in module:
			output.append('-a gui')
		elif 'tests.game.long' in module:
			output.append('-a long')

		output = u' '.join(output)

		ec, ev, tb = err
		return (ec, self.addOutputToErr(ev, output), tb)

	def formatFailure(self, test, err):
		return self.formatError(test, err)

	def addOutputToErr(self, ev, output):
		if isinstance(ev, Exception):
			ev = unicode(ev)
		return u'\n'.join([ev, u'', ln(u'>> rerun the test <<'), output])