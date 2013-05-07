# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

import sys
import traceback
from collections import deque

try:
	import greenlet
except ImportError:
	print 'The greenlet package is needed to run the UH gui tests.'
	sys.exit(1)


_scheduled = deque()
_current = greenlet.getcurrent()


class Tasklet(greenlet.greenlet):
	"""Wrapper around greenlet.

	Let's you add callbacks when the greenlet finished and wait for it to finish.
	"""
	def __init__(self, *args, **kwargs):
		super(Tasklet, self).__init__(*args, **kwargs)
		self.links = []

	def link(self, func):
		"""Call func once this greenlet finished execution."""
		self.links.append(func)

	def join(self):
		"""Blocks until this greenlet finished execution."""

		# little hack because we don't have Python3's nonlocal
		class Flag(object):
			running = True

		def stop(_):
			Flag.running = False

		self.link(stop)

		while Flag.running:
			schedule()


def spawn(func, *args, **kwargs):
	"""Schedule a new function to run."""
	g = Tasklet(func)
	_scheduled.append((g, args, kwargs))
	return g


def schedule():
	global _scheduled
	global _current

	if not _current.dead:
		_scheduled.append((_current, [], {}))
	else:
		[l(_current) for l in _current.links]

	while _scheduled:
		g, args, kwargs = _scheduled.popleft()

		_current = g
		g.switch(*args, **kwargs)
		break
