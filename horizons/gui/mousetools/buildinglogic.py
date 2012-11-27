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

class ShipBuildingToolLogic(object):
	"""Helper class to seperate the logic needed when building from a ship from
	the main building tool."""

	def __init__(self, ship):
		self.ship = ship

	def highlight_buildable(self, building_tool, tiles_to_check=None):
		"""Highlights all buildable tiles.
		@param tiles_to_check: list of tiles to check for coloring."""
		# resolved variables from inner loops
		is_tile_buildable = building_tool._class.is_tile_buildable
		session = building_tool.session
		player = session.world.player
		buildable_tiles_add = building_tool._buildable_tiles.add

		if tiles_to_check is not None: # only check these tiles
			for tile in tiles_to_check:
				if is_tile_buildable(session, tile, self.ship):
					building_tool._color_buildable_tile(tile)
		else: # build from ship
			building_tool.renderer.removeAllColored()
			for island in session.world.get_islands_in_radius(self.ship.position, self.ship.radius):
				for tile in island.get_surrounding_tiles(self.ship.position, self.ship.radius):
					if is_tile_buildable(session, tile, self.ship):
						buildable_tiles_add(tile)
						# check that there is no other player's settlement
						if tile.settlement is None or tile.settlement.owner == player:
							building_tool._color_buildable_tile(tile)

	def on_escape(self, session):
		for selected in session.selected_instances:
			selected.get_component(SelectableComponent).deselect()
		session.selected_instances = set([self.ship])
		self.ship.get_component(SelectableComponent).select()
		self.ship.get_component(SelectableComponent).show_menu()

	def remove(self, session):
		self.on_escape(session)

	def add_change_listener(self, instance, building_tool):
		# instance is self.ship here
		instance.add_change_listener(building_tool.highlight_buildable)
		instance.add_change_listener(building_tool.force_update)

	def remove_change_listener(self, instance, building_tool):
		# be idempotent
		if instance.has_change_listener(building_tool.highlight_buildable):
			instance.remove_change_listener(building_tool.highlight_buildable)
		if instance.has_change_listener(building_tool.force_update):
			instance.remove_change_listener(building_tool.force_update)


	def continue_build(self): pass

class SettlementBuildingToolLogic(object):
	"""Helper class to seperate the logic needen when building from a settlement
	from the main building tool"""

	def __init__(self, building_tool):
		self.building_tool = weakref.ref(building_tool)
		self.subscribed = False

	def highlight_buildable(self, building_tool, tiles_to_check=None):
		"""Highlights all buildable tiles.
		@param tiles_to_check: list of tiles to check for coloring."""

		# resolved variables from inner loops
		is_tile_buildable = building_tool._class.is_tile_buildable
		session = building_tool.session
		player = session.world.player

		if not self.subscribed:
			self.subscribed = True
			SettlementRangeChanged.subscribe(self._on_update)

		if tiles_to_check is not None: # only check these tiles
			for tile in tiles_to_check:
				if is_tile_buildable(session, tile, None):
					building_tool._color_buildable_tile(tile)

		else: #default build on island
			for settlement in session.world.settlements:
				if settlement.owner == player:
					island = session.world.get_island(Point(*settlement.ground_map.iterkeys().next()))
					for tile in settlement.ground_map.itervalues():
						if is_tile_buildable(session, tile, None, island, check_settlement=False):
							building_tool._color_buildable_tile(tile)

class BuildRelatedBuildingToolLogic(SettlementBuildingToolLogic):
	"""Same as normal build, except quitting it drops to the build related tab."""
	def __init__(self, building_tool, instance):
		super(BuildRelatedBuildingToolLogic, self).__init__(building_tool)
		# instance must be weakref
		self.instance = instance

	def _reshow_tab(self):
		from horizons.gui.tabs import BuildRelatedTab
		self.instance().get_component(SelectableComponent).show_menu(jump_to_tabclass=BuildRelatedTab)

	def on_escape(self, session):
		super(BuildRelatedBuildingToolLogic, self).on_escape(session)
		self._reshow_tab()

	def continue_build(self):
		self._reshow_tab()

	def add_change_listener(self, instance, building_tool): pass # using messages now
	def remove_change_listener(self, instance, building_tool): pass
	def remove(self, session):
		super(BuildRelatedBuildingToolLogic, self).remove(session)