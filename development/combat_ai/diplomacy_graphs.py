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

"""
This is a balancing tool for diplomacy which makes setting diplomacy parameters (such as mid, root or peek) easier.
It requires matplotlib (along with pylab) library in order to plot functions.

Usage:
1. Run the script from UH root, i.e. python development/combat_ai/diplomacy_graphs.py
2. A graph should appear on screen displaying current functions for each of the settings (see parameter_sets below)
3. After you close the plot window, next one should appear
4. Uncomment functions from parameter_sets you don't want to have displayed
"""
from __future__ import print_function

import sys
import pylab

sys.path.append(".")
sys.path.append("./horizons")
sys.path.append("./horizons/util")

try:
	import run_uh
except ImportError as e:
	print(e.message)
	print("Please run from Unknown Horizons root dir")
	sys.exit(1)

from run_uh import init_environment
init_environment(False)

import horizons.main

from horizons.ai.aiplayer.behavior.diplomacysettings import DiplomacySettings
from horizons.ai.aiplayer.behavior.behaviorcomponents import BehaviorDiplomatic

_move_f = BehaviorDiplomatic._move_f
_get_quadratic_function = BehaviorDiplomatic._get_quadratic_function
get_enemy_function = BehaviorDiplomatic.get_enemy_function
get_ally_function = BehaviorDiplomatic.get_ally_function
get_neutral_function = BehaviorDiplomatic.get_neutral_function


def diplomacy_graph():
	header = "Diplomacy function"
	x_label = "relationship_score"
	y_label = "probability"

	# define functions here to plot them.
	# Second parameter is color
	upper_boundary = DiplomacySettings.upper_boundary

	parameter_sets = (

		("BehaviorGood.allied_player", DiplomacySettings.Good.parameters_allied),
		("BehaviorGood.neutral_player", DiplomacySettings.Good.parameters_neutral),
		("BehaviorGood.hostile_player", DiplomacySettings.Good.parameters_hostile),

		("BehaviorNeutral.allied_player", DiplomacySettings.Neutral.parameters_hostile),
		("BehaviorNeutral.neutral_player", DiplomacySettings.Neutral.parameters_neutral),
		("BehaviorNeutral.hostile_player", DiplomacySettings.Neutral.parameters_hostile),

		("BehaviorEvil.allied_player", DiplomacySettings.Evil.parameters_hostile),
		("BehaviorEvil.neutral_player", DiplomacySettings.Evil.parameters_neutral),
		("BehaviorEvil.hostile_player", DiplomacySettings.Evil.parameters_hostile),

	)

	for parameter_name, parameters in parameter_sets:

		# always print upper boundary
		x = [-10, 10]
		y = [upper_boundary] * 2
		pylab.plot(x, y, color='y', marker=None)

		functions = []
		if 'enemy' in parameters:
			functions.append((get_enemy_function(**parameters['enemy']), 'r'))
		if 'ally' in parameters:
			functions.append((get_ally_function(**parameters['ally']), 'g'))
		if 'neutral' in parameters:
			functions.append((get_neutral_function(**parameters['neutral']), 'b'))

		for f, c in functions:
			gen = [(x / 10.0, f(x / 10.0)) for x in xrange(-100, 100)]
			x = [item[0] for item in gen]
			y = [item[1] for item in gen]
			pylab.plot(x, y, color=c, marker=None)
			pylab.xlabel(x_label)
			pylab.ylabel(y_label)
			pylab.title(parameter_name)
			pylab.grid(True)
		pylab.show()


if __name__ == "__main__":
	diplomacy_graph()
