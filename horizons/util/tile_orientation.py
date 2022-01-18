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

from horizons.constants import BUILDINGS


def get_tile_alignment_action(origin, is_similar_tile):
	"""
	ROAD/WALL ORIENTATION CHEATSHEET
	================================
	a       b
	 \  e  /     a,b,c,d are connections to nearby roads
	  \   /
	   \ /       e,f,g,h indicate whether this area occupies more space than
	 h  X  f     a single road would (i.e. whether we should fill this three-
	   / \       cornered space with graphics that will make it look like a
	  /   \      coherent square instead of many short-circuit road circles).
	 /  g  \     Note that 'e' can only be placed if both 'a' and 'b' exist.
	d       c

	SAMPLE ROADS
	============
	\     \     \..../  \    /    \    /
	 \    .\     \../    \  /.     \  /.
	  \   ..\     \/      \/..      \/..
	  /   ../     /         ..      /\..
	 /    ./     /           .     /..\.
	/     /     /                 /....\

	ad    adh   abde   abf (im-   abcdfg
			   possible)
	"""
	action = ''

	# Order is important here.
	ordered_actions = sorted(BUILDINGS.ACTION.action_offset_dict.items())
	for action_part, (xoff, yoff) in ordered_actions:
		if not is_similar_tile(origin.offset(xoff, yoff)):
			continue

		if action_part in 'abcd':
			action += action_part
		if action_part in 'efgh':
			# Now check whether we can place valid road-filled areas.
			# Only adds 'g' to action if both 'c' and 'd' are in already
			# (that's why order matters - we need to know at this point)
			# and the condition for 'g' is met: road tiles exist in that
			# direction.
			fill_left = chr(ord(action_part) - 4) in action
			# 'h' has the parents 'd' and 'a' (not 'e'), so we need a slight hack here.
			fill_right = chr(ord(action_part) - 3 - 4 * (action_part == 'h')) in action
			if fill_left and fill_right:
				action += action_part
	if action == '':
		# Single trail piece with no neighbor road tiles.
		action = 'single'

	return action
