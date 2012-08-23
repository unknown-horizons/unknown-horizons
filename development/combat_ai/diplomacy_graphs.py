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

"""
This is a balancing tool for diplomacy which makes setting diplomacy parameters (such as mid, root or peek)
It requires matplotlib (along with pylab) library in order to plot functions.
"""

from pylab import *

sys.path.append(".")
sys.path.append("./horizons")
sys.path.append("./horizons/util")

# So far I couldn't easily pull these functions from the code itself, so check if these match with code in BehaviorDiplomatic (ai.aiplayer.behavior.behaviorcomponents.py)
#from horizons.ai.aiplayer.behavior.diplomacysettings import Settings

def _move_f(f, v_x, v_y):
		"""
		Return function f moved by vector (v_x, v_y)
		"""
		return lambda x: f(x - v_x) + v_y

def _get_quadratic_function(mid, root, peek=1.0):
		"""
		Functions for border distributions such as enemy or ally (left or right parabola).
		@param mid: value on axis X that is to be center of the parabola
		@type mid: float
		@param root: value on axis X which is a crossing point of axis OX and the function itself
		@type root: float
		@param peek: value on axis Y which is a peek of a function
		@type peek: float
		@return: quadratic function
		@rtype: lambda(x)
		"""

		# base function is upside-down parabola, stretched in X in order to have roots at exactly 'root' value.
		# (-1. / (abs(mid - root) ** 2)) part is for stretching the parabola in X axis and flipping it upside down, we have to use
		# abs(mid - root) because it's later moved by mid
		# Note: Multiply by 1./abs(mid-root) to scale function in X (e.g. if mid is 1.0 and root is 1.5 -> make original x^2 function 2 times narrower
		base = lambda x: (-1. / (abs(mid - root) ** 2)) * (x ** 2)

		# we move the function so it looks like "distribution", i.e. move it far left(or right), and assume the peek is 1.0
		moved = _move_f(base, mid, 1.0)

		# in case of negative values of f(x) we want to have 0.0 instead
		# we multiply by peek here in order to scale function in Y
		final_function = lambda x: max(0.0, moved(x) * peek)

		return final_function

def get_enemy_function(root, peek=1.0):
	return _get_quadratic_function(-10.0, root, peek)

def get_ally_function(root, peek=1.0):
	return _get_quadratic_function(10.0, root, peek)

def get_neutral_function(mid, root, peek=1.0):
	return _get_quadratic_function(mid, root, peek)

def diplomacy_graph():
	header = "Diplomacy function"
	x_label = "relationship_score"
	y_label = "probability"

	# define functions here to plot them.
	# Second parameter is color
	upper_boundary = 5.0

	parameters = {
		'ally': {'root': 5.0, },
		'enemy': {'root': -6.7, },
	}

	functions = [
		(get_enemy_function(**parameters['enemy']), 'r'), # typical hostile (aka. WAR) function
		#(get_neutral_function(**parameters['neutral']), 'b'), # neutral function
		(get_ally_function(**parameters['ally']), 'g'), # ally function
	 ]
	x = [-10, 10]
	y = [upper_boundary]*2
	plot (x,y,color='y', marker=None)
	for f, c in functions:
		gen = [(x/10.0, f(x/10.0)) for x in xrange(-100, 100) ]
		x = [item[0] for item in gen]
		y = [item[1] for item in gen]
		plot(x,y, color=c,marker=None)
		xlabel(x_label)
		ylabel(y_label)
		title(header)
		grid(True)
	show()

if(__name__=="__main__"):
	diplomacy_graph()