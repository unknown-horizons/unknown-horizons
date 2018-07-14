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

import copy
import logging
import math
from collections import defaultdict, deque

from horizons.ai.aiplayer.areabuilder import AreaBuilder
from horizons.ai.aiplayer.basicbuilder import BasicBuilder
from horizons.ai.aiplayer.constants import BUILD_RESULT, BUILDING_PURPOSE
from horizons.constants import AI, BUILDINGS
from horizons.entities import Entities
from horizons.util.shapes import Rect, distances


class VillageBuilder(AreaBuilder):
	"""
	An object of this class manages the village area of a settlement.

	Important attributes:
	* plan: a dictionary of the form {(x, y): (purpose, (section, seq_no)), ...} where
		purpose is one of the BUILDING_PURPOSE constants, section is the sequence number
		of the village section and seq_no is the sequence number of a residence or None
		if it is another type of building. The plan is created in the beginning and
		changed only when land is lost.
	* special_building_assignments: {BUILDING_PURPOSE constant: {village producer coordinates: [residence coordinates, ...]}}
	* tent_queue: deque([(x, y), ...]) of remaining residence spots in the right order
	* num_sections: number of sections in the area
	* current_section: 1-based number of the section that is being filled with residences
	* roads_built: boolean showing whether all planned roads in the area have been built
	"""

	log = logging.getLogger("ai.aiplayer")

	def __init__(self, settlement_manager):
		super().__init__(settlement_manager)
		self.__init(settlement_manager)
		if not self.land_manager.feeder_island:
			self._create_plan()

	def __init(self, settlement_manager):
		self.land_manager = settlement_manager.land_manager
		self.tent_queue = deque()
		self._init_cache()
		self.roads_built = False
		self.personality = self.owner.personality_manager.get('VillageBuilder')

		if self.land_manager.feeder_island:
			self.num_sections = 0
			self.current_section = 0

	def save(self, db):
		super().save(db)
		db("INSERT INTO ai_village_builder(rowid, settlement_manager, num_sections, current_section) VALUES(?, ?, ?, ?)",
			self.worldid, self.settlement_manager.worldid, self.num_sections, self.current_section)

		db_query = 'INSERT INTO ai_village_builder_plan(village_builder, x, y, purpose, section, seq_no) VALUES(?, ?, ?, ?, ?, ?)'
		for (x, y), (purpose, (section, seq_no)) in self.plan.items():
			db(db_query, self.worldid, x, y, purpose, section, seq_no)

	def _load(self, db, settlement_manager):
		db_result = db("SELECT rowid, num_sections, current_section FROM ai_village_builder WHERE settlement_manager = ?", settlement_manager.worldid)
		worldid, self.num_sections, self.current_section = db_result[0]
		super()._load(db, settlement_manager, worldid)
		self.__init(settlement_manager)

		db_result = db("SELECT x, y, purpose, section, seq_no FROM ai_village_builder_plan WHERE village_builder = ?", worldid)
		for x, y, purpose, section, seq_no in db_result:
			self.plan[(x, y)] = (purpose, (section, seq_no))
			if purpose == BUILDING_PURPOSE.ROAD:
				self.land_manager.roads.add((x, y))

		self._recreate_tent_queue()
		self._create_special_village_building_assignments()

	def _get_village_section_coordinates(self, start_x, start_y, width, height):
		"""Return set([(x, y), ...]) of usable coordinates in the rectangle defined by the parameters."""
		warehouse_coords_set = set(self.land_manager.settlement.warehouse.position.tuple_iter())
		result = set()
		for dx in range(width):
			for dy in range(height):
				coords = (start_x + dx, start_y + dy)
				if coords in self.land_manager.village and self.land_manager.coords_usable(coords) and coords not in warehouse_coords_set:
					result.add(coords)
		return result

	def _create_plan(self):
		"""
		Create the area plan.

		The algorithm:
		* find a way to cut the village area into rectangular section_plans
		* each section gets a plan with a main square, roads, and residence locations
		* the plan is stitched together and other village buildings are by replacing some
			of the residences
		"""
		# Sets of coordinates used for calulate the width and height
		xs = {x for (x, _) in self.land_manager.village}
		ys = {y for (_, y) in self.land_manager.village}

		width = max(xs) - min(xs) + 1
		height = max(ys) - min(ys) + 1
		horizontal_sections = int(math.ceil(float(width) / self.personality.max_village_section_size))
		vertical_sections = int(math.ceil(float(height) / self.personality.max_village_section_size))

		section_plans = [] # [{(x, y): BUILDING_PURPOSE constant, ...}, ...]
		vertical_roads = set() # set([x, ...])
		horizontal_roads = set() # set([y, ...])

		# partition with roads between the sections
		start_y = min(ys)
		section_width = width // horizontal_sections
		section_height = height // vertical_sections
		section_coords_set_list = []
		for i in range(vertical_sections):
			bottom_road = i + 1 < vertical_sections
			max_y = min(max(ys), start_y + section_height)
			current_height = max_y - start_y + 1
			start_x = min(xs)

			for j in range(horizontal_sections):
				right_road = j + 1 < horizontal_sections
				max_x = min(max(xs), start_x + section_width)
				current_width = max_x - start_x + 1
				section_coords_set_list.append(self._get_village_section_coordinates(start_x, start_y, current_width - right_road, current_height - bottom_road))
				start_x += current_width
				if i == 0 and right_road:
					vertical_roads.add(start_x - 1)

			start_y += current_height
			if bottom_road:
				horizontal_roads.add(start_y - 1)

		for section_coords_set in section_coords_set_list:
			section_plan = self._create_section_plan(section_coords_set, vertical_roads, horizontal_roads)
			section_plans.append(section_plan[1])

		self._stitch_sections_together(section_plans, vertical_roads, horizontal_roads)
		self._return_unused_space()

	def _stitch_sections_together(self, section_plans, vertical_roads, horizontal_roads):
		"""
		Complete creating the plan by stitching the sections together and creating the tent queue.

		@param section_plans: list of section plans in the format [{(x, y): BUILDING_PURPOSE constant, ...}, ...]
		@param vertical_roads: vertical roads between the sections in the form set([x, ...])
		@param horizontal_roads: horizontal roads between the sections in the form set([y, ...])
		"""

		self.plan = {}
		ys = set(list(zip(*self.land_manager.village.keys()))[1])
		for road_x in vertical_roads:
			for road_y in ys:
				coords = (road_x, road_y)
				if self.land_manager.coords_usable(coords):
					self.plan[coords] = (BUILDING_PURPOSE.ROAD, (0, None))

		xs = set(list(zip(*self.land_manager.village.keys()))[0])
		for road_y in horizontal_roads:
			for road_x in xs:
				coords = (road_x, road_y)
				if self.land_manager.coords_usable(coords):
					self.plan[coords] = (BUILDING_PURPOSE.ROAD, (0, None))

		for i, section_plan in enumerate(section_plans):
			self._optimize_section_plan(section_plan)
			tent_lookup = self._create_tent_queue(section_plan)
			for coords, purpose in section_plan.items():
				self.plan[coords] = (purpose, (i, tent_lookup[coords]))
		self.num_sections = len(section_plans)
		self.current_section = 0
		self._reserve_special_village_building_spots()
		self._recreate_tent_queue()

		# add potential roads to the island's network
		for coords, (purpose, _) in self.plan.items():
			if purpose == BUILDING_PURPOSE.ROAD:
				self.land_manager.roads.add(coords)

	@classmethod
	def _remove_unreachable_roads(cls, section_plan, main_square):
		"""
		Remove the roads that can't be reached by starting from the main square.

		@param section_plan: {(x, y): BUILDING_PURPOSE constant, ...}
		@param main_square: Rect representing the position of the main square
		"""

		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		reachable = set()
		queue = deque()
		for (x, y) in main_square.tuple_iter():
			for (dx, dy) in moves:
				coords = (x + dx, y + dy)
				if coords in section_plan and section_plan[coords] == BUILDING_PURPOSE.ROAD:
					queue.append(coords)
					reachable.add(coords)

		while queue:
			(x, y) = queue.popleft()
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords in section_plan and section_plan[coords] == BUILDING_PURPOSE.ROAD and coords not in reachable:
					reachable.add(coords)
					queue.append(coords)

		to_remove = []
		for coords, purpose in section_plan.items():
			if purpose == BUILDING_PURPOSE.ROAD and coords not in reachable:
				to_remove.append(coords)
		for coords in to_remove:
			section_plan[coords] = BUILDING_PURPOSE.NONE

	def _get_possible_building_positions(self, section_coords_set, size):
		"""Return {(x, y): Rect, ...} that contains every size x size potential building location where only the provided coordinates are legal."""
		result = {}
		for (x, y) in sorted(section_coords_set):
			ok = True
			for dx in range(size[0]):
				for dy in range(size[1]):
					coords = (x + dx, y + dy)
					if coords not in section_coords_set or not self.land_manager.coords_usable(coords):
						ok = False
						break
				if not ok:
					break
			if ok:
				result[(x, y)] = Rect.init_from_topleft_and_size_tuples((x, y), size)
		return result

	def _create_section_plan(self, section_coords_set, vertical_roads, horizontal_roads):
		"""
		Create the section plan that contains the main square, roads, and residence positions.

		The algorithm is as follows:
		* place the main square
		* form a road grid to support the tents
		* choose the best one by preferring the one with more residence locations and less
			unreachable / blocked / parallel side by side roads.

		@param section_plans: list of section plans in the format [{(x, y): BUILDING_PURPOSE constant, ...}, ...]
		@param vertical_roads: vertical roads between the sections in the form set([x, ...])
		@param horizontal_roads: horizontal roads between the sections in the form set([y, ...])
		@return: (number of residences in the plan, the plan in the form {(x, y): BUILDING_PURPOSE constant}
		"""

		best_plan = {}
		best_tents = 0
		best_value = -1
		tent_squares = [(0, 0), (0, 1), (1, 0), (1, 1)]
		road_connections = [(-1, 0), (-1, 1), (0, -1), (0, 2), (1, -1), (1, 2), (2, 0), (2, 1)]
		tent_radius_sq = Entities.buildings[BUILDINGS.RESIDENTIAL].radius ** 2

		xs = set(x for (x, _) in section_coords_set)
		for x in vertical_roads:
			if x - 1 in xs or x + 1 in xs:
				xs.add(x)
		xs = sorted(xs)

		ys = set(y for (_, y) in section_coords_set)
		for y in horizontal_roads:
			if y - 1 in ys or y + 1 in ys:
				ys.add(y)
		ys = sorted(ys)

		distance_rect_rect_sq = distances.distance_rect_rect_sq
		possible_road_positions = self._get_possible_building_positions(section_coords_set, (1, 1))
		possible_residence_positions = self._get_possible_building_positions(section_coords_set, Entities.buildings[BUILDINGS.RESIDENTIAL].size)
		possible_main_square_positions = self._get_possible_building_positions(section_coords_set, Entities.buildings[BUILDINGS.MAIN_SQUARE].size)

		for (x, y), main_square in sorted(possible_main_square_positions.items()):
			section_plan = dict.fromkeys(section_coords_set, BUILDING_PURPOSE.NONE)
			bad_roads = 0
			good_tents = 0
			double_roads = 0

			# place the main square
			for coords in main_square.tuple_iter():
				section_plan[coords] = BUILDING_PURPOSE.RESERVED
			section_plan[(x, y)] = BUILDING_PURPOSE.MAIN_SQUARE

			# place the roads running parallel to the y-axis
			last_road_y = None
			for road_y in ys:
				if road_y not in horizontal_roads:
					if road_y < y:
						if (y - road_y) % 5 != 1:
							continue
					else:
						if road_y < y + 6 or (road_y - y) % 5 != 1:
							continue

				if last_road_y == road_y - 1:
					double_roads += 1
				last_road_y = road_y

				for road_x in xs:
					if road_x not in vertical_roads:
						coords = (road_x, road_y)
						if coords in possible_road_positions:
							section_plan[coords] = BUILDING_PURPOSE.ROAD
						else:
							bad_roads += 1

			# place the roads running parallel to the x-axis
			last_road_x = None
			for road_x in xs:
				if road_x not in vertical_roads:
					if road_x < x:
						if (x - road_x) % 5 != 1:
							continue
					else:
						if road_x < x + 6 or (road_x - x) % 5 != 1:
							continue

				if last_road_x == road_x - 1:
					double_roads += 1
				last_road_x = road_x

				for road_y in ys:
					if road_y not in horizontal_roads:
						coords = (road_x, road_y)
						if coords in possible_road_positions:
							section_plan[coords] = BUILDING_PURPOSE.ROAD
						else:
							bad_roads += 1

			if bad_roads > 0:
				self._remove_unreachable_roads(section_plan, main_square)

			# place the tents
			for coords, position in sorted(possible_residence_positions.items()):
				ok = True
				for dx, dy in tent_squares:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if section_plan[coords2] != BUILDING_PURPOSE.NONE:
						ok = False
						break
				if not ok:
					continue
				if distance_rect_rect_sq(main_square, position) > tent_radius_sq:
					continue # unable to build or out of main square range

				# is there a road connection?
				ok = False
				for dx, dy in road_connections:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 in section_plan and section_plan[coords2] == BUILDING_PURPOSE.ROAD:
						ok = True
						break

				# connection to a road tile exists, build the tent
				if ok:
					for dx, dy in tent_squares:
						section_plan[(coords[0] + dx, coords[1] + dy)] = BUILDING_PURPOSE.RESERVED
					section_plan[coords] = BUILDING_PURPOSE.RESIDENCE
					good_tents += 1

			value = self.personality.tent_value * good_tents - self.personality.bad_road_penalty * bad_roads - self.personality.double_road_penalty * double_roads
			if best_value < value:
				best_plan = section_plan
				best_tents = good_tents
				best_value = value
		return (best_tents, best_plan)

	def _optimize_section_plan(self, section_plan):
		"""Try to fit more residences into the grid."""
		# calculate distance from the main square to every tile
		road_connections = [(-1, 0), (-1, 1), (0, -1), (0, 2), (1, -1), (1, 2), (2, 0), (2, 1)]
		tent_squares = [(0, 0), (0, 1), (1, 0), (1, 1)]
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		distance = {}
		queue = deque()

		for coords, purpose in sorted(section_plan.items()):
			if purpose == BUILDING_PURPOSE.MAIN_SQUARE:
				for coords in self._get_position(coords, BUILDINGS.MAIN_SQUARE).tuple_iter():
					distance[coords] = 0
					queue.append(coords)

		while queue:
			(x, y) = queue.popleft()
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords in section_plan and coords not in distance:
					distance[coords] = distance[(x, y)] + 1
					queue.append(coords)

		# remove planned tents from the section plan
		for (x, y) in section_plan:
			coords = (x, y)
			if section_plan[coords] == BUILDING_PURPOSE.RESIDENCE:
				for dx, dy in tent_squares:
					section_plan[(x + dx, y + dy)] = BUILDING_PURPOSE.NONE

		# create new possible tent position list
		possible_tents = []
		for coords in sorted(section_plan):
			if coords in distance and section_plan[coords] == BUILDING_PURPOSE.NONE:
				possible_tents.append((distance[coords], coords))
		possible_tents.sort()

		# place the tents
		for _, (x, y) in possible_tents:
			ok = True
			for dx, dy in tent_squares:
				coords = (x + dx, y + dy)
				if coords not in section_plan or section_plan[coords] != BUILDING_PURPOSE.NONE:
					ok = False
					break
			if not ok:
				continue

			# is there a road connection?
			ok = False
			for dx, dy in road_connections:
				coords = (x + dx, y + dy)
				if coords in section_plan and section_plan[coords] == BUILDING_PURPOSE.ROAD:
					ok = True
					break

			# connection to a road tile exists, build the tent
			if ok:
				for dx, dy in tent_squares:
					section_plan[(x + dx, y + dy)] = BUILDING_PURPOSE.RESERVED
				section_plan[(x, y)] = BUILDING_PURPOSE.RESIDENCE

	def _return_unused_space(self):
		"""Return the area that remains unused after creating the plan."""
		not_needed = []
		for coords in self.land_manager.village:
			if coords not in self.plan or self.plan[coords][0] == BUILDING_PURPOSE.NONE:
				not_needed.append(coords)
		for coords in not_needed:
			# if the warehouse is (partly) in the village area then it needs to be handed over but it won't be in the plan at all
			if coords in self.plan:
				del self.plan[coords]
			self.land_manager.add_to_production(coords)

	@classmethod
	def _get_position(cls, coords, building_id):
		"""Return the position Rect of a building of the given type at the given position."""
		return Rect.init_from_topleft_and_size_tuples(coords, Entities.buildings[building_id].size)

	def _get_sorted_building_positions(self, building_purpose):
		"""Return a list of sorted building positions in the form [Rect, ...]."""
		building_id = BUILDING_PURPOSE.purpose_to_building[building_purpose]
		return sorted(self._get_position(coords, building_id) for coords, (purpose, _) in self.plan.items() if purpose == building_purpose)

	def _replace_planned_residence(self, new_purpose, max_buildings, capacity):
		"""
		Replace up to max_buildings residence spots with buildings of purpose new_purpose.

		This function is used to amend the existing plan with village producers such as
		pavilions, schools, and taverns. The goal is to place as few of them as needed
		while still covering the maximum number of residences.

		@param new_purpose: the BUILDING_PURPOSE constant of the new buildings
		@param max_buildings: maximum number of residences to replace
		@param capacity: maximum number of residences one of the new buildings can service
		"""

		distance_rect_rect_sq = distances.distance_rect_rect_sq
		distance_rect_tuple = distances.distance_rect_tuple
		tent_range_sq = Entities.buildings[BUILDINGS.RESIDENTIAL].radius ** 2
		planned_tents = self._get_sorted_building_positions(BUILDING_PURPOSE.RESIDENCE)

		possible_positions = copy.copy(planned_tents)
		if new_purpose == BUILDING_PURPOSE.TAVERN:
			# filter out the positions that are too far from the main squares and the warehouse
			tavern_radius_sq = Entities.buildings[BUILDINGS.TAVERN].radius ** 2
			storage_positions = self._get_sorted_building_positions(BUILDING_PURPOSE.MAIN_SQUARE)
			storage_positions.append(self.settlement_manager.settlement.warehouse.position)
			possible_positions = [rect for rect in possible_positions if any(distance_rect_rect_sq(rect, storage_rect) <= tavern_radius_sq for storage_rect in storage_positions)]

		num_kept = int(min(len(possible_positions), max(self.personality.min_coverage_building_options, len(possible_positions) * self.personality.coverage_building_option_ratio)))
		possible_positions = self.session.random.sample(possible_positions, num_kept)

		def get_centroid(planned, blocked):
			total_x, total_y = 0, 0
			for position in planned_tents:
				if position not in blocked:
					total_x += position.left
					total_y += position.top
			mid_x = total_x / float(len(planned) - len(blocked))
			mid_y = total_y / float(len(planned) - len(blocked))
			return (mid_x, mid_y)

		def get_centroid_distance_pairs(planned, blocked):
			centroid = get_centroid(planned_tents, blocked)
			positions = []
			for position in planned_tents:
				if position not in blocked:
					positions.append((distance_rect_tuple(position, centroid), position))
			positions.sort(reverse=True)
			return positions

		for _ in range(max_buildings):
			if len(planned_tents) <= 1:
				break
			best_score = None
			best_pos = None

			for replaced_pos in possible_positions:
				positions = get_centroid_distance_pairs(planned_tents, set([replaced_pos]))
				score = 0
				in_range = 0
				for distance_to_centroid, position in positions:
					if in_range < capacity and distance_rect_rect_sq(replaced_pos, position) <= tent_range_sq:
						in_range += 1
					else:
						score += distance_to_centroid
				if best_score is None or best_score > score:
					best_score = score
					best_pos = replaced_pos

			in_range = 0
			positions = list(zip(*get_centroid_distance_pairs(planned_tents, set([best_pos]))))[1]
			for position in positions:
				if in_range < capacity and distance_rect_rect_sq(best_pos, position) <= tent_range_sq:
					planned_tents.remove(position)
					in_range += 1
			if not in_range:
				continue

			possible_positions.remove(best_pos)
			coords = best_pos.origin.to_tuple()
			self.register_change_list([coords], new_purpose, (self.plan[coords][1][0], None))

	def _reserve_special_village_building_spots(self):
		"""Replace residence spots with special village buildings such as pavilions, schools, taverns, doctors and fire stations."""
		num_other_buildings = 0 # the maximum number of each village producer that should be placed
		residences = len(self.tent_queue)
		while residences > 0:
			num_other_buildings += 3
			residences -= 3 + self.personality.normal_coverage_building_capacity

		self._replace_planned_residence(BUILDING_PURPOSE.PAVILION, num_other_buildings, self.personality.max_coverage_building_capacity)
		self._replace_planned_residence(BUILDING_PURPOSE.VILLAGE_SCHOOL, num_other_buildings, self.personality.max_coverage_building_capacity)
		self._replace_planned_residence(BUILDING_PURPOSE.TAVERN, num_other_buildings, self.personality.max_coverage_building_capacity)

		num_fire_stations = max(0, int(round(0.5 + (len(self.tent_queue) - 3 * num_other_buildings) // self.personality.normal_fire_station_capacity)))
		self._replace_planned_residence(BUILDING_PURPOSE.FIRE_STATION, num_fire_stations, self.personality.max_fire_station_capacity)

		num_doctors = max(0, int(round(0.5 + (len(self.tent_queue) - 3 * num_other_buildings) // self.personality.normal_doctor_capacity)))
		self._replace_planned_residence(BUILDING_PURPOSE.DOCTOR, num_doctors, self.personality.max_doctor_capacity)

		self._create_special_village_building_assignments()

	def _create_special_village_building_assignments(self):
		"""
		Create an assignment of residence spots to special village building spots.

		This is useful for deciding which of the special village buildings would be most useful.
		"""

		distance_rect_rect = distances.distance_rect_rect
		self.special_building_assignments = {} # {BUILDING_PURPOSE constant: {village producer coordinates: [residence coordinates, ...]}}
		residence_positions = self._get_sorted_building_positions(BUILDING_PURPOSE.RESIDENCE)

		building_types = []
		for purpose in [BUILDING_PURPOSE.PAVILION, BUILDING_PURPOSE.VILLAGE_SCHOOL, BUILDING_PURPOSE.TAVERN]:
			building_types.append((purpose, Entities.buildings[BUILDINGS.RESIDENTIAL].radius, self.personality.max_coverage_building_capacity))
		building_types.append((BUILDING_PURPOSE.FIRE_STATION, Entities.buildings[BUILDINGS.FIRE_STATION].radius, self.personality.max_fire_station_capacity))
		building_types.append((BUILDING_PURPOSE.DOCTOR, Entities.buildings[BUILDINGS.DOCTOR].radius, self.personality.max_doctor_capacity))

		for purpose, range, max_capacity in building_types:
			producer_positions = sorted(self._get_position(coords, BUILDING_PURPOSE.get_building(purpose)) for coords, (pos_purpose, _) in self.plan.items() if pos_purpose == purpose)
			self.special_building_assignments[purpose] = {}
			for producer_position in producer_positions:
				self.special_building_assignments[purpose][producer_position.origin.to_tuple()] = []

			options = []
			for producer_position in producer_positions:
				for position in residence_positions:
					distance = distance_rect_rect(producer_position, position)
					if distance <= range:
						options.append((distance, producer_position.origin.to_tuple(), position.origin.to_tuple()))
			options.sort(reverse=True)

			assigned_residence_coords = set()
			for _, producer_coords, residence_coords in options:
				if residence_coords in assigned_residence_coords:
					continue
				if len(self.special_building_assignments[purpose][producer_coords]) >= max_capacity:
					continue
				assigned_residence_coords.add(residence_coords)
				self.special_building_assignments[purpose][producer_coords].append(residence_coords)

	def _create_tent_queue(self, section_plan):
		"""
		Place the residences of a section in a visually appealing order; save the result in the tent queue.

		The algorithm:
		* split the residences of the section into blocks where a block is formed of all
			residence spots that share sides
		* calculate the distance from the main square to the block
		* form the final sequence by sorting the blocks by distance to the main square and
			by sorting the residences of a block by their coordinates

		@return: {(x, y): residence sequence number}
		"""
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		blocks = []
		block = {}

		# form blocks of tents
		main_square = None
		for coords, purpose in sorted(section_plan.items()):
			if purpose == BUILDING_PURPOSE.MAIN_SQUARE:
				main_square = self._get_position(coords, BUILDINGS.MAIN_SQUARE)
			if purpose != BUILDING_PURPOSE.RESIDENCE or coords in block:
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
					if coords not in section_plan or coords in explored:
						continue
					if section_plan[coords] == BUILDING_PURPOSE.RESIDENCE or section_plan[coords] == BUILDING_PURPOSE.RESERVED:
						explored.add(coords)
						queue.append(coords)
						if section_plan[coords] == BUILDING_PURPOSE.RESIDENCE:
							block[coords] = len(blocks)
							block_list.append(coords)
			blocks.append(block_list)

		# calculate distance from the main square to the block
		distance_rect_tuple = distances.distance_rect_tuple
		block_distances = []
		for coords_list in blocks:
			distance = 0
			for coords in coords_list:
				distance += distance_rect_tuple(main_square, coords)
			block_distances.append((distance / len(coords_list), coords_list))

		# form the sorted tent queue
		result = defaultdict(lambda: None)
		if block_distances:
			for block in list(zip(*sorted(block_distances)))[1]:
				for coords in sorted(block):
					result[coords] = len(self.tent_queue)
					self.tent_queue.append(coords)
		return result

	def _recreate_tent_queue(self, removal_location=None):
		"""Recreate the tent queue making sure that the possibly removed location is missing."""
		queue = []
		for coords, (purpose, (_, seq_no)) in self.plan.items():
			if purpose == BUILDING_PURPOSE.RESIDENCE:
				object = self.island.ground_map[coords].object
				if object is None or object.id != BUILDINGS.RESIDENTIAL or removal_location == coords:
					queue.append((seq_no, coords))
		if queue:
			self.tent_queue = deque(list(zip(*sorted(queue)))[1])
		else:
			self.tent_queue = deque()

	def build_roads(self):
		"""Try to build all roads in the village area, record the result in the field roads_built."""
		all_built = True
		for coords, (purpose, (section, _)) in sorted(self.plan.items()):
			if section > self.current_section or coords not in self.settlement.ground_map:
				all_built = False
				continue
			if purpose != BUILDING_PURPOSE.ROAD:
				continue
			object = self.settlement.ground_map[coords].object
			if object is not None and not object.buildable_upon:
				continue
			if not self.have_resources(BUILDINGS.TRAIL):
				all_built = False
				break
			assert BasicBuilder(BUILDINGS.TRAIL, coords, 0).execute(self.land_manager)
		self.roads_built = all_built

	def build_tent(self, coords=None):
		"""Build the next tent (or the specified one if coords is not None)."""
		if not self.tent_queue:
			return BUILD_RESULT.IMPOSSIBLE

		# can_trigger_next_section is used to start building the next section when the old one is done
		# if a tent is built just to extend the area then that can't trigger the next section
		# TODO: handle extension tents nicer than just letting them die
		can_trigger_next_section = False
		if coords is None:
			coords = self.tent_queue[0]
			can_trigger_next_section = True

		ok = True
		x, y = coords
		owned_by_other = False
		size = Entities.buildings[BUILDINGS.RESIDENTIAL].size
		for dx in range(size[0]):
			for dy in range(size[1]):
				coords2 = (x + dx, y + dy)
				if coords2 not in self.settlement.ground_map:
					ok = False
					if self.island.ground_map[coords2].settlement is not None:
						owned_by_other = True

		if ok and not owned_by_other:
			if not self.have_resources(BUILDINGS.RESIDENTIAL):
				return BUILD_RESULT.NEED_RESOURCES
			assert BasicBuilder(BUILDINGS.RESIDENTIAL, (x, y), 0).execute(self.land_manager)

		if ok or owned_by_other:
			if self.tent_queue[0] == coords:
				self.tent_queue.popleft()
			else:
				for i in range(len(self.tent_queue)):
					if self.tent_queue[i] == coords:
						del self.tent_queue[i]
						break
			if owned_by_other:
				self.log.debug('%s tent position owned by other player at (%d, %d)', self, x, y)
				return BUILD_RESULT.IMPOSSIBLE

		if not ok:
			# need to extends the area, it is not owned by another player
			self.log.debug('%s tent position not owned by the player at (%d, %d), extending settlement area instead', self, x, y)
			return self.extend_settlement(Rect.init_from_topleft_and_size(x, y, size[0], size[1]))

		if not self.roads_built:
			self.build_roads()
		if can_trigger_next_section and self.plan[coords][1][0] > self.current_section:
			self.current_section = self.plan[coords][1][0]
		return BUILD_RESULT.OK

	def handle_lost_area(self, coords_list):
		"""
		Handle losing the potential land in the given coordinates list.

		Take the following actions:
		* remove the lost area from the village and road areas
		* remove village sections with impossible main squares
		* remove all planned buildings that are now impossible
		* TODO: if the village area takes too much of the total area then remove / reduce the remaining sections
		"""

		# remove village sections with impossible main squares
		removed_sections = set()
		for coords, (purpose, (section, _)) in self.plan.items():
			if purpose != BUILDING_PURPOSE.MAIN_SQUARE:
				continue
			possible = True
			for main_square_coords in self._get_position(coords, BUILDINGS.MAIN_SQUARE).tuple_iter():
				if main_square_coords not in self.land_manager.village:
					possible = False
					break
			if not possible:
				# impossible to build the main square because a part of the area is owned by another player: remove the whole section
				removed_sections.add(section)

		removed_coords_list = []
		for coords, (purpose, (section, _)) in self.plan.items():
			if purpose in [BUILDING_PURPOSE.RESERVED, BUILDING_PURPOSE.NONE]:
				continue
			position = self._get_position(coords, BUILDING_PURPOSE.get_building(purpose))
			building = self.settlement.ground_map[coords].object if coords in self.settlement.ground_map else None

			if section in removed_sections:
				if purpose == BUILDING_PURPOSE.ROAD:
					if building is None or building.id != BUILDINGS.TRAIL:
						removed_coords_list.append(coords)
					continue # leave existing roads behind
				elif building is not None and not building.buildable_upon:
					# TODO: remove the actual building
					pass

				for building_coords in position.tuple_iter():
					removed_coords_list.append(building_coords)
			else:
				# remove the planned village buildings that are no longer possible
				if purpose == BUILDING_PURPOSE.ROAD:
					if coords not in self.land_manager.village:
						removed_coords_list.append(coords)
					continue

				possible = True
				for building_coords in position.tuple_iter():
					if building_coords not in self.land_manager.village:
						possible = False
				if possible:
					continue

				for building_coords in position.tuple_iter():
					removed_coords_list.append(building_coords)

		for coords in removed_coords_list:
			del self.plan[coords]
		self._recreate_tent_queue()
		# TODO: renumber the sections
		# TODO: create a new plan with village producers
		self._return_unused_space()
		self._create_special_village_building_assignments()
		super().handle_lost_area(coords_list)

	def remove_building(self, building):
		"""Called when a building is removed from the area (the building still exists during the call)."""
		if building.id == BUILDINGS.RESIDENTIAL:
			self._recreate_tent_queue(building.position.origin.to_tuple())

		super().remove_building(building)

	def display(self):
		"""Show the plan on the map unless it is disabled in the settings."""
		if not AI.HIGHLIGHT_PLANS:
			return

		unknown_color = (255, 0, 0)
		renderer = self.session.view.renderer['InstanceRenderer']

		tile_colors = {
			BUILDING_PURPOSE.MAIN_SQUARE: (255, 0, 255),
			BUILDING_PURPOSE.RESIDENCE: (255, 255, 255),
			BUILDING_PURPOSE.ROAD: (30, 30, 30),
			BUILDING_PURPOSE.VILLAGE_SCHOOL: (128, 128, 255),
			BUILDING_PURPOSE.PAVILION: (255, 128, 128),
			BUILDING_PURPOSE.TAVERN: (255, 255, 0),
			BUILDING_PURPOSE.FIRE_STATION: (255, 64, 64),
			BUILDING_PURPOSE.DOCTOR: (255, 128, 64),
			BUILDING_PURPOSE.RESERVED: (0, 0, 255),
		}
		for coords, (purpose, _) in self.plan.items():
			tile = self.island.ground_map[coords]
			color = tile_colors.get(purpose, unknown_color)
			renderer.addColored(tile._instance, *color)

	def __str__(self):
		return '{} VillageBuilder({})'.format(
			self.settlement_manager,
			self.worldid if hasattr(self, 'worldid') else 'none')
