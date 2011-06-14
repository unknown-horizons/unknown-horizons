# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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

from collections import deque

from builder import Builder
from constants import BUILD_RESULT

from horizons.constants import AI, BUILDINGS
from horizons.util import Point, WorldObject
from horizons.util.python import decorators

class VillageBuilder(WorldObject):
	class purpose:
		none = 1
		reserved = 2
		main_square = 3
		planned_tent = 4
		tent = 5
		road = 6
		pavilion = 7
		village_school = 8

	def __init__(self, settlement_manager):
		super(VillageBuilder, self).__init__()
		self.__init(settlement_manager)
		self._create_plan()

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self.land_manager = settlement_manager.land_manager
		self.island = self.land_manager.island
		self.session = self.island.session
		self.owner = self.land_manager.owner
		self.settlement = self.land_manager.settlement
		self.tents_to_build = 0
		self.pavilions_to_build = 0
		self.plan = {}
		self.tent_queue = deque()

	def save(self, db):
		super(VillageBuilder, self).save(db)
		db("INSERT INTO ai_village_builder(rowid, settlement_manager) VALUES(?, ?)", self.worldid, \
			self.settlement_manager.worldid)
		for (x, y), (purpose, builder) in self.plan.iteritems():
			db("INSERT INTO ai_village_builder_coords(village_builder, x, y, purpose, builder) VALUES(?, ?, ?, ?, ?)", \
				self.worldid, x, y, purpose, None if builder is None else builder.worldid)
			if builder is not None:
				assert isinstance(builder, Builder)
				builder.save(db)

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_village_builder WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		super(VillageBuilder, self).load(db, worldid)
		self.__init(settlement_manager)

		db_result = db("SELECT x, y, purpose, builder FROM ai_village_builder_coords WHERE village_builder = ?", worldid)
		for x, y, purpose, builder_id in db_result:
			coords = (x, y)
			builder = Builder.load(db, builder_id, self.land_manager) if builder_id else None
			self.plan[coords] = (purpose, builder)
			if purpose == self.purpose.planned_tent or purpose == self.purpose.tent:
				self.tents_to_build += 1
		self._create_tent_queue()

		self.pavilions_to_build = 0
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose != self.purpose.pavilion:
				continue
			object = self.land_manager.island.ground_map[coords]
			if object is not None or object.id != BUILDINGS.PAVILION_CLASS:
				self.pavilions_to_build += 1

	@classmethod
	def _remove_unreachable_roads(cls, plan, main_square):
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		reachable = set()
		queue = deque()
		for (x, y) in main_square.position.tuple_iter():
			for (dx, dy) in moves:
				coords = (x + dx, y + dy)
				if coords in plan and plan[coords][0] == cls.purpose.road:
					queue.append(coords)
					reachable.add(coords)

		while queue:
			(x, y) = queue.popleft()
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords in plan and plan[coords][0] == cls.purpose.road and coords not in reachable:
					reachable.add(coords)
					queue.append(coords)

		to_remove = []
		for coords, (purpose, _) in plan.iteritems():
			if purpose == cls.purpose.road and coords not in reachable:
				to_remove.append(coords)
		for coords in to_remove:
			plan[coords] = (cls.purpose.none, None)

	def _create_plan(self):
		"""
		The algorithm is as follows:
		Place the main square and then form a road grid to support the tents;
		prefer the one with maximum number of tent locations and minimum number of
		impossible road locations.
		"""

		self.plan = {}
		best_value = -1
		xs = set([coords[0] for coords in self.land_manager.village])
		ys = set([coords[1] for coords in self.land_manager.village])
		tent_squares = [(0, 0), (0, 1), (1, 0), (1, 1)]
		road_connections = [(-1, 0), (-1, 1), (0, -1), (0, 2), (1, -1), (1, 2), (2, 0), (2, 1)]

		for x, y in self.land_manager.village:
			# will it fit in the area?
			if (x + 5, y + 5) not in self.land_manager.village:
				continue

			point = Point(x, y)
			main_square = Builder.create(BUILDINGS.MARKET_PLACE_CLASS, self.land_manager, point)
			if not main_square:
				continue

			plan = dict.fromkeys(self.land_manager.village, (self.purpose.none, None))
			bad_roads = 0
			good_tents = 0

			# place the main square
			for dy in xrange(6):
				for dx in xrange(6):
					plan[(x + dx, y + dy)] = (self.purpose.reserved, None)
			plan[(x, y)] = (self.purpose.main_square, main_square)

			# place the roads running parallel to the y-axis
			for road_y in ys:
				if road_y < y:
					if (y - road_y) % 5 != 1:
						continue
				else:
					if road_y < y + 6 or (road_y - y) % 5 != 1:
						continue
				for road_x in xs:
					coords = (road_x, road_y)
					if coords not in self.land_manager.village:
						bad_roads += 1
						continue
					road = Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, Point(road_x, road_y))
					if road:
						plan[coords] = (self.purpose.road, road)
					else:
						bad_roads += 1

			# place the roads running parallel to the x-axis
			for road_x in xs:
				if road_x < x:
					if (x - road_x) % 5 != 1:
						continue
				else:
					if road_x < x + 6 or (road_x - x) % 5 != 1:
						continue
				for road_y in ys:
					coords = (road_x, road_y)
					if coords not in self.land_manager.village:
						bad_roads += 1
						continue
					road = Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, Point(road_x, road_y))
					if road:
						plan[coords] = (self.purpose.road, road)
					else:
						bad_roads += 1

			if bad_roads > 0:
				self._remove_unreachable_roads(plan, main_square)

			# place the tents
			for coords in sorted(plan):
				ok = True
				for dx, dy in tent_squares:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 not in plan or plan[coords2][0] != self.purpose.none:
						ok = False
						break
				if not ok:
					continue
				tent = Builder.create(BUILDINGS.RESIDENTIAL_CLASS, self.land_manager, Point(coords[0], coords[1]))
				if not tent:
					continue

				# is there a road connection?
				ok = False
				for dx, dy in road_connections:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 in plan and plan[coords2][0] == self.purpose.road:
						ok = True
						break

				# connection to a road tile exists, build the tent
				if ok:
					for dx, dy in tent_squares:
						plan[(coords[0] + dx, coords[1] + dy)] = (self.purpose.reserved, None)
					plan[coords] = (self.purpose.planned_tent, tent)
					good_tents += 1

			value = 10 * good_tents - bad_roads
			if best_value < value:
				self.plan = plan
				self.tents_to_build = good_tents
				best_value = value
		self._optimize_plan()
		self._reserve_other_buildings()
		self._create_tent_queue()

	def _optimize_plan(self):
		# calculate distance from the main square to every tile
		road_connections = [(-1, 0), (-1, 1), (0, -1), (0, 2), (1, -1), (1, 2), (2, 0), (2, 1)]
		tent_squares = [(0, 0), (0, 1), (1, 0), (1, 1)]
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		distance = {}
		queue = deque()

		for coords, (purpose, builder) in self.plan.iteritems():
			if purpose == self.purpose.main_square:
				for coords in builder.position.tuple_iter():
					distance[coords] = 0
					queue.append(coords)

		while queue:
			(x, y) = queue.popleft()
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords in self.plan and coords not in distance:
					distance[coords] = distance[(x, y)] + 1
					queue.append(coords)

		# remove planned tents from the plan
		for (x, y) in self.plan:
			coords = (x, y)
			if self.plan[coords][0] == self.purpose.planned_tent:
				for dx, dy in tent_squares:
					self.plan[(x + dx, y + dy)] = (self.purpose.none, None)

		# create new possible tent position list
		possible_tents = []
		for coords in self.plan:
			if self.plan[coords][0] == self.purpose.none:
				possible_tents.append((distance[coords], coords))
		possible_tents.sort()

		# place the tents
		for _, (x, y) in possible_tents:
			ok = True
			for dx, dy in tent_squares:
				coords = (x + dx, y + dy)
				if coords not in self.plan or self.plan[coords][0] != self.purpose.none:
					ok = False
					break
			if not ok:
				continue
			tent = Builder.create(BUILDINGS.RESIDENTIAL_CLASS, self.land_manager, Point(x, y))
			if not tent:
				continue

			# is there a road connection?
			ok = False
			for dx, dy in road_connections:
				coords = (x + dx, y + dy)
				if coords in self.plan and self.plan[coords][0] == self.purpose.road:
					ok = True
					break

			# connection to a road tile exists, build the tent
			if ok:
				for dx, dy in tent_squares:
					self.plan[(x + dx, y + dy)] = (self.purpose.reserved, None)
				self.plan[(x, y)] = (self.purpose.planned_tent, tent)

		self._return_unused_space()

	def _return_unused_space(self):
		not_needed = []
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose == self.purpose.none:
				not_needed.append(coords)
		for coords in not_needed:
			self.land_manager.add_to_production(coords)

	def _replace_planned_tent(self, building_id, new_purpose):
		tent_range = 12 # TODO: load it the right way
		planned_tents = [builder for (purpose, builder) in self.plan.itervalues() if purpose == self.purpose.planned_tent]

		max_covered = 0
		min_distance = 0
		best_point = None
		for replaced_builder in planned_tents:
			covered = 0
			distance = 0
			for builder in planned_tents:
				if replaced_builder.position.distance(builder.position) <= tent_range:
					covered += 1
					distance += replaced_builder.position.distance(builder.position)
			if covered > max_covered or (covered == max_covered and min_distance > distance):
				max_covered = covered
				min_distance = distance
				best_point = replaced_builder.position.origin

		if best_point is not None:
			builder = Builder.create(building_id, self.land_manager, best_point)
			print best_point, building_id
			self.plan[best_point.to_tuple()] = (new_purpose, builder)
			self.tents_to_build -= 1
			return True
		return False

	def _reserve_other_buildings(self):
		"""Replaces a planned tent with a pavilion and another with a school."""
		assert self._replace_planned_tent(BUILDINGS.PAVILION_CLASS, self.purpose.pavilion)
		self.pavilions_to_build = 1
		assert self._replace_planned_tent(BUILDINGS.VILLAGE_SCHOOL_CLASS, self.purpose.village_school)

	def _create_tent_queue(self):
		""" This function takes the plan and orders all planned tents according to
		the distance from the main square to the block they belong to. """
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		blocks = []
		block = {}

		# form blocks of tents
		main_square = None
		for coords, (purpose, builder) in self.plan.iteritems():
			if purpose == self.purpose.main_square:
				main_square = builder
			if purpose != self.purpose.planned_tent or coords in block:
				continue
			block[coords] = len(blocks)

			block_list = [coords]
			queue = deque()
			explored = set([coords])
			queue.append(coords)
			while queue:
				(x, y) = queue.popleft()
				for dx, dy in moves:
					coords = (x + dx, y + dy)
					if coords not in self.plan or coords in explored:
						continue
					if self.plan[coords][0] == self.purpose.planned_tent or self.plan[coords][0] == self.purpose.reserved:
						explored.add(coords)
						queue.append(coords)
						if self.plan[coords][0] == self.purpose.planned_tent:
							block[coords] = len(blocks)
							block_list.append(coords)
			blocks.append(block_list)

		# calculate distance from the main square to the block
		block_distances = []
		for coords_list in blocks:
			distance = 0
			for coords in coords_list:
				distance += main_square.position.distance(coords)
			block_distances.append((distance / len(coords_list), coords_list))

		# form the sorted tent queue
		self.tent_queue = deque()
		block_distances.sort()
		for _, block in block_distances:
			for coords in sorted(block):
				self.tent_queue.append(coords)

	def build_roads(self):
		for (purpose, builder) in self.plan.itervalues():
			if purpose == self.purpose.road:
				builder.execute()

	def build_village_building(self, building_id, building_purpose):
		for coords, (purpose, builder) in self.plan.iteritems():
			if purpose == building_purpose:
				object = self.land_manager.island.ground_map[coords]
				if object is not None or object.id != building_id:
					if not builder.have_resources():
						return BUILD_RESULT.NEED_RESOURCES
					building = builder.execute()
					if not building:
						return BUILD_RESULT.UNKNOWN_ERROR
					return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def build_main_square(self):
		return self.build_village_building(BUILDINGS.MARKET_PLACE_CLASS, self.purpose.main_square)

	def build_pavilion(self):
		if self.pavilions_to_build <= 0:
			return BUILD_RESULT.IMPOSSIBLE
		result = self.build_village_building(BUILDINGS.PAVILION_CLASS, self.purpose.pavilion)
		if result == BUILD_RESULT.OK:
			self.pavilions_to_build -= 1
		return result

	def build_village_school(self):
		return self.build_village_building(BUILDINGS.VILLAGE_SCHOOL_CLASS, self.purpose.village_school)

	def build_tent(self):
		if self.tent_queue:
			coords = self.tent_queue[0]
			builder = self.plan[coords][1]
			if not builder.have_resources():
				return BUILD_RESULT.NEED_RESOURCES
			if not builder.execute():
				return BUILD_RESULT.UNKNOWN_ERROR
			self.plan[coords] = (self.purpose.tent, builder)
			self.tent_queue.popleft()
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def count_tents(self):
		tents = 0
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose != self.purpose.tent:
				continue
			object = self.island.ground_map[coords].object
			if object is not None and object.id == BUILDINGS.RESIDENTIAL_CLASS:
				tents += 1
		return tents

	def display(self):
		if not AI.HIGHLIGHT_PLANS:
			return

		road_colour = (30, 30, 30)
		tent_colour = (255, 255, 255)
		planned_tent_colour = (200, 200, 200)
		sq_colour = (255, 0, 255)
		pavilion_colour = (255, 128, 128)
		village_school_colour = (128, 128, 255)
		reserved_colour = (0, 0, 255)
		unknown_colour = (255, 0, 0)
		renderer = self.session.view.renderer['InstanceRenderer']

		for coords, (purpose, _) in self.plan.iteritems():
			tile = self.island.ground_map[coords]
			if purpose == self.purpose.main_square:
				renderer.addColored(tile._instance, *sq_colour)
			elif purpose == self.purpose.tent:
				renderer.addColored(tile._instance, *tent_colour)
			elif purpose == self.purpose.planned_tent:
				renderer.addColored(tile._instance, *planned_tent_colour)
			elif purpose == self.purpose.road:
				renderer.addColored(tile._instance, *road_colour)
			elif purpose == self.purpose.village_school:
				renderer.addColored(tile._instance, *village_school_colour)
			elif purpose == self.purpose.pavilion:
				renderer.addColored(tile._instance, *pavilion_colour)
			elif purpose == self.purpose.reserved:
				renderer.addColored(tile._instance, *reserved_colour)
			else:
				renderer.addColored(tile._instance, *unknown_colour)

decorators.bind_all(VillageBuilder)
