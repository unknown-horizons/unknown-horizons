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

class DefaultPersonality:
	class AIPlayer:
		little_money = 3000 # cutoff to decide that we really need to get more money by selling resources on other players' islands
		buy_coefficient_rich = 30 # value coefficient of buying resources when we have more than little_money gold
		buy_coefficient_poor = 10 # value coefficient of buying resources when we have less than or equal to little_money gold

		min_feeder_island_area = 400 # minimum amount of usable free land on an island to consider turning it into a feeder island
		feeder_island_requirement_cutoff = 30 # if there are less than this many free 3x3 squares in a settlement then a feeder island is needed

		# found a settlement on a random island that is at least as large as the first element; if it is impossible then try the next size
		island_size_sequence = [500, 300, 150]

		# minimum amount of a resource required to found a new settlement
		min_new_island_gold = 8000
		min_new_island_tools = 5
		min_new_island_boards = 17
		min_new_island_food = 10

		# maximum amount of a resource loaded on a ship to found a new settlement
		max_new_island_tools = 30
		max_new_island_boards = 30
		max_new_island_food = 30

		# minimum amount of a resource required to start a new feeder island
		min_new_feeder_island_gold = 4000
		min_new_feeder_island_tools = 10
		min_new_feeder_island_boards = 20

		# maximum amount of a resource loaded on a ship to start a new feeder island
		max_new_feeder_island_tools = 30
		max_new_feeder_island_boards = 30

	class AreaBuilder:
		path_road_penalty_threshold = 9
		path_distant_road_penalty = 0.5
		path_near_road_constant_penalty = 0.7
		path_near_road_linear_penalty = 0.15
		path_unreachable_road_penalty = 0.1

		path_boundary_penalty_threshold = 10
		path_near_boundary_constant_penalty = 0.3
		path_near_boundary_linear_penalty = 0.03
		path_unreachable_boundary_penalty = 0.1

	class ProductionBuilder(AreaBuilder):
		expected_collector_capacity = 0.07 # resource collected per collector per tick
		collector_coverage_alignment_coefficient = 0.001 # the importance of alignment when choosing a location for a storage to improve collector coverage
		collector_extra_distance = 5 # constant distance on top of the actual distance a collector has to move (accounts for breaks)

		collector_area_enlargement_alignment_coefficient = 3 # the importance of alignment when choosing a location for a storage to enlarge collector coverage
		max_interesting_collector_area = 100 # maximum collector area (of 3x3 squares) we are interested in when considering whether to enlarge the area
		max_collector_area_unreachable = 10 # maximum collector area (of 3x3 squares) that doesn't have to be reachable when considering whether to enlarge the area

		deposit_coverage_alignment_coefficient = 0.7 # the importance of alignment when choosing a location for a storage to get closer to a deposit

	class VillageBuilder(AreaBuilder):
		max_village_section_size = 22 # maximum side length of a village section

		tent_value = 10 # the value of a tent in a village
		bad_road_penalty = 1 # the penalty for an impossible road tile
		double_road_penalty = 30 # the penalty for building two roads right next to each other (per complete road, not segment)

		max_coverage_building_capacity = 22 # maximum number of residences a coverage building can service
		normal_coverage_building_capacity = 20 # the initial plan calls for this number of residences per coverage building (may or may not be optimised away)

	class LandManager:
		max_section_side = 22 # minimise the number of village sections by considering this to be its maximum side length

		village_area_small = 0.28 # use this fraction of the area for the village if <= 1600 tiles are available for the settlement
		village_area_40 = 0.3 # use this fraction of the area for the village if <= 2500 tiles are available for the settlement
		village_area_50 = 0.32 # use this fraction of the area for the village if <= 3600 tiles are available for the settlement
		village_area_60 = 0.35 # use this fraction of the area for the village if > 3600 tiles are available for the settlement
		min_village_size = 81 # minimum possible village size in tiles
