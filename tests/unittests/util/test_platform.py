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
# Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

import os

from horizons.util.platform import get_user_game_directories


def test_get_user_game_directory_windows(tmpdir, mocker):
	tmpdir = str(tmpdir)
	mocker.patch('platform.system', return_value='Windows')
	_config_dir, _data_dir, _cache_dir = get_user_game_directories(
		home_directory=tmpdir, env={})

	assert _config_dir == os.path.join(tmpdir, 'My Games', 'unknown-horizons')
	assert _data_dir == os.path.join(tmpdir, 'My Games', 'unknown-horizons')
	assert _cache_dir == os.path.join(tmpdir, 'My Games',
									  'unknown-horizons', 'cache')


def test_get_user_game_directory_unix(tmpdir):
	tmpdir = str(tmpdir)
	_config_dir, _data_dir, _cache_dir = get_user_game_directories(
		home_directory=tmpdir, env={})

	assert _config_dir == os.path.join(tmpdir, '.config', 'unknown-horizons')
	assert _data_dir == os.path.join(tmpdir, '.local', 'share',
									 'unknown-horizons')
	assert _cache_dir == os.path.join(tmpdir, '.cache', 'unknown-horizons')


def test_xdg_config_home_overrides_config_dir(tmpdir):
	"""XDG_CONFIG_HOME overrides config dir, joined with UH suffix."""
	tmpdir = str(tmpdir)
	env = {'XDG_CONFIG_HOME': '/custom/config'}
	config_dir, _, _ = get_user_game_directories(
		home_directory=tmpdir, env=env)
	assert config_dir == '/custom/config/unknown-horizons'


def test_xdg_data_home_overrides_data_dir(tmpdir):
	"""XDG_DATA_HOME overrides data dir, joined with UH suffix."""
	tmpdir = str(tmpdir)
	env = {'XDG_DATA_HOME': '/custom/data'}
	_, data_dir, _ = get_user_game_directories(
		home_directory=tmpdir, env=env)
	assert data_dir == '/custom/data/unknown-horizons'


def test_xdg_cache_home_overrides_cache_dir(tmpdir):
	"""XDG_CACHE_HOME overrides cache dir, joined with UH suffix."""
	tmpdir = str(tmpdir)
	env = {'XDG_CACHE_HOME': '/custom/cache'}
	_, _, cache_dir = get_user_game_directories(
		home_directory=tmpdir, env=env)
	assert cache_dir == '/custom/cache/unknown-horizons'


def test_uh_user_dir_overrides_config_dir(tmpdir):
	"""UH_USER_DIR overrides XDG_CONFIG_HOME for config_dir."""
	tmpdir = str(tmpdir)
	env = {'XDG_CONFIG_HOME': '/custom/config',
	       'UH_USER_DIR': '/custom/user'}
	config_dir, _, _ = get_user_game_directories(
		home_directory=tmpdir, env=env)
	assert config_dir == '/custom/user'


def test_uh_user_config_dir_wins_over_uh_user_dir(tmpdir):
	"""UH_USER_CONFIG_DIR has highest priority for config_dir."""
	tmpdir = str(tmpdir)
	env = {'UH_USER_DIR': '/custom/user',
	       'UH_USER_CONFIG_DIR': '/explicit/config'}
	config_dir, _, _ = get_user_game_directories(
		home_directory=tmpdir, env=env)
	assert config_dir == '/explicit/config'


def test_env_missing_uses_defaults(tmpdir):
	"""No env vars means defaults are used unchanged."""
	tmpdir = str(tmpdir)
	config_dir, data_dir, cache_dir = get_user_game_directories(
		home_directory=tmpdir, env={})

	assert config_dir == os.path.join(tmpdir, '.config', 'unknown-horizons')
	assert data_dir == os.path.join(tmpdir, '.local', 'share',
									 'unknown-horizons')
	assert cache_dir == os.path.join(tmpdir, '.cache', 'unknown-horizons')


def test_cache_dir_uses_user_dir_cache_suffix(tmpdir):
	"""UH_USER_DIR is joined with 'cache' for cache_dir."""
	tmpdir = str(tmpdir)
	env = {'UH_USER_DIR': '/custom/user'}
	_, _, cache_dir = get_user_game_directories(
		home_directory=tmpdir, env=env)

	assert cache_dir == '/custom/user/cache'


def test_uh_user_dir_overrides_xdg_data_home(tmpdir):
	"""UH_USER_DIR overrides XDG_DATA_HOME for data_dir."""
	tmpdir = str(tmpdir)
	env = {'XDG_DATA_HOME': '/custom/data',
	       'UH_USER_DIR': '/custom/user'}
	_, data_dir, _ = get_user_game_directories(
		home_directory=tmpdir, env=env)
	assert data_dir == '/custom/user'