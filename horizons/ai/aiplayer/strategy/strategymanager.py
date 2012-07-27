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

from horizons.ai.aiplayer.combat.condition import Condition, get_all_conditions
from horizons.ai.aiplayer.strategy.condition import  get_all_conditions
from horizons.component.namedcomponent import NamedComponent


class StrategyManager(object):
	"""
	StrategyManager object is responsible for handling major decisions in game such as
	sending fleets to battle, keeping track of diplomacy between players, declare wars.
	"""
	log = logging.getLogger("ai.aiplayer.fleetmission")

	def __init__(self, owner):
		super(StrategyManager, self).__init__()
		self.__init(owner)

	def __init(self, owner):
		self.owner = owner
		self.world = owner.world
		self.session = owner.session
		self.unit_manager = owner.unit_manager
		self.missions = set()
		self.conditions = get_all_conditions(self.owner)

	def report_success(self, mission, msg):
		self.log.info("Player: %s|StrategyManager|Mission %s was a success: %s", self.owner.worldid, mission, msg)
		self.end_mission(mission)

	def report_failure(self, mission, msg):
		self.log.info("Player: %s|StrategyManager|Mission %s was a failure: %s", self.owner.worldid, mission, msg)
		self.end_mission(mission)

	def end_mission(self, mission):
		self.log.info("Player: %s|StrategyManager|Mission %s ended", self.owner.worldid, mission)
		if mission in self.missions:
			self.missions.remove(mission)

	def start_mission(self, mission):
		self.log.info("Player: %s|StrategyManager|Mission %s started", self.owner.worldid, mission)
		self.missions.add(mission)
		mission.start()

	def get_missions(self, condition=None):
		"""
		Get missions filtered by certain condition (by default return all missions)
		"""
		if condition:
			return [mission for mission in self.missions if condition(mission)]
		else:
			return self.missions

	def request_to_pause_mission(self, mission):
		"""
		@return: returns True is mission is allowed to pause, False otherwise
		@rtype: bool
		"""
		# TODO: make that decision based on environment (**environment as argument)
		mission.pause_mission()
		return True

	def handle_strategy(self):
		filters = self.unit_manager.filtering_rules
		rules = (filters.ship_state((self.owner.shipStates.idle,)), filters.fighting(), filters.not_in_fleet())

		# Get all available ships that can take part in a mission
		idle_ships = self.unit_manager.get_ships(rules)

		# Get all other players
		other_players = [player for player in self.session.world.players if player != self.owner]

		# Prepare environment
		environment = {'idle_ships': idle_ships, 'players': other_players}

		# Check which conditions occur
		occuring_conditions = []

		print
		print
		print "CONDITIONS"
		for condition in self.conditions.keys():
			condition_outcome = condition.check(**environment)
			print " ",condition.__class__.__name__,":", ("Yes" if condition_outcome else "No")
			if condition_outcome:
				occuring_conditions.append((condition, condition_outcome))

		# Nothing to do when none of the conditions occur
		if occuring_conditions:
			# Choose the most important one
			selected_condition, selected_outcome = sorted(occuring_conditions, key = lambda c: self.conditions[c[0]] * c[1]['certainty'], reverse=True)[0]
			print "SELECTED:"
			print selected_condition.__class__.__name__
			for key, value in selected_outcome.iteritems():
				print " %s: %s" % (key, value)
			print "//CONDITIONS"

			# Insert condition-gathered info into environment
			for key, value in selected_outcome.iteritems():
				environment[key] = value

			# Try to execute a mission that resolves given condition the best
			mission = self.owner.behavior_manager.request_strategy(**environment)
			if mission:
				self.start_mission(mission)

		## TODO: Debugging section, remove later
		"""j
		print "IDLE SHIPS"
		for ship in idle_ships:
			print " ",ship.get_component(NamedComponent).name
		print "//IDLE SHIPS"
		"""
		print "MISSIONS"
		for mission in list(self.missions):
			print " ",mission
		print "//MISSIONS"
		"""
		print "FLEETS"
		for fleet in list(self.unit_manager.fleets):
			print " ", fleet
		for ship, fleet in self.unit_manager.ships.iteritems():
			print ship.get_component(NamedComponent).name, fleet.worldid
		print "//FLEETS"
		"""

	def tick(self):
		self.handle_strategy()
