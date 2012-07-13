# encoding=utf-8

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

import shutil
import sys
import tempfile

from tests.gui import TestFinished, gui_test


USER_DIR = None

def setup():
	global USER_DIR
	USER_DIR = tempfile.mkdtemp(suffix=u'H߀ｒìｚｏԉｓ').encode(sys.getfilesystemencoding())


def teardown():
	global USER_DIR
	shutil.rmtree(USER_DIR)
	USER_DIR = None


def dummy(gui):
	"""This test will end the game immediately."""
	yield
	yield TestFinished
dummy.__original__ = dummy


def test_user_dir_contains_non_ascii():
	# NOTE we have to create the test this way because if it were defined globally,
	# USER_DIR would not be defined yet at the time the decorator is evaluated
	yield gui_test(timeout=60, use_dev_map=True, _user_dir=USER_DIR)(dummy)
test_user_dir_contains_non_ascii.gui = True
