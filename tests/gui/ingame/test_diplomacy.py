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

from tests.gui import gui_test


@gui_test(use_dev_map=True, ai_players=1)
def test_diplomacy(gui):
	"""Test changing diplomacy status."""

	human = gui.session.world.player

	players = list(gui.session.world.players)
	players.remove(human)

	pirate = gui.session.world.pirate
	ai = players[0]

	diplomacy = gui.session.world.diplomacy

	# Make sure they are neutral at first
	for p in (ai, pirate):
		assert diplomacy.are_neutral(human, p)

	# Ally with first player
	gui.trigger('mainhud/diplomacyButton')
	gui.trigger('tab0/ally_check_box')

	assert diplomacy.are_allies(human, ai)

	# Be enemy with second player
	gui.trigger('tab_base/1')
	gui.trigger('tab0/enemy_check_box')

	assert diplomacy.are_enemies(human, pirate)
