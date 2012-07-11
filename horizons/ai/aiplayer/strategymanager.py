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

import logging
from horizons.ai.aiplayer.behavior import BehaviorManager
from horizons.ai.aiplayer.behavior.profile import BehaviorProfile
from horizons.ai.aiplayer.mission.combat.scouting import ScoutingMission
from horizons.ai.aiplayer.unitmanager import UnitManager
from horizons.command.diplomacy import AddEnemyPair
from horizons.command.unit import Attack
from horizons.component.namedcomponent import NamedComponent
from horizons.util.worldobject import WorldObject
from horizons.world.units.fightingship import FightingShip
from horizons.world.units.pirateship import PirateShip


class StrategyManager(object):
	"""
	StrategyManager object is responsible for handling major decisions in game such as
	sending fleets to battle, keeping track of diplomacy between players, declare wars.
	"""
	log = logging.getLogger("ai.aiplayer.behavior.strategymanager")

	def __init__(self, owner):
		super(StrategyManager, self).__init__()
		self.__init(owner)

	def __init(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.unit_manager = owner.unit_manager

	def handle_strategy(self):
		# TODO: Think of a good way to scan game for certain things here.
		# Create some "Condition" abstraction for that i.e. AreHostileShipsEasyToSingleOut.check(), IsEnemyConsiderablyWeakerAndHostile().check() etc.
		# Then create mission if any of these occur. Probably attach certain priority/certainty measure to each one in case of many hits.

		# All it does currently is send idle ships to scouting missions
		fleets = self.unit_manager.get_available_ship_groups(None)
		for fleet in fleets:
			for ship in fleet:
				if self.owner.ships[ship] == self.owner.shipStates.idle:
					scouting_mission = ScoutingMission.create(self.owner.report_success, self.owner.report_failure, ship)
					self.owner.start_mission(scouting_mission)

	def tick(self):
		self.handle_strategy()
