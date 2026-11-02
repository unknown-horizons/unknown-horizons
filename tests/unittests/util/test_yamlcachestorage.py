# ###################################################
# Copyright (C) 2008-2016 The Unknown Horizons Team
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
import tempfile

import pytest

from horizons.util.yamlcachestorage import YamlCacheStorage


@pytest.fixture
def tmp_cache_file():
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.close()

    yield tmp_file.name

    os.unlink(tmp_file.name)


def test_save_and_reopen(tmp_cache_file):
    cache = YamlCacheStorage(tmp_cache_file)
    cache["foo"] = "bar"
    cache.sync()

    new_cache = YamlCacheStorage.open(tmp_cache_file)

    assert new_cache["foo"] == "bar"
