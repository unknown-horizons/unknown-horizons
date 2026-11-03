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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
# ###################################################

import os
import shutil
import tempfile
from contextlib import ExitStack
from unittest.mock import patch

import pytest

from horizons.constants import PATHS
from horizons.savegamemanager import SavegameManager
from horizons.util import create_user_dirs

ODD_CHARACTERS = "u\xfc\xdf\xfau"


@pytest.fixture
def special_dirs():
    outer = tempfile.mkdtemp(ODD_CHARACTERS)
    inner = os.path.join(outer, ODD_CHARACTERS)
    inner2 = os.path.join(outer, ODD_CHARACTERS + "2")

    yield outer, inner, inner2

    if os.path.isdir(inner):
        for dirpath, _dirnames, _filenames in os.walk(inner, topdown=False):
            os.rmdir(dirpath)

    if os.path.isdir(inner2):
        os.rmdir(inner2)

    if os.path.isdir(outer):
        os.rmdir(outer)


def test_normal():
    create_user_dirs(migrate=False)


def test_special_character(special_dirs):
    """Make paths have special characters and check some basic operations."""

    _outer, inner, inner2 = special_dirs

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(PATHS, "USER_DATA_DIR", inner)
        )
        stack.enter_context(
            patch.object(PATHS, "LOG_DIR", os.path.join(inner, "log"))
        )
        stack.enter_context(
            patch.object(PATHS, "USER_MAPS_DIR", os.path.join(inner, "maps"))
        )
        stack.enter_context(
            patch.object(PATHS, "SCREENSHOT_DIR", os.path.join(inner, "screenshots"))
        )
        stack.enter_context(
            patch.object(PATHS, "SAVEGAME_DIR", os.path.join(inner, "save"))
        )
        stack.enter_context(
            patch.object(SavegameManager, "autosave_dir", inner2)
        )

        create_user_dirs(migrate=False)

        scenario_file = os.listdir(
            SavegameManager.scenarios_dir
        )[0]

        shutil.copy(
            os.path.join(
                SavegameManager.scenarios_dir,
                scenario_file,
            ),
            inner,
        )

        stack.enter_context(
            patch.object(
                SavegameManager,
                "scenarios_dir",
                inner,
            )
        )

        SavegameManager.init()

        # try to read scenario files
        SavegameManager.get_available_scenarios()

        os.remove(os.path.join(inner, scenario_file))

        SavegameManager.create_autosave_filename()
