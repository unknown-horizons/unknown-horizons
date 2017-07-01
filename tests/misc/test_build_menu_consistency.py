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
	Parse referenced building from yaml data.
	"""
	for section in yaml_data.values():
		for value in section:
			if type(value) != list:
				continue

			for text in value:
				if text.startswith('BUILDING'):
					yield text


def test_build_menu_consistency():
	"""
	Check that the same buildings are referenced in both configurations of the build menu.
	"""
	assert len(BuildTab.build_menus) == 2, 'Expected 2 build menu configs'

	buildings = []
	for filename in BuildTab.build_menus:
		with open(os.path.join(ROOT_DIR, filename)) as f:
			data = YamlCache.load_yaml_data(f)
			buildings.append(sorted(list(_get_referenced_buildings(data))))

	assert buildings[0] == buildings[1]
