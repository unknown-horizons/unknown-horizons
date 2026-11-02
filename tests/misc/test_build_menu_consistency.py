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

import horizons.main  # this import needs to stay to avoid errors with BuildTab
from horizons.gui.tabs.buildtabs import BuildTab
from horizons.util.yamlcache import YamlCache

ROOT_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../')


def _get_referenced_buildings(yaml_data):
	"""
	Parse referenced building string tokens from raw yaml data.
	"""
	for section in yaml_data.values():
		if not isinstance(section, list):
			continue

		for value in section:
			if not isinstance(value, list):
				continue

			for text in value:
				if isinstance(text, str) and text.startswith('BUILDINGS.'):
					yield text


def _get_building_ids(yaml_data):
	"""
	Extract converted numeric building IDs from game-loaded yaml data.
	"""
	for section in yaml_data.values():
		if not isinstance(section, list):
			continue

		for value in section:
			if not isinstance(value, list):
				continue

			for entry in value:
				if isinstance(entry, int):
					yield entry


def test_build_menu_files_exist():
	"""
	Verify that all configured build menu files actually exist on disk.
	"""
	assert len(BuildTab.build_menus) == 2, 'Expected 2 build menu configs'
	for filename in BuildTab.build_menus:
		assert os.path.isfile(os.path.join(ROOT_DIR, filename)), f"Build menu file missing: {filename}"


def test_build_menu_consistency():
	"""
	Check that the same buildings are referenced in both configurations of the build menu.
	"""
	menus = []
	for filename in BuildTab.build_menus:
		with open(os.path.join(ROOT_DIR, filename)) as f:
			data = YamlCache.load_yaml_data(f)
			menus.append(set(_get_referenced_buildings(data)))

	assert menus[0] == menus[1], "Per-tier and per-type build menus reference different sets of buildings"


def test_build_menu_contains_meta_section():
	"""
	Verify that every build menu file contains the required 'meta' section.
	"""
	for filename in BuildTab.build_menus:
		with open(os.path.join(ROOT_DIR, filename)) as f:
			data = YamlCache.load_yaml_data(f)
		assert "meta" in data, f"Missing 'meta' section in {filename}"


def test_build_menu_contains_unlocking_strategy():
	"""
	Verify that the meta section specifies an unlocking strategy.
	"""
	for filename in BuildTab.build_menus:
		with open(os.path.join(ROOT_DIR, filename)) as f:
			data = YamlCache.load_yaml_data(f)
		assert "unlocking_strategy" in data.get("meta", {}), f"Missing 'unlocking_strategy' in {filename} meta"


def test_build_menu_loadable_via_game_loader():
	"""
	Verify build-menu files can be successfully loaded through the real game path using token conversion.
	"""
	for filename in BuildTab.build_menus:
		data = YamlCache.get_file(
			os.path.join(ROOT_DIR, filename),
			game_data=True
		)
		assert data, f"Failed to load {filename} via YamlCache with game_data=True"


def test_get_building_tiers_returns_non_empty_mapping():
	"""
	Exercise BuildTab logic directly to ensure tier mappings are properly resolved,
	non-empty, non-negative, and exact key-wise consistent with game-loaded building IDs.
	"""
	tiers = BuildTab.get_building_tiers()
	assert tiers, "BuildTab.get_building_tiers() returned empty mapping"
	assert all(isinstance(v, int) for v in tiers.values()), "Building tier values must be integers"
	assert min(tiers.values()) >= 0, "Building tier values cannot be negative"

	# Load via game loader path so token conversion matches BuildTab internals
	data = YamlCache.get_file(
		os.path.join(ROOT_DIR, BuildTab.build_menu_config_per_tier),
		game_data=True
	)
	buildings = set(_get_building_ids(data))

	assert set(tiers.keys()) == buildings, (
		"Mismatch between extracted building tiers and "
		"per-tier menu references"
	)
