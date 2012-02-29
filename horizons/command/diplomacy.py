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

from horizons.util import WorldObject
from horizons.command import Command

class GenericDiplomacyCommand(Command):
	def __init__(self, a, b):
		self.player1_id = a.worldid
		self.player2_id = b.worldid

class AddAllyPair(GenericDiplomacyCommand):
	def __call__(self, issuer):
		player1 = WorldObject.get_object_by_id(self.player1_id)
		player2 = WorldObject.get_object_by_id(self.player2_id)
		player1.session.world.diplomacy.add_ally_pair(player1, player2)

Command.allow_network(AddAllyPair)

class AddEnemyPair(GenericDiplomacyCommand):
	def __call__(self, issuer):
		player1 = WorldObject.get_object_by_id(self.player1_id)
		player2 = WorldObject.get_object_by_id(self.player2_id)
		player1.session.world.diplomacy.add_enemy_pair(player1, player2)

Command.allow_network(AddEnemyPair)

class AddNeutralPair(GenericDiplomacyCommand):
	def __call__(self, issuer):
		player1 = WorldObject.get_object_by_id(self.player1_id)
		player2 = WorldObject.get_object_by_id(self.player2_id)
		player1.session.world.diplomacy.add_neutral_pair(player1, player2)

Command.allow_network(AddNeutralPair)

