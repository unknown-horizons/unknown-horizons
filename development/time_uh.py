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
import ctypes
import multiprocessing
import os
import os.path
import subprocess
import sys
import time

from optparse import AmbiguousOptionError, BadOptionError, OptionParser

# make this script work both when started inside development and in the uh root dir
if not os.path.exists('content'):
	os.chdir('..')
assert os.path.exists('content'), 'Content dir not found.'
sys.path.append('.')


class PassThroughOptionParser(OptionParser):
	"""Consider unrecognised options to be arguments."""
	def _process_args(self, largs, rargs, values):
		while rargs:
			try:
				OptionParser._process_args(self, largs, rargs, values)
			except (AmbiguousOptionError, BadOptionError), e:
				largs.append(e.opt_str)


def get_range(expr):
	if not expr:
		return [None]
	parts = []
	for part in expr.split(','):
		parts.append(int(part.strip()))
	return range(*tuple(parts))


def get_length(r):
	return max(len(str(min(r))), len(str(max(r))))


dev_null = open(os.devnull, 'w')


class GameTimer:
	def __init__(self, name, args):
		self.name = name
		self.args = args
		self.returncode = None
		self.time = None

	def run(self):
		start = time.time()
		args = ' '.join([sys.executable, 'run_uh.py'] + self.args)
		proc = subprocess.Popen(args, executable=sys.executable, stdin=dev_null, stdout=dev_null, stderr=dev_null)
		proc.wait()
		self.returncode = proc.returncode
		self.time = time.time() - start

	def __cmp__(self, other):
		if self.returncode != other.returncode:
			return -1 if self.returncode < other.returncode else 1
		if self.time == other.time:
			return 0
		return -1 if self.time < other.time else 1


def run_game_timer(game, queue, counter):
	game.run()
	queue.put_nowait(game)
	counter.value -= 1


def show_data(games):
	print()
	for game in sorted(games):
		s = game.time
		h = s // 3600
		s %= 3600
		m = s // 60
		s %= 60
		print(game.name, '[:d}:{:02d}:{:06.3f}s'.format(h, m, s), game.returncode)


if __name__ == '__main__':
	parser = PassThroughOptionParser()
	parser.add_option("-p", "--processes", dest="num_processes", metavar="<processes>",
	                  type="int", default=1, help="Run <processes> processes in parallel.")
	parser.add_option("--game-seed-range", dest="game_seed_range",
	                  help="Use the given expression (same as for xrange) to run a number of game instances with --sp-seed=SEED")
	parser.add_option("--map-seed-range", dest="map_seed_range",
	                  help="Use the given expression (same as for xrange) to run a number of game instances with --start-specific-random-map=SEED")
	(options, args) = parser.parse_args()

	games = []
	game_seed_len = get_length(get_range(options.game_seed_range))
	map_seed_len = get_length(get_range(options.map_seed_range))
	for sp_seed in get_range(options.game_seed_range):
		for map_seed in get_range(options.map_seed_range):
			name = 'game'
			args_t = args + []
			if sp_seed is not None:
				args_t.append('--sp-seed=' + str(sp_seed))
				name += ('-s%0' + str(game_seed_len) + 'd') % sp_seed
			if map_seed is not None:
				args_t.append('--start-specific-random-map=' + str(map_seed))
				name += ('-m%0' + str(map_seed_len) + 'd') % map_seed
			games.append(GameTimer(name, args_t))

	manager = multiprocessing.Manager()
	queue = manager.Queue()
	counter = manager.Value(ctypes.c_int, len(games))
	pool = multiprocessing.Pool(processes=options.num_processes)
	for game in games:
		pool.apply_async(run_game_timer, [game, queue, counter])
	pool.close()

	data = []
	try:
		while not queue.empty() or counter.value > 0:
			changed = False
			while not queue.empty():
				game = queue.get()
				data.append(game)
				changed = True
			if changed:
				show_data(data)
			time.sleep(0.05)
	except KeyboardInterrupt:
		pool.terminate()
