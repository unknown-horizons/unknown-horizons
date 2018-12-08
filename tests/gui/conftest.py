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

import os
import subprocess
import sys

import pytest

from tests import RANDOM_SEED
from tests.gui import TEST_FIXTURES_DIR
from tests.utils import Timer


@pytest.fixture
def gui():
	# This is necessary for the function to work with pytest. It isn't actually executed by
	# pytest because it's running in a subprocess, but oherwise pytest complains about unknown
	# fixture `gui`.
	pass


class TestFailed(Exception):
	pass


def pytest_pyfunc_call(pyfuncitem):
	"""
	Tests marked with gui_test will, instead of executing the test function, start a new
	process with the game and run the test function code inside that process.
	"""
	info = pyfuncitem.get_marker('gui_test')
	if not info:
		return

	tmpdir = pyfuncitem._request.getfixturevalue('tmpdir')

	use_fixture = info.kwargs.get('use_fixture', None)
	use_dev_map = info.kwargs.get('use_dev_map', False)
	use_scenario = info.kwargs.get('use_scenario', None)
	ai_players = info.kwargs.get('ai_players', 0)
	additional_cmdline = info.kwargs.get('additional_cmdline', None)
	timeout = info.kwargs.get('timeout', 15 * 60)
	modify_user_dir = info.kwargs.get('_modify_user_dir', lambda v: v)

	test_name = '{}.{}'.format(pyfuncitem.module.__name__, pyfuncitem.name)

	# when running under coverage, enable it for subprocesses too
	if os.environ.get('RUNCOV'):
		executable = ['coverage', 'run']
	else:
		executable = [sys.executable]

	args = executable + ['run_uh.py', '--sp-seed', str(RANDOM_SEED), '--gui-test', test_name]

	if use_fixture:
		path = os.path.join(TEST_FIXTURES_DIR, use_fixture + '.sqlite')
		if not os.path.exists(path):
			raise Exception('Savegame {} not found'.format(path))
		args.extend(['--load-game', path])
	elif use_dev_map:
		args.append('--start-dev-map')
	elif use_scenario:
		args.extend(['--start-scenario', use_scenario + '.yaml'])

	if ai_players:
		args.extend(['--ai-players', str(ai_players)])

	if additional_cmdline:
		args.extend(additional_cmdline)

	user_dir = modify_user_dir(tmpdir.join('user_dir'))

	env = os.environ.copy()
	# Setup temporary user directory for each test
	env['UH_USER_DIR'] = str(user_dir)
	# Activate fail-fast, this way the game will stop running when for example the savegame
	# could not be loaded (instead of showing an error popup)
	env['FAIL_FAST'] = '1'
	# Show additional information (e.g. about threads) when the interpreter crashes
	env['PYTHONFAULTHANDLER'] = '1'

	if pyfuncitem.config.option.capture == 'no':
		# if pytest does not capture stdout, then most likely someone wants to
		# use a debugger (he passed -s at the cmdline). In that case, we will
		# redirect stdout/stderr from the gui-test process to the testrunner
		# process.
		stdout = sys.stdout
		stderr = sys.stderr
		output_captured = False
	else:
		# if pytest captures stdout, we can't redirect to sys.stdout, as that
		# was replaced by a custom object. Instead we capture it and return the
		# data at the end.
		stdout = subprocess.PIPE
		stderr = subprocess.PIPE
		output_captured = True

	# Start game
	proc = subprocess.Popen(args, stdout=stdout, stderr=stderr, env=env)

	def handler(signum, frame):
		proc.kill()
		raise TestFailed('\n\nTest run exceeded {:d}s time limit'.format(timeout))

	timelimit = Timer(handler)
	timelimit.start(timeout)

	stdout, stderr = proc.communicate()

	if proc.returncode != 0:
		if output_captured:
			if stdout:
				print(stdout)
			if b'Traceback' not in stderr:
				stderr += b'\nNo usable error output received, possibly a segfault.'
		raise TestFailed(stderr.decode('ascii'))

	return True


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
	"""
	When a gui test fails, we replace the internal traceback with the one from the subprocess
	stderr.
	"""
	report = (yield).get_result()
	if report.when != 'call' or report.outcome != 'failed':
		return report

	if isinstance(call.excinfo.value, TestFailed):
		report.longrepr = call.excinfo.value.args[0]
		return report
