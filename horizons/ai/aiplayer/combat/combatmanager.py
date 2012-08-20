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
from collections import defaultdict

import logging
from fife import fife
from weakref import WeakKeyDictionary
import horizons
from horizons.ai.aiplayer.behavior import BehaviorManager
from horizons.ai.aiplayer.behavior.movecallbacks import BehaviorMoveCallback
from horizons.ai.aiplayer.combat.unitmanager import UnitManager
from horizons.component.namedcomponent import NamedComponent
from horizons.constants import LAYERS, AI
from horizons.ext.enum import Enum
from horizons.util.python.callback import Callback
from horizons.util.python.defaultweakkeydictionary import DefaultWeakKeyDictionary
from horizons.util.shapes.point import Point
from horizons.util.worldobject import WorldObject


class CombatManager(object):
	"""
	CombatManager object is responsible for handling close combat in game.
	It scans the environment (lookout) and requests certain actions from behavior
	"""
	log = logging.getLogger("ai.aiplayer.combat.combatmanager")

	# states to keep track of combat movement of each ship.

	shipStates = Enum('idle', 'moving')

	combat_range = 18

	def __init__(self, owner):
		super(CombatManager, self).__init__()
		self.__init(owner)

	def __init(self, owner):
		self.owner = owner
		self.unit_manager = owner.unit_manager
		self.world = owner.world
		self.session = owner.session

		# Dictionary of ship => shipState
		self.ships = DefaultWeakKeyDictionary(lambda ship: self.shipStates.idle)

	@classmethod
	def close_range(cls, ship):
		"""
		Range used when wanting to get close to ships.
		"""
		return (2*ship._max_range + ship._min_range)/3 + 1

	@classmethod
	def fallback_range(cls, ship):
		"""
		Range used when wanting to get away from ships.
		"""
		return cls.combat_range - 1

	def save(self, db):
		for ship, state in self.ships.iteritems():
			db("INSERT INTO ai_combat_ship (owner_id, ship_id, state_id) VALUES (?, ?, ?)", self.owner.worldid, ship.worldid, state.index)

	def set_ship_state(self, ship, state):
		self.ships[ship] = state

	def get_ship_state(self, ship):
		if ship not in self.ships:
			self.ships[ship] = self.shipStates.idle
		return self.ships[ship]

	def add_new_unit(self, ship, state=None):
		if not state:
			state = self.shipStates.idle

		self.set_ship_state(ship, state)

	def remove_unit(self, ship):
		if ship in self.ships:
			del self.ships[ship]

	@classmethod
	def load(cls, db, owner):
		self = cls.__new__(cls)
		self._load(db, owner)
		return self

	def _load(self, db, owner):
		self.__init(owner)

		db_result = db("SELECT ship_id, state_id FROM ai_combat_ship WHERE owner_id = ?", self.owner.worldid)
		for (ship_id, state_id,) in db_result:
			ship = WorldObject.get_object_by_id(ship_id)
			state = self.shipStates[state_id]

			# add move callbacks corresponding to given state
			if state == self.shipStates.moving:
				ship.add_move_callback(Callback(BehaviorMoveCallback._arrived, ship))

			self.add_new_unit(ship, state)

	# DISPLAY-RELATED FUNCTIONS
	def _init_fake_tile(self):
		"""Sets the _fake_tile_obj class variable with a ready to use fife object. To create a new fake tile, use _add_fake_tile()"""
		# use fixed SelectableBuildingComponent here, to make sure subclasses also read the same variable
		if not hasattr(CombatManager, "_fake_range_tile_obj"):
			# create object to create instances from
			CombatManager._fake_range_tile_obj = horizons.main.fife.engine.getModel().createObject('_fake_range_tile_obj', 'ground')
			fife.ObjectVisual.create(CombatManager._fake_range_tile_obj)

			img_path = 'content/gfx/fake_water.png'
			img = horizons.main.fife.imagemanager.load(img_path)
			for rotation in [45, 135, 225, 315]:
				CombatManager._fake_range_tile_obj.get2dGfxVisual().addStaticImage(rotation, img.getHandle())
		if not hasattr(self, '_selected_fake_tiles'):
			self._selected_fake_tiles = []
		if not hasattr(self, '_selected_tiles'):
			self._selected_tiles = []

	def _add_fake_tile(self, x, y, layer, renderer, color):
		"""Adds a fake tile to the position. Requires 'self._fake_tile_obj' to be set."""
		inst = layer.createInstance(CombatManager._fake_range_tile_obj, fife.ModelCoordinate(x, y, 0), "")
		fife.InstanceVisual.create(inst)
		self._selected_fake_tiles.append(inst)
		renderer.addColored(inst, *color)

	def _add_tile(self, tile, renderer, color):
		self._selected_tiles.append(tile)
		renderer.addColored(tile._instance, *color)

	def _clear_fake_tiles(self):
		if not hasattr(self, '_selected_fake_tiles'):
			return
		renderer = self.session.view.renderer['InstanceRenderer']
		for tile in self._selected_fake_tiles:
			renderer.removeColored(tile)
			self.session.view.layers[LAYERS.FIELDS].deleteInstance(tile)
		self._selected_fake_tiles = []

		for tile in self._selected_tiles:
			renderer.removeColored(tile._instance)
		self._selected_tiles = []

	def _highlight_points(self, points, color):
		renderer = self.session.view.renderer['InstanceRenderer']
		layer = self.session.world.session.view.layers[LAYERS.FIELDS]
		for point in points:
			tup = (point.x, point.y)
			island_tile = [island for island in self.session.world.islands if island.get_tile_tuple(tup)]
			if island_tile:
				tile = island_tile[0].get_tile_tuple(tup)
				self._add_tile(tile, renderer, color)
			else:
				self._add_fake_tile(tup[0], tup[1], layer, renderer, color)

	def _highlight_circle(self, position, radius, color):
		points = set(self.session.world.get_points_in_radius(position, radius))
		points2 = set(self.session.world.get_points_in_radius(position, radius-1))
		self._highlight_points(list(points-points2), color)

	def display(self):
		"""
		Display combat ranges.
		"""
		if not AI.HIGHLIGHT_COMBAT:
			return

		combat_range_color = (80, 0, 250)
		attack_range_color = (255, 0, 0)
		close_range_color = (0, 0, 100)
		fallback_range_color = (0, 180, 100)
		center_point_color = (0, 200, 0)

		self._clear_fake_tiles()
		self._init_fake_tile()

		for ship, state in self.ships.iteritems():
			range = self.combat_range
			self._highlight_circle(ship.position, range, combat_range_color)
			self._highlight_circle(ship.position, self.close_range(ship), close_range_color)
			self._highlight_circle(ship.position, self.fallback_range(ship), fallback_range_color)
			self._highlight_circle(ship.position, ship._max_range, attack_range_color)
			self._highlight_circle(ship.position, ship._min_range, attack_range_color)
			self._highlight_points([ship.position], center_point_color)

	def handle_mission_combat(self, mission):
		"""
		Routine for handling combat in mission that requests for it.
		"""
		filters = self.unit_manager.filtering_rules
		fleet = mission.fleet

		ship_group = fleet.get_ships()
		ship_group = self.unit_manager.filter_ships(ship_group, (filters.ship_state(self.ships, self.shipStates.idle)))

		if not ship_group:
			mission.abort_mission()

		ships_around = self.unit_manager.find_ships_near_group(ship_group, self.combat_range)
		ships_around = self.unit_manager.filter_ships(ships_around, (filters.hostile(), ))
		pirate_ships = self.unit_manager.filter_ships(ships_around, (filters.pirate(), ))
		fighting_ships = self.unit_manager.filter_ships(ships_around, (filters.fighting(), ))
		working_ships = self.unit_manager.filter_ships(ships_around, (filters.working(), ))

		environment = {'ship_group': ship_group}

		# begin combat if it's still unresolved
		if fighting_ships:
			environment['enemies'] = fighting_ships
			environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, fighting_ships)
			self.log.debug("Player: %s vs Player: %s -> power_balance:%s", self.owner.name, fighting_ships[0].owner.name, environment['power_balance'])
			self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
				'fighting_ships_in_sight', **environment)
		elif pirate_ships:
			environment['enemies'] = pirate_ships
			environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, pirate_ships)
			self.log.debug("Player: %s vs Player: %s -> power_balance:%s", self.owner.name, pirate_ships[0].owner.name, environment['power_balance'])
			self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
				'pirate_ships_in_sight', **environment)
		elif working_ships:
			environment['enemies'] = working_ships
			self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
				'working_ships_in_sight', **environment)
		else:
			# no one else is around to fight -> continue mission
			mission.continue_mission()

	def handle_uncertain_combat(self, mission):
		"""
		Handles fleets that may way to be in combat.
		"""
		filters = self.unit_manager.filtering_rules

		# test first whether requesting for combat is of any use (any ships nearby)
		ship_group = mission.fleet.get_ships()

		# filter out ships that are already doing a combat move
		ship_group = self.unit_manager.filter_ships(ship_group, (filters.ship_state(self.ships, self.shipStates.idle)))
		ships_around = self.unit_manager.find_ships_near_group(ship_group, self.combat_range)
		ships_around = self.unit_manager.filter_ships(ships_around, (filters.hostile()))
		pirate_ships = self.unit_manager.filter_ships(ships_around, (filters.pirate(), ))
		fighting_ships = self.unit_manager.filter_ships(ships_around, (filters.fighting(), ))
		working_ships = self.unit_manager.filter_ships(ships_around, (filters.working(), ))

		if fighting_ships:
			environment = {'enemies': fighting_ships}
			if self.owner.strategy_manager.request_to_pause_mission(mission, **environment):
				self.handle_mission_combat(mission)
		elif pirate_ships:
			environment = {'enemies': pirate_ships}
			if self.owner.strategy_manager.request_to_pause_mission(mission, **environment):
				self.handle_mission_combat(mission)
		elif working_ships:
			environment = {'enemies': working_ships}
			if self.owner.strategy_manager.request_to_pause_mission(mission, **environment):
				self.handle_mission_combat(mission)

	def handle_casual_combat(self):
		"""
		Handles combat for ships wandering around the map (not assigned to any fleet/mission).
		"""
		filters = self.unit_manager.filtering_rules

		rules = (filters.not_in_fleet(), filters.fighting(), filters.ship_state(self.ships, self.shipStates.idle))
		for ship in self.unit_manager.get_ships(rules):
			# Turn into one-ship group, since reasoning is based around groups of ships
			ship_group = [ship, ]
			# TODO: create artificial groups by dividing ships that are nearby into groups based on their distance.
			# This may end up being costly, so postpone until we have more cpu resources to spare.

			ships_around = self.unit_manager.find_ships_near_group(ship_group, self.combat_range)
			pirate_ships = self.unit_manager.filter_ships(ships_around, (filters.pirate(), ))
			fighting_ships = self.unit_manager.filter_ships(ships_around, (filters.fighting(), ))
			working_ships = self.unit_manager.filter_ships(ships_around, (filters.working(), ))
			environment = {'ship_group': ship_group}
			if fighting_ships:
				environment['enemies'] = fighting_ships
				environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, fighting_ships)
				self.log.debug("Player: %s vs Player: %s -> power_balance:%s", self.owner.name, fighting_ships[0].owner.name, environment['power_balance'])
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
					'fighting_ships_in_sight', **environment)
			elif pirate_ships:
				environment['enemies'] = pirate_ships
				environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, pirate_ships)
				self.log.debug("Player: %s vs Player: %s -> power_balance:%s", self.owner.name, pirate_ships[0].owner.name, environment['power_balance'])
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
					'pirate_ships_in_sight', **environment)
			elif working_ships:
				environment['enemies'] = working_ships
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
					'working_ships_in_sight', **environment)
			else:
				# execute idle action only if whole fleet is idle
				# we check for AIPlayer state here
				if all((self.owner.ships[ship] == self.owner.shipStates.idle for ship in ship_group)):
					self.owner.behavior_manager.request_action(BehaviorManager.action_types.idle,
						'no_one_in_sight', **environment)

	def lookout(self):
		"""
		Basically do 3 things:
		1. Handle combat for missions that explicitly request for it.
		2. Check whether any of current missions may want to be interrupted to resolve potential
			combat that was not planned (e.g. hostile ships nearby fleet on a mission)
		3. Handle combat for ships currently not used in any mission.
		"""
		# handle fleets that explicitly request to be in combat
		for mission in self.owner.strategy_manager.get_missions(condition=lambda mission: mission.combat_phase):
			self.handle_mission_combat(mission)

		# handle fleets that may way to be in combat, but request for it first
		for mission in self.owner.strategy_manager.get_missions(condition=lambda mission: not mission.combat_phase):
			self.handle_uncertain_combat(mission)

		# handle idle ships that are wandering around the map
		self.handle_casual_combat()

		# Log ship states every tick
		if self.log.isEnabledFor(logging.DEBUG):
			self.log.debug("Player:%s Ships combat states:", self.owner.name)
			for ship, state in self.ships.iteritems():
				self.log.debug(" %s: %s", ship.get_component(NamedComponent).name, state)

	def tick(self):
		self.lookout()
		self.display()


class PirateCombatManager(CombatManager):
	"""
	Pirate player requires slightly different handling of combat, thus it gets his own CombatManager.
	Pirate player is able to use standard BehaviorComponents in it's BehaviorManager.
	"""
	log = logging.getLogger("ai.aiplayer.piratecombatmanager")

	shipStates = Enum.get_extended(CombatManager.shipStates, 'chasing_ship', 'going_home')

	def __init__(self, owner):
		super(PirateCombatManager, self).__init__(owner)

	def handle_mission_combat(self, mission):
		"""
		Routine for handling combat in mission that requests for it.
		"""
		filters = self.unit_manager.filtering_rules
		fleet = mission.fleet

		ship_group = fleet.get_ships()
		ship_group = self.unit_manager.filter_ships(ship_group, (filters.ship_state(self.ships, self.shipStates.idle)))

		if not ship_group:
			mission.abort_mission()

		ships_around = self.unit_manager.find_ships_near_group(ship_group, self.combat_range)
		ships_around = self.unit_manager.filter_ships(ships_around, (filters.hostile(), ))
		fighting_ships = self.unit_manager.filter_ships(ships_around, (filters.fighting(), ))
		working_ships = self.unit_manager.filter_ships(ships_around, (filters.working(), ))

		environment = {'ship_group': ship_group}

		# begin combat if it's still unresolved
		if fighting_ships:
			environment['enemies'] = fighting_ships
			environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, fighting_ships)
			self.log.debug("Player: %s vs Player: %s -> power_balance:%s", self.owner.name, fighting_ships[0].owner.name, environment['power_balance'])
			self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
				'fighting_ships_in_sight', **environment)
		elif working_ships:
			environment['enemies'] = working_ships
			self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
				'working_ships_in_sight', **environment)
		else:
			# no one else is around to fight -> continue mission
			mission.continue_mission()

	def handle_uncertain_combat(self, mission):
		"""
		Handles fleets that may way to be in combat.
		"""
		filters = self.unit_manager.filtering_rules

		# test first whether requesting for combat is of any use (any ships nearby)
		ship_group = mission.fleet.get_ships()
		ship_group = self.unit_manager.filter_ships(ship_group, (filters.ship_state(self.ships, self.shipStates.idle)))
		ships_around = self.unit_manager.find_ships_near_group(ship_group, self.combat_range)
		ships_around = self.unit_manager.filter_ships(ships_around, (filters.hostile()))
		fighting_ships = self.unit_manager.filter_ships(ships_around, (filters.fighting(), ))
		working_ships = self.unit_manager.filter_ships(ships_around, (filters.working(), ))

		if fighting_ships:
			environment = {'enemies': fighting_ships}
			if self.owner.strategy_manager.request_to_pause_mission(mission, **environment):
				self.handle_mission_combat(mission)
		elif working_ships:
			environment = {'enemies': working_ships}
			if self.owner.strategy_manager.request_to_pause_mission(mission, **environment):
				self.handle_mission_combat(mission)

	def handle_casual_combat(self):
		"""
		Combat with idle ships (not assigned to a mission)
		"""
		filters = self.unit_manager.filtering_rules

		rules = (filters.not_in_fleet(), filters.pirate(), filters.ship_state(self.ships, self.shipStates.idle))
		for ship in self.unit_manager.get_ships(rules):
			# Turn into one-ship group, since reasoning is based around groups of ships
			ship_group = [ship, ]

			ships_around = self.unit_manager.find_ships_near_group(ship_group, self.combat_range)
			fighting_ships = self.unit_manager.filter_ships(ships_around, (filters.fighting(), ))
			working_ships = self.unit_manager.filter_ships(ships_around, (filters.working(), ))
			environment = {'ship_group': ship_group}
			if fighting_ships:
				environment['enemies'] = fighting_ships
				environment['power_balance'] = UnitManager.calculate_power_balance(ship_group, fighting_ships)
				self.log.debug("Player: %s vs Player: %s -> power_balance:%s", self.owner.name, fighting_ships[0].owner.name, environment['power_balance'])
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
					'fighting_ships_in_sight', **environment)
			elif working_ships:
				environment['enemies'] = working_ships
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.offensive,
					'working_ships_in_sight', **environment)
			else:
				self.owner.behavior_manager.request_action(BehaviorManager.action_types.idle,
					'no_one_in_sight', **environment)
