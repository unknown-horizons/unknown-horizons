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

"""Run game time as fast as the CPU allows, without waiting on wall clock.

GUI tests normally advance the simulation via ``GuiHelper.run()``, which is
bounded by the engine frame rate and gated by ``Timer.check_tick`` on wall-clock
time. ``fast_forward`` drives the timer directly with a fake clock so ``n`` game
ticks are processed back to back, leaving only the game logic to run.
"""

import time

import horizons.timer as timer_mod
from horizons.scheduler import Scheduler

_real_time = time.time

# One clock for the whole process; it must only ever move forward because
# Timer.check_tick compares it against tick_next_time.
_clock = {'now': None}


def _fake_time():
	return _clock['now']


class _FakeTime:
	"""Swap ``horizons.timer.time.time`` for the fake clock while active."""

	def __enter__(self):
		self._saved = timer_mod.time.time
		timer_mod.time.time = _fake_time
		return self

	def __exit__(self, *exc):
		timer_mod.time.time = self._saved
		return False


def fast_forward(ticks, stop=None, check_interval=200):
	"""Advance the game by up to *ticks* game ticks, ignoring wall clock.

	*stop* is checked every *check_interval* ticks and ends the loop early once
	it is true. Returns the number of ticks run.
	"""
	timer = Scheduler().timer
	if timer.ticks_per_second == 0:
		# Paused: nothing would advance.
		return 0

	# Resume from where the engine left off.
	if _clock['now'] is None or _clock['now'] < timer.tick_next_time:
		_clock['now'] = max(_real_time(), timer.tick_next_time)

	step = 1.0 / timer.ticks_per_second
	done = 0
	with _FakeTime():
		for i in range(ticks):
			timer.check_tick()
			_clock['now'] += step
			done += 1
			if stop is not None and i % check_interval == 0 and stop():
				break

	# Hand back control at the real time so the engine does not try to catch up.
	timer.tick_next_time = _real_time()
	return done
