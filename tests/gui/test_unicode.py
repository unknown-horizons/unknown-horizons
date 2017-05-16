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

import shutil
import tempfile

import pytest

from tests.gui import gui_test

USER_DIR = None

def setup():
	global USER_DIR
	USER_DIR = tempfile.mkdtemp(suffix='H߀ｒìｚｏԉｓ')


def teardown():
	global USER_DIR
	try:
		shutil.rmtree(USER_DIR)
	except:
		pass
	USER_DIR = None


def dummy(gui):
	"""This test will end the game immediately."""
	pass
dummy.__original__ = dummy # type: ignore


@pytest.mark.gui
def test_user_dir_contains_non_ascii():
	# NOTE we have to create the test this way because if it were defined globally,
	# USER_DIR would not be defined yet at the time the decorator is evaluated
	gui_test(timeout=60, use_dev_map=True, _user_dir=USER_DIR)(dummy)()
