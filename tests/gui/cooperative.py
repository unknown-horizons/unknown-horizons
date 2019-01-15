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

from __future__ import print_function

import sys
from collections import deque
from typing import Any, Callable, Dict, List, Tuple

try:
	import greenlet
except ImportError:
	print('The greenlet package is needed to run the UH gui tests.')
	sys.exit(1)


_scheduled = deque() # type: deque[Tuple[Tasklet, Tuple[Any, ...], Dict[str, Any]]]
_current = greenlet.getcurrent()


class Tasklet(greenlet.greenlet):
	"""Wrapper around greenlet.

	Let's you add callbacks when the greenlet finished and wait for it to finish.
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.links = [] # type: List[Callable]

	def link(self, func):
		"""Call func once this greenlet finished execution."""
		self.links.append(func)

	def join(self):
		"""Blocks until this greenlet finished execution."""
		running = True

		def stop(_):
			nonlocal running
			running = False

		self.link(stop)

		while running:
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
		_scheduled.append((_current, tuple(), {}))
	else:
		[l(_current) for l in _current.links]

	while _scheduled:
		g, args, kwargs = _scheduled.popleft()

		_current = g
		g.switch(*args, **kwargs)
		break
