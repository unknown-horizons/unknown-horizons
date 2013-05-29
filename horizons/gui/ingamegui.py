# ###################################################
# Copyright (C) 2008-2013 The Unknown Horizons Team
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

import horizons.globals
from horizons.command.game import SpeedDownCommand, SpeedUpCommand, TogglePauseCommand
from horizons.component.selectablecomponent import SelectableComponent
from horizons.constants import BUILDINGS, GAME_SPEED, VERSION, LAYERS, VIEW
from horizons.entities import Entities
from horizons.gui import mousetools
from horizons.gui.keylisteners import IngameKeyListener, KeyConfig
from horizons.gui.modules import PauseMenu, HelpDialog, SelectSavegameDialog
from horizons.gui.modules.ingame import ChatDialog, ChangeNameDialog, CityInfo
from horizons.gui.tabs import TabWidget, BuildTab, DiplomacyTab, SelectMultiTab, MainSquareOverviewTab
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.logbook import LogBook
from horizons.gui.widgets.messagewidget import MessageWidget
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.widgets.playersoverview import PlayersOverview
from horizons.gui.widgets.playerssettlements import PlayersSettlements
from horizons.gui.widgets.playersships import PlayersShips
from horizons.gui.widgets.resourceoverviewbar import ResourceOverviewBar
from horizons.gui.windows import WindowManager
from horizons.messaging import (TabWidgetChanged, SpeedChanged, NewDisaster, MineEmpty,
                                NewSettlement, PlayerLevelUpgrade)
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.util.living import livingProperty, LivingObject
from horizons.util.python.callback import Callback
from horizons.world.managers.productionfinishediconmanager import ProductionFinishedIconManager
from horizons.world.managers.statusiconmanager import StatusIconManager


class IngameGui(LivingObject):
	"""Class handling all the ingame gui events.
	Assumes that only 1 instance is used (class variables)"""

	message_widget = livingProperty()
	minimap = livingProperty()
	keylistener = livingProperty()

	def __init__(self, session):
		super(IngameGui, self).__init__()
		self.session = session
		assert isinstance(self.session, horizons.session.Session)
		self.settlement = None
		self._old_menu = None

		self.cursor = None
		self.coordinates_tooltip = None

		self.keylistener = IngameKeyListener(self.session)

		self.cityinfo = CityInfo(self)
		LastActivePlayerSettlementManager.create_instance(self.session)

		self.message_widget = MessageWidget(self.session)

		# Windows
		self.windows = WindowManager()
		self.show_popup = self.windows.show_popup
		self.show_error_popup = self.windows.show_error_popup

		self.logbook = LogBook(self.session, self.windows)
		self.players_overview = PlayersOverview(self.session)
		self.players_settlements = PlayersSettlements(self.session)
		self.players_ships = PlayersShips(self.session)

		self.chat_dialog = ChatDialog(self.windows, self.session)
		self.change_name_dialog = ChangeNameDialog(self.windows, self.session)
		self.pausemenu = PauseMenu(self.session, self, self.windows, in_editor_mode=False)
		self.help_dialog = HelpDialog(self.windows, session=self.session)

		# Icon manager
		self.status_icon_manager = StatusIconManager(
			renderer=self.session.view.renderer['GenericRenderer'],
			layer=self.session.view.layers[LAYERS.OBJECTS]
		)
		self.production_finished_icon_manager = ProductionFinishedIconManager(
			renderer=self.session.view.renderer['GenericRenderer'],
			layer=self.session.view.layers[LAYERS.OBJECTS]
		)

		# 'minimap' is the guichan gui around the actual minimap, which is saved
		# in self.minimap
		self.mainhud = load_uh_widget('minimap.xml')
		self.mainhud.position_technique = "right:top"

		icon = self.mainhud.findChild(name="minimap")
		self.minimap = Minimap(icon,
		                       targetrenderer=horizons.globals.fife.targetrenderer,
		                       imagemanager=horizons.globals.fife.imagemanager,
		                       session=self.session,
		                       view=self.session.view)

		def speed_up():
			SpeedUpCommand().execute(self.session)

		def speed_down():
			SpeedDownCommand().execute(self.session)

		self.mainhud.mapEvents({
			'zoomIn' : self.session.view.zoom_in,
			'zoomOut' : self.session.view.zoom_out,
			'rotateRight' : Callback.ChainedCallbacks(self.session.view.rotate_right, self.minimap.rotate_right),
			'rotateLeft' : Callback.ChainedCallbacks(self.session.view.rotate_left, self.minimap.rotate_left),
			'speedUp' : speed_up,
			'speedDown' : speed_down,
			'destroy_tool' : self.toggle_destroy_tool,
			'build' : self.show_build_menu,
			'diplomacyButton' : self.show_diplomacy_menu,
			'gameMenuButton' : self.toggle_pause,
			'logbook' : lambda: self.windows.toggle(self.logbook)
		})
		self.mainhud.show()

		self.resource_overview = ResourceOverviewBar(self.session)

		# Register for messages
		SpeedChanged.subscribe(self._on_speed_changed)
		NewDisaster.subscribe(self._on_new_disaster)
		NewSettlement.subscribe(self._on_new_settlement)
		PlayerLevelUpgrade.subscribe(self._on_player_level_upgrade)
		MineEmpty.subscribe(self._on_mine_empty)
		self.session.view.add_change_listener(self._update_zoom)

		self._display_speed(self.session.timer.ticks_per_second)

	def end(self):
		# unsubscribe early, to avoid messages coming in while we're shutting down
		SpeedChanged.unsubscribe(self._on_speed_changed)
		NewDisaster.unsubscribe(self._on_new_disaster)
		NewSettlement.unsubscribe(self._on_new_settlement)
		PlayerLevelUpgrade.unsubscribe(self._on_player_level_upgrade)
		MineEmpty.unsubscribe(self._on_mine_empty)
		self.session.view.remove_change_listener(self._update_zoom)

		self.mainhud.mapEvents({
			'zoomIn' : None,
			'zoomOut' : None,
			'rotateRight' : None,
			'rotateLeft': None,

			'destroy_tool' : None,
			'build' : None,
			'diplomacyButton' : None,
			'gameMenuButton' : None
		})
		self.mainhud.hide()
		self.mainhud = None

		self.windows.close_all()
		self.message_widget = None
		self.minimap = None
		self.resource_overview.end()
		self.resource_overview = None
		self.keylistener = None
		self.cityinfo.end()
		self.cityinfo = None
		self.hide_menu()

		if self.cursor:
			self.cursor.remove()
			self.cursor.end()
			self.cursor = None

		LastActivePlayerSettlementManager().remove()
		LastActivePlayerSettlementManager.destroy_instance()

		self.production_finished_icon_manager.end()
		self.production_finished_icon_manager = None
		self.status_icon_manager.end()
		self.status_icon_manager = None

		super(IngameGui, self).end()

	def show_select_savegame(self, mode):
		window = SelectSavegameDialog(mode, self.windows)
		return self.windows.show(window)

	def toggle_pause(self):
		self.windows.toggle(self.pausemenu)

	def toggle_help(self):
		self.windows.toggle(self.help_dialog)

	def minimap_to_front(self):
		"""Make sure the full right top gui is visible and not covered by some dialog"""
		self.mainhud.hide()
		self.mainhud.show()

	def show_diplomacy_menu(self):
		# check if the menu is already shown
		if getattr(self.get_cur_menu(), 'name', None) == "diplomacy_widget":
			self.hide_menu()
			return

		if not DiplomacyTab.is_useable(self.session.world):
			self.windows.show_popup(_("No diplomacy possible"),
			                        _("Cannot do diplomacy as there are no other players."))
			return

		tab = DiplomacyTab(self, self.session.world)
		self.show_menu(tab)

	def show_multi_select_tab(self, instances):
		tab = TabWidget(self, tabs=[SelectMultiTab(instances)], name='select_multi')
		self.show_menu(tab)

	def show_build_menu(self, update=False):
		"""
		@param update: set when build possibilities change (e.g. after inhabitant tier upgrade)
		"""
		# check if build menu is already shown
		if hasattr(self.get_cur_menu(), 'name') and self.get_cur_menu().name == "build_menu_tab_widget":
			self.hide_menu()

			if not update: # this was only a toggle call, don't reshow
				return

		self.set_cursor() # set default cursor for build menu
		self.deselect_all()

		if not any( settlement.owner.is_local_player for settlement in self.session.world.settlements):
			# player has not built any settlements yet. Accessing the build menu at such a point
			# indicates a mistake in the mental model of the user. Display a hint.
			tab = TabWidget(self, tabs=[ TabInterface(widget="buildtab_no_settlement.xml") ])
		else:
			btabs = BuildTab.create_tabs(self.session, self._build)
			tab = TabWidget(self, tabs=btabs, name="build_menu_tab_widget",
											active_tab=BuildTab.last_active_build_tab)
		self.show_menu(tab)

	def deselect_all(self):
		for instance in self.session.selected_instances:
			instance.get_component(SelectableComponent).deselect()
		self.session.selected_instances.clear()

	def _build(self, building_id, unit=None):
		"""Calls the games buildingtool class for the building_id.
		@param building_id: int with the building id that is to be built.
		@param unit: weakref to the unit, that builds (e.g. ship for warehouse)"""
		self.hide_menu()
		self.deselect_all()
		cls = Entities.buildings[building_id]
		if hasattr(cls, 'show_build_menu'):
			cls.show_build_menu()
		self.set_cursor('building', cls, None if unit is None else unit())

	def toggle_road_tool(self):
		if not isinstance(self.cursor, mousetools.BuildingTool) or self.cursor._class.id != BUILDINGS.TRAIL:
			self._build(BUILDINGS.TRAIL)
		else:
			self.set_cursor()

	def get_cur_menu(self):
		"""Returns menu that is currently displayed"""
		return self._old_menu

	def show_menu(self, menu):
		"""Shows a menu
		@param menu: str with the guiname or pychan object.
		"""
		if self._old_menu is not None:
			if hasattr(self._old_menu, "remove_remove_listener"):
				self._old_menu.remove_remove_listener( Callback(self.show_menu, None) )
			self._old_menu.hide()

		self._old_menu = menu
		if self._old_menu is not None:
			if hasattr(self._old_menu, "add_remove_listener"):
				self._old_menu.add_remove_listener( Callback(self.show_menu, None) )
			self._old_menu.show()
			self.minimap_to_front()

		TabWidgetChanged.broadcast(self)

	def hide_menu(self):
		self.show_menu(None)

	def save(self, db):
		self.message_widget.save(db)
		self.logbook.save(db)
		self.resource_overview.save(db)
		LastActivePlayerSettlementManager().save(db)

	def load(self, db):
		self.message_widget.load(db)
		self.logbook.load(db)
		self.resource_overview.load(db)

		if self.session.is_game_loaded():
			LastActivePlayerSettlementManager().load(db)
			cur_settlement = LastActivePlayerSettlementManager().get_current_settlement()
			self.cityinfo.set_settlement(cur_settlement)

		self.minimap.draw() # update minimap to new world

		self.current_cursor = 'default'
		self.cursor = mousetools.SelectionTool(self.session)
		# Set cursor correctly, menus might need to be opened.
		# Open menus later; they may need unit data not yet inited
		self.cursor.apply_select()

		if not self.session.is_game_loaded():
			# Fire a message for new world creation
			self.session.ingame_gui.message_widget.add('NEW_WORLD')

		# Show message when the relationship between players changed
		def notify_change(caller, old_state, new_state, a, b):
			player1 = u"%s" % a.name
			player2 = u"%s" % b.name

			data = {'player1' : player1, 'player2' : player2}

			string_id = 'DIPLOMACY_STATUS_{old}_{new}'.format(old=old_state.upper(),
			                                                  new=new_state.upper())
			self.message_widget.add(string_id=string_id, message_dict=data)

		self.session.world.diplomacy.add_diplomacy_status_changed_listener(notify_change)

	def show_change_name_dialog(self, instance):
		"""Shows a dialog where the user can change the name of an object."""
		self.windows.show(self.change_name_dialog, instance=instance)

	def on_escape(self):
		if self.windows.visible:
			self.windows.on_escape()
		elif hasattr(self.cursor, 'on_escape'):
			self.cursor.on_escape()
		else:
			self.toggle_pause()

		return True

	def on_return(self):
		if self.windows.visible:
			self.windows.on_return()

		return True

	def _on_speed_changed(self, message):
		self._display_speed(message.new)

	def _display_speed(self, tps):
		text = u''
		up_icon = self.mainhud.findChild(name='speedUp')
		down_icon = self.mainhud.findChild(name='speedDown')
		if tps == 0: # pause
			text = u'0x'
			up_icon.set_inactive()
			down_icon.set_inactive()
		else:
			if tps != GAME_SPEED.TICKS_PER_SECOND:
				text = unicode("%1gx" % (tps * 1.0/GAME_SPEED.TICKS_PER_SECOND))
				#%1g: displays 0.5x, but 2x instead of 2.0x
			index = GAME_SPEED.TICK_RATES.index(tps)
			if index + 1 >= len(GAME_SPEED.TICK_RATES):
				up_icon.set_inactive()
			else:
				up_icon.set_active()
			if index > 0:
				down_icon.set_active()
			else:
				down_icon.set_inactive()

		wdg = self.mainhud.findChild(name="speed_text")
		wdg.text = text
		wdg.resizeToContent()
		self.mainhud.show()

	def on_key_press(self, action, evt):
		"""Handle a key press in-game.

		Returns True if the key was acted upon.
		"""
		_Actions = KeyConfig._Actions
		keyval = evt.getKey().getValue()

		if action == _Actions.ESCAPE:
			return self.on_escape()
		elif keyval == fife.Key.ENTER:
			return self.on_return()

		if action == _Actions.GRID:
			gridrenderer = self.session.view.renderer['GridRenderer']
			gridrenderer.setEnabled( not gridrenderer.isEnabled() )
		elif action == _Actions.COORD_TOOLTIP:
			self.coordinates_tooltip.toggle()
		elif action == _Actions.DESTROY_TOOL:
			self.toggle_destroy_tool()
		elif action == _Actions.REMOVE_SELECTED:
			self.session.remove_selected()
		elif action == _Actions.ROAD_TOOL:
			self.toggle_road_tool()
		elif action == _Actions.SPEED_UP:
			SpeedUpCommand().execute(self.session)
		elif action == _Actions.SPEED_DOWN:
			SpeedDownCommand().execute(self.session)
		elif action == _Actions.PAUSE:
			TogglePauseCommand().execute(self.session)
		elif action == _Actions.PLAYERS_OVERVIEW:
			self.logbook.toggle_stats_visibility(widget='players')
		elif action == _Actions.SETTLEMENTS_OVERVIEW:
			self.logbook.toggle_stats_visibility(widget='settlements')
		elif action == _Actions.SHIPS_OVERVIEW:
			self.logbook.toggle_stats_visibility(widget='ships')
		elif action == _Actions.LOGBOOK:
			self.windows.toggle(self.logbook)
		elif action == _Actions.DEBUG and VERSION.IS_DEV_VERSION:
			import pdb; pdb.set_trace()
		elif action == _Actions.BUILD_TOOL:
			self.show_build_menu()
		elif action == _Actions.ROTATE_RIGHT:
			if hasattr(self.cursor, "rotate_right"):
				# used in e.g. build preview to rotate building instead of map
				self.cursor.rotate_right()
			else:
				self.session.view.rotate_right()
				self.minimap.rotate_right()
		elif action == _Actions.ROTATE_LEFT:
			if hasattr(self.cursor, "rotate_left"):
				self.cursor.rotate_left()
			else:
				self.session.view.rotate_left()
				self.minimap.rotate_left()
		elif action == _Actions.CHAT:
			self.windows.show(self.chat_dialog)
		elif action == _Actions.TRANSLUCENCY:
			self.session.world.toggle_translucency()
		elif action == _Actions.TILE_OWNER_HIGHLIGHT:
			self.session.world.toggle_owner_highlight()
		elif keyval in (fife.Key.NUM_0, fife.Key.NUM_1, fife.Key.NUM_2, fife.Key.NUM_3, fife.Key.NUM_4,
		                fife.Key.NUM_5, fife.Key.NUM_6, fife.Key.NUM_7, fife.Key.NUM_8, fife.Key.NUM_9):
			num = int(keyval - fife.Key.NUM_0)
			if evt.isControlPressed():
				# create new group (only consider units owned by the player)
				self.session.selection_groups[num] = \
				    set(filter(lambda unit : unit.owner.is_local_player,
				               self.session.selected_instances))
				# drop units of the new group from all other groups
				for group in self.session.selection_groups:
					if group is not self.session.selection_groups[num]:
						group -= self.session.selection_groups[num]
			else:
				# deselect
				# we need to make sure to have a cursor capable of selection (for apply_select())
				# this handles deselection implicitly in the destructor
				self.set_cursor('selection')

				# apply new selection
				for instance in self.session.selection_groups[num]:
					instance.get_component(SelectableComponent).select(reset_cam=True)
				# assign copy since it will be randomly changed, the unit should only be changed on ctrl-events
				self.session.selected_instances = self.session.selection_groups[num].copy()
				# show menu depending on the entities selected
				if self.session.selected_instances:
					self.cursor.apply_select()
				else:
					# nothing is selected here, we need to hide the menu since apply_select doesn't handle that case
					self.show_menu(None)
		elif action == _Actions.QUICKSAVE:
			self.session.quicksave() # load is only handled by the MainListener
		elif action == _Actions.PIPETTE:
			# copy mode: pipette tool
			self.toggle_cursor('pipette')
		elif action == _Actions.HEALTH_BAR:
			# shows health bar of every instance with an health component
			self.session.world.toggle_health_for_all_health_instances()
		elif action == _Actions.SHOW_SELECTED:
			if self.session.selected_instances:
				# scroll to first one, we can never guarantee to display all selected units
				instance = iter(self.session.selected_instances).next()
				self.session.view.center( * instance.position.center.to_tuple())
				for instance in self.session.selected_instances:
					if hasattr(instance, "path") and instance.owner.is_local_player:
						self.minimap.show_unit_path(instance)
		elif action == _Actions.HELP:
			self.toggle_help()
		else:
			return False

		return True

	def toggle_cursor(self, which, *args, **kwargs):
		"""Alternate between the cursor which and default.
		args and kwargs are used to construct which."""
		if self.current_cursor == which:
			self.set_cursor()
		else:
			self.set_cursor(which, *args, **kwargs)

	def set_cursor(self, which='default', *args, **kwargs):
		"""Sets the mousetool (i.e. cursor).
		This is done here for encapsulation and control over destructors.
		Further arguments are passed to the mouse tool constructor."""
		self.cursor.remove()
		self.current_cursor = which
		klass = {
			'default'        : mousetools.SelectionTool,
			'selection'      : mousetools.SelectionTool,
			'tearing'        : mousetools.TearingTool,
			'pipette'        : mousetools.PipetteTool,
			'attacking'      : mousetools.AttackingTool,
			'building'       : mousetools.BuildingTool,
		}[which]
		self.cursor = klass(self.session, *args, **kwargs)

	def toggle_destroy_tool(self):
		"""Initiate the destroy tool"""
		self.toggle_cursor('tearing')

	def _update_zoom(self):
		"""Enable/disable zoom buttons"""
		zoom = self.session.view.get_zoom()
		in_icon = self.mainhud.findChild(name='zoomIn')
		out_icon = self.mainhud.findChild(name='zoomOut')
		if zoom == VIEW.ZOOM_MIN:
			out_icon.set_inactive()
		else:
			out_icon.set_active()
		if zoom == VIEW.ZOOM_MAX:
			in_icon.set_inactive()
		else:
			in_icon.set_active()

	def _on_new_disaster(self, message):
		"""Called when a building is 'infected' with a disaster."""
		if message.building.owner.is_local_player:
			pos = message.building.position.center
			self.message_widget.add(point=pos, string_id=message.disaster_class.NOTIFICATION_TYPE)

	def _on_new_settlement(self, message):
		player = message.settlement.owner
		self.message_widget.add(
			string_id='NEW_SETTLEMENT',
			point=message.warehouse_position,
			message_dict={'player': player.name},
			play_sound=player.is_local_player
		)

	def _on_player_level_upgrade(self, message):
		"""Called when a player's population reaches a new level."""
		if not message.sender.is_local_player:
			return

		# show notification
		self.message_widget.add(
			point=message.building.position.center,
			string_id='SETTLER_LEVEL_UP',
			message_dict={'level': message.level + 1}
		)

		# update build menu to show new buildings
		menu = self.get_cur_menu()
		if hasattr(menu, "name") and menu.name == "build_menu_tab_widget":
			self.show_build_menu(update=True)

		# TODO: Use a better measure then first tab
		# Quite fragile, makes sure the tablist in the mainsquare menu is updated
		if hasattr(menu, '_tabs') and isinstance(menu._tabs[0], MainSquareOverviewTab):
			instance = list(self.session.selected_instances)[0]
			instance.get_component(SelectableComponent).show_menu(jump_to_tabclass=type(menu.current_tab))

	def _on_mine_empty(self, message):
		self.message_widget.add(point=message.mine.position.center, string_id='MINE_EMPTY')
