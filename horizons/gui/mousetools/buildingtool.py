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

from fife import fife
import logging
import random
import weakref

import horizons.globals

from horizons.entities import Entities
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.shapes import Point
from horizons.util.worldobject import WorldObject
from horizons.command.building import Build
from horizons.component.selectablecomponent import SelectableBuildingComponent, SelectableComponent
from horizons.gui.mousetools.navigationtool import NavigationTool
from horizons.command.sounds import PlaySound
from horizons.gui.util import load_uh_widget
from horizons.constants import BUILDINGS, GFX
from horizons.extscheduler import ExtScheduler
from horizons.messaging import WorldObjectDeleted, SettlementInventoryUpdated, PlayerInventoryUpdated
from horizons.util.python import decorators
from buildinglogic import ShipBuildingToolLogic, SettlementBuildingToolLogic, BuildRelatedBuildingToolLogic
import buildgraphics

class BuildingTool(NavigationTool, buildgraphics.Graphics):
	"""Represents a dangling tool after a building was selected from the list.
	Builder visualizes if and why a building can not be built under the cursor position.
	@param building: selected building type"
	@param ship: If building from a ship, restrict to range of ship

	The building tool has been under heavy development for several years, it's a collection
	of random artifacts that used to have a purpose once.

	Terminology:
	- Related buildings: Buildings lower in the hiearchy, needed by current building to operate (tree when building lumberjack)
	- Inversely related building: lumberjack for tree. Need to show its range to place building, it must be in range.
	- Building instances/fife instances: the image of a building, that is dragged around.

	Main features:
	- Display tab to the right, showing build preview icon and rotation button (draw_gui(), load_gui())
	- Show buildable ground (highlight buildable) as well as ranges of inversely related buildings
		- This also is called for tiles that need to be recolored, other highlights sometimes draw over
		  tiles, then this is called again to redo the original coloring.
	- Catch mouse events and handle preview on map:
		- Get tentative fife instances for buildings, draw them colored according to buildability
		- Check for resources missing for build
		- Making surrounding of preview transparent, so you see where you are building in a forest
		- Highlight related buildings, that are in range
		- Draw building range and highlight related buildings that are in range in this position (_color_preview_building)
	- Initiate actual build (do_build)
		- Clean up coloring, possibly end build mode
	- Several buildability logics, strategy pattern via self._build_logic.

	Interaction sequence:
	- Init, comprises mainly of gui init and highlight_buildable
	- Update, which is mainly controlled by preview_build
		- Update highlights related to build
			- Transparency
			- Inversely related buildings in range (highlight_related_buildings)
			- Related buildings in range (_color_preview_build)
		- Set new instances
		- During this time, don't touch anything set by highlight_buildable, or restore it later
	- End, possibly do_build and on_escape
	"""
	
	#######################################################
	#log = logging.getLogger("gui.buildingtool")

	#buildable_color = (255, 255, 255)
	#not_buildable_color = (255, 0, 0)
	#related_building_color = (0, 192, 0)
	#related_building_outline = (16, 228, 16, 2)
	#nearby_objects_radius = 4

	# archive the last roads built, for possible user notification
	#_last_road_built = []

	#send_hover_instances_update = False

	#gui = None # share gui between instances
	
	#######################################################

	def __init__(self, session, building, ship=None, build_related=None):
		super(BuildingTool, self).__init__(session)
		assert not (ship and build_related)
		self.renderer = self.session.view.renderer['InstanceRenderer']
		self.ship = ship
		self._class = building
		self.__init_selectable_component()
		self.buildings = [] # list of PossibleBuild objs
		self.buildings_action_set_ids = [] # list action set ids of list above
		self.buildings_fife_instances = {} # fife instances of possible builds
		self.buildings_missing_resources = {} # missing resources for possible builds
		self.rotation = 45 + random.randint(0, 3)*90
		self.start_point, self.end_point = None, None
		self.last_change_listener = None
		self._transparencified_instances = set() # fife instances modified for transparency
		self._buildable_tiles = set() # tiles marked as buildable
		self._related_buildings = set() # buildings highlighted as related
		self._highlighted_buildings = set() # related buildings highlighted when preview is near it
		self._build_logic = None
		self._related_buildings_selected_tiles = frozenset() # highlights w.r.t. related buildings
		if self.ship is not None:
			self._build_logic = ShipBuildingToolLogic(ship)
		elif build_related is not None:
			self._build_logic = BuildRelatedBuildingToolLogic(self, weakref.ref(build_related) )
		else:
			self._build_logic = SettlementBuildingToolLogic(self)

		self.load_gui()
		self.__class__.gui.show()
		self.session.ingame_gui.minimap_to_front()

		self.session.gui.on_escape = self.on_escape

		self.highlight_buildable()
		WorldObjectDeleted.subscribe(self._on_worldobject_deleted)

		SettlementInventoryUpdated.subscribe(self.update_preview)
		PlayerInventoryUpdated.subscribe(self.update_preview)


	def __init_selectable_component(self):
		self.selectable_comp = SelectableBuildingComponent
		try:
			template = self._class.get_component_template(SelectableComponent)
			self.selectable_comp = SelectableComponent.get_instance(template)
		except KeyError:
			pass

	def remove(self):
		self.session.ingame_gui.resource_overview.close_construction_mode()
		WorldObjectDeleted.unsubscribe(self._on_worldobject_deleted)
		self._remove_listeners()
		self._remove_building_instances()
		self._remove_coloring()
		self._build_logic.remove(self.session)
		self._buildable_tiles = None
		self._transparencified_instances = None
		self._related_buildings_selected_tiles = None
		self._related_buildings = None
		self._highlighted_buildings = None
		self._build_logic = None
		self.buildings = None
		if self.__class__.gui is not None:
			self.__class__.gui.hide()
		ExtScheduler().rem_all_classinst_calls(self)
		SettlementInventoryUpdated.discard(self.update_preview)
		PlayerInventoryUpdated.discard(self.update_preview)
		super(BuildingTool, self).remove()

	def _on_worldobject_deleted(self, message):
		# remove references to this object
		self._related_buildings.discard(message.sender)
		self._transparencified_instances = \
		  set( i for i in self._transparencified_instances if
		       i() is not None and int(i().getId()) != message.worldid )
		check_building = lambda b : b.worldid != message.worldid
		self._highlighted_buildings = set( tup for tup in self._highlighted_buildings if check_building(tup[0]) )
		self._related_buildings = set( filter(check_building, self._related_buildings) )

	def load_gui(self):
		if self.__class__.gui is None:
			self.__class__.gui = load_uh_widget("place_building.xml")
			top_bar = self.__class__.gui.findChild(name='top_bar')
			top_bar.position = ((self.__class__.gui.size[0] // 2) - (top_bar.size[0] // 2) - 16, 50)
			self.__class__.gui.position_technique = "right-1:top+157"
		self.__class__.gui.mapEvents( { "rotate_left" : self.rotate_left,
		                                "rotate_right": self.rotate_right } )
		# set translated building name in gui
		self.__class__.gui.findChild(name='headline').text = _('Build {building}').format(building=_(self._class.name))
		self.__class__.gui.findChild(name='running_costs').text = unicode(self._class.running_costs)
		head_box = self.__class__.gui.findChild(name='head_box')
		head_box.adaptLayout() # recalculates size of new content
		# calculate and set new center
		new_x = max(25, (self.__class__.gui.size[0] // 2) - (head_box.size[0] // 2))
		head_box.position = (new_x, head_box.position[1])
		head_box.adaptLayout()
		self.draw_gui()

	def on_escape(self):
		self._build_logic.on_escape(self.session)
		if self.__class__.gui is not None:
			self.__class__.gui.hide()
		self.session.set_cursor() # will call remove()

	def mouseMoved(self, evt):
		self.log.debug("BuildingTool mouseMoved")
		super(BuildingTool, self).mouseMoved(evt)
		point = self.get_world_location(evt)
		if self.start_point != point:
			self.start_point = point
		self._check_update_preview(point)
		evt.consume()

	def mousePressed(self, evt):
		self.log.debug("BuildingTool mousePressed")
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mousePressed(evt)
			return
		if evt.getButton() == fife.MouseEvent.RIGHT:
			self.on_escape()
		elif evt.getButton() == fife.MouseEvent.LEFT:
			pass
		else:
			super(BuildingTool, self).mousePressed(evt)
			return
		evt.consume()

	def mouseDragged(self, evt):
		self.log.debug("BuildingTool mouseDragged")
		super(BuildingTool, self).mouseDragged(evt)
		point = self.get_world_location(evt)
		if self.start_point is not None:
			self._check_update_preview(point)
		evt.consume()

	def mouseReleased(self, evt):
		"""Actually build."""
		self.log.debug("BuildingTool mouseReleased")
		if evt.isConsumedByWidgets():
			super(BuildingTool, self).mouseReleased(evt)
		elif evt.getButton() == fife.MouseEvent.LEFT:
			point = self.get_world_location(evt)

			# check if position has changed with this event and update everything
			self._check_update_preview(point)

			# actually do the build
			changed_tiles = self.do_build()
			found_buildable = bool(changed_tiles)
			if found_buildable:
				PlaySound("build").execute(self.session, local=True)

			# HACK: users sometimes don't realise that roads can be dragged
			# check if 3 roads have been built within 1.2 seconds, and display
			# a hint in case
			if self._class.class_package == 'path':
				import time
				now = time.time()
				BuildingTool._last_road_built.append(now)
				if len(BuildingTool._last_road_built) > 2:
					if (now - BuildingTool._last_road_built[-3]) < 1.2:
						self.session.ingame_gui.message_widget.add(point=None, string_id="DRAG_ROADS_HINT")
						# don't display hint multiple times at the same build situation
						BuildingTool._last_road_built = []
					BuildingTool._last_road_built = BuildingTool._last_road_built[-3:]

			# check how to continue: either build again or escape
			shift = evt.isShiftPressed() or horizons.globals.fife.get_uh_setting('UninterruptedBuilding')
			if ((shift and not self._class.id == BUILDINGS.WAREHOUSE)
			    or not found_buildable
			    or self._class.class_package == 'path'):
				# build once more
				self._restore_transparencified_instances()
				self.highlight_buildable(changed_tiles)
				self.start_point = point
				self._build_logic.continue_build()
				self.preview_build(point, point)
			else:
				self.on_escape()
			evt.consume()
		elif evt.getButton() != fife.MouseEvent.RIGHT:
			super(BuildingTool, self).mouseReleased(evt)

	def do_build(self):
		"""Actually builds the previews
		@return a set of tiles where buildings have really been built"""
		changed_tiles = set()

		# actually do the build and build preparations
		for i, building in enumerate(self.buildings):
			# remove fife instance, the building will create a new one.
			# Check if there is a matching fife instance, could be missing
			# in case of trees, which are hidden if not buildable
			if building in self.buildings_fife_instances:
				fife_instance = self.buildings_fife_instances.pop(building)
				self.renderer.removeColored(fife_instance)
				self.renderer.removeOutlined(fife_instance)
				fife_instance.getLocationRef().getLayer().deleteInstance(fife_instance)

			if building.buildable:
				island = self.session.world.get_island(building.position.origin)
				for position in building.position:
					tile = island.get_tile(position)
					if tile in self._buildable_tiles:
						# for some kind of buildabilities, not every coord of the
						# building is buildable (e.g. fisher: only coastline is marked
						# as buildable). For those tiles, that are not buildable,
						# we don't need to do anything.
						self._buildable_tiles.remove(tile)
						self.renderer.removeColored(tile._instance)
						changed_tiles.add(tile)
				self._remove_listeners() # Remove changelisteners for update_preview
				# create the command and execute it
				cmd = Build(building=self._class,
							x=building.position.origin.x,
							y=building.position.origin.y,
							rotation=building.rotation,
							island=island,
							settlement=self.session.world.get_settlement(building.position.origin),
							ship=self.ship,
							tearset=building.tearset,
							action_set_id=self.buildings_action_set_ids[i],
							)
				cmd.execute(self.session)
			else:
				if len(self.buildings) == 1: # only give messages for single bulds
					# first, buildable reasons such as grounds
					# second, resources

					if building.problem is not None:
						msg = building.problem[1]
						self.session.ingame_gui.message_widget.add_custom(
						  point=building.position.origin, messagetext=msg)

					# check whether to issue a missing res notification
					# we need the localized resource name here
					elif building in self.buildings_missing_resources:
						res_name = self.session.db.get_res_name( self.buildings_missing_resources[building] )
						self.session.ingame_gui.message_widget.add(
						  point=building.position.origin,
						  string_id='NEED_MORE_RES', message_dict={'resource' : res_name})

		self.buildings = []
		self.buildings_action_set_ids = []
		return changed_tiles

	def _check_update_preview(self, end_point):
		"""Used internally if the end_point changes"""
		if self.end_point != end_point:
			self.end_point = end_point
			self.update_preview()

	def _remove_listeners(self):
		"""Resets the ChangeListener for update_preview."""
		if self.last_change_listener is not None:
			if self.last_change_listener.has_change_listener(self.force_update):
				self.last_change_listener.remove_change_listener(self.force_update)
			if self.last_change_listener.has_change_listener(self.highlight_buildable):
				self.last_change_listener.remove_change_listener(self.highlight_buildable)
			self._build_logic.remove_change_listener(self.last_change_listener, self)

		self.last_change_listener = None

	def _add_listeners(self, instance):
		if self.last_change_listener != instance:
			self._remove_listeners()
			self.last_change_listener = instance
			if self.last_change_listener is not None:
				self._build_logic.add_change_listener(self.last_change_listener, self)

	def force_update(self):
		self.update_preview(force=True)

	def update_preview(self, force=False):
		"""Used as callback method"""
		if self.start_point is not None:
			end_point = self.end_point or self.start_point
			self.preview_build(self.start_point, end_point, force=force)

	def _rotate(self, degrees):
		self.rotation = (self.rotation + degrees) % 360
		self.log.debug("BuildingTool: Building rotation now: %s", self.rotation)
		self.update_preview()
		self.draw_gui()

	def rotate_left(self):
		self._rotate(degrees=90)

	def rotate_right(self):
		self._rotate(degrees=270)
		

decorators.bind_all(BuildingTool)
decorators.bind_all(SettlementBuildingToolLogic)
decorators.bind_all(ShipBuildingToolLogic)
decorators.bind_all(BuildRelatedBuildingToolLogic)