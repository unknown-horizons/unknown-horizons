# ###################################################
# Copyright (C) 2010 The Unknown Horizons Team
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

import horizons.globals

from horizons.entities import Entities
from horizons.util.living import livingProperty, LivingObject
from horizons.util.pychanchildfinder import PychanChildFinder
from horizons.util.python.callback import Callback
from horizons.gui.mousetools import BuildingTool
from horizons.gui.tabs import TabWidget, BuildTab, DiplomacyTab, SelectMultiTab
from horizons.gui.widgets.messagewidget import MessageWidget
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.widgets.logbook import LogBook
from horizons.gui.widgets.playersoverview import PlayersOverview
from horizons.gui.widgets.playerssettlements import PlayersSettlements
from horizons.gui.widgets.resourceoverviewbar import ResourceOverviewBar
from horizons.gui.widgets.playersships import PlayersShips
from horizons.gui.widgets.choose_next_scenario import ScenarioChooser
from horizons.extscheduler import ExtScheduler
from horizons.gui.util import LazyWidgetsDict
from horizons.constants import BUILDINGS, GUI
from horizons.command.game import SpeedDownCommand, SpeedUpCommand
from horizons.gui.ingame import ChangeNameDialog, SaveMapDialog, ChatDialog, LogbookProxy
from horizons.gui.pausemenu import PauseMenu
from horizons.gui.mainmenu import Help, Settings, SaveLoad
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.gui.tabs import MainSquareOverviewTab
from horizons.gui.window import WindowManager
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.component.selectablecomponent import SelectableComponent
from horizons.component.namedcomponent import SettlementNameComponent
from horizons.messaging import SettlerUpdate, SettlerInhabitantsChanged, ResourceBarResize, HoverSettlementChanged, TabWidgetChanged
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager

class IngameGui(LivingObject):
	"""Class handling all the ingame gui events.
	Assumes that only 1 instance is used (class variables)"""

	gui = livingProperty()
	tabwidgets = livingProperty()
	message_widget = livingProperty()
	minimap = livingProperty()

	styles = {
		'city_info' : 'city_info',
		'change_name' : 'book',
		'save_map' : 'book',
		'help': 'book',
		'chat' : 'book',
		'ingamemenu': 'headline',
		'game_settings' : 'book',
	  	'select_savegame': 'book',
	}

	def __init__(self, session, gui):
		super(IngameGui, self).__init__()
		self.session = session
		assert isinstance(self.session, horizons.session.Session)
		self.main_gui = gui
		self.main_widget = None
		self.tabwidgets = {}
		self.settlement = None
		self.resource_source = None
		self.resources_needed, self.resources_usable = {}, {}
		self._old_menu = None

		self.widgets = LazyWidgetsDict(self.styles, center_widgets=False)

		self.windows = WindowManager(self.widgets)
		self._settings = Settings(None, manager=self.windows)
		self._help = Help(self.widgets, gui=self, manager=self.windows)
		self._pausemenu = PauseMenu(self.widgets, gui=self, manager=self.windows)
		self._change_name_dialog = ChangeNameDialog(self.widgets, gui=self, manager=self.windows)
		self._save_map_dialog = SaveMapDialog(self.widgets, gui=self, manager=self.windows)
		self._chat_dialog = ChatDialog(self.widgets, gui=self, manager=self.windows)
		self._logbook_proxy = LogbookProxy(self.widgets, gui=self, manager=self.windows)
		self._saveload = SaveLoad(self.widgets, gui=self, manager=self.windows)

		self.cityinfo = self.widgets['city_info']
		self.cityinfo.child_finder = PychanChildFinder(self.cityinfo)

		self.logbook = LogBook(self.session)
		self.message_widget = MessageWidget(self.session)
		self.players_overview = PlayersOverview(self.session)
		self.players_settlements = PlayersSettlements(self.session)
		self.players_ships = PlayersShips(self.session)
		self.scenario_chooser = ScenarioChooser(self.session)

		# self.widgets['minimap'] is the guichan gui around the actual minimap,
		# which is saved in self.minimap
		minimap = self.widgets['minimap']
		minimap.position_technique = "right+0:top+0"

		icon = minimap.findChild(name="minimap")
		self.minimap = Minimap(icon,
		                       targetrenderer=horizons.globals.fife.targetrenderer,
		                       imagemanager=horizons.globals.fife.imagemanager,
		                       session=self.session,
		                       view=self.session.view)

		def speed_up():
			SpeedUpCommand().execute(self.session)

		def speed_down():
			SpeedDownCommand().execute(self.session)

		minimap.mapEvents({
			'zoomIn' : self.session.view.zoom_in,
			'zoomOut' : self.session.view.zoom_out,
			'rotateRight' : Callback.ChainedCallbacks(self.session.view.rotate_right, self.minimap.rotate_right),
			'rotateLeft' : Callback.ChainedCallbacks(self.session.view.rotate_left, self.minimap.rotate_left),
			'speedUp' : speed_up,
			'speedDown' : speed_down,
			'destroy_tool' : self.session.toggle_destroy_tool,
			'build' : self.show_build_menu,
			'diplomacyButton' : self.show_diplomacy_menu,
			'gameMenuButton' : self.toggle_pause,
			'logbook' : self.logbook.toggle_visibility
		})
		minimap.show()
		#minimap.position_technique = "right+15:top+153"

		self.widgets['tooltip'].hide()

		self.resource_overview = ResourceOverviewBar(self.session)
		ResourceBarResize.subscribe(self._on_resourcebar_resize)

		# Register for messages
		SettlerUpdate.subscribe(self._on_settler_level_change)
		SettlerInhabitantsChanged.subscribe(self._on_settler_inhabitant_change)
		HoverSettlementChanged.subscribe(self._cityinfo_set)

	def _on_resourcebar_resize(self, message):
		self._update_cityinfo_position()

	def end(self):
		self.widgets['minimap'].mapEvents({
			'zoomIn' : None,
			'zoomOut' : None,
			'rotateRight' : None,
			'rotateLeft': None,

			'destroy_tool' : None,
			'build' : None,
			'diplomacyButton' : None,
			'gameMenuButton' : None
		})

		for w in self.widgets.itervalues():
			if w.parent is None:
				w.hide()
		self.message_widget = None
		self.tabwidgets = None
		self.minimap = None
		self.resource_overview.end()
		self.resource_overview = None
		self.hide_menu()
		SettlerUpdate.unsubscribe(self._on_settler_level_change)
		ResourceBarResize.unsubscribe(self._on_resourcebar_resize)
		HoverSettlementChanged.unsubscribe(self._cityinfo_set)
		SettlerInhabitantsChanged.unsubscribe(self._on_settler_inhabitant_change)

		super(IngameGui, self).end()

	def _cityinfo_set(self, message):
		"""Sets the city name at top center of screen.

		Show/Hide is handled automatically
		To hide cityname, set name to ''
		@param message: HoverSettlementChanged message
		"""
		settlement = message.settlement
		old_was_player_settlement = False
		if self.settlement is not None:
			self.settlement.remove_change_listener(self.update_settlement)
			old_was_player_settlement = self.settlement.owner.is_local_player

		# save reference to new "current" settlement in self.settlement
		self.settlement = settlement

		if settlement is None: # we want to hide the widget now (but perhaps delayed).
			if old_was_player_settlement:
				# After scrolling away from settlement, leave name on screen for some
				# seconds. Players can still click on it to rename the settlement now.
				ExtScheduler().add_new_object(self.cityinfo.hide, self,
				      run_in=GUI.CITYINFO_UPDATE_DELAY)
				#TODO 'click to rename' tooltip of cityinfo can stay visible in
				# certain cases if cityinfo gets hidden in tooltip delay buffer.
			else:
				# hovered settlement of other player, simply hide the widget
				self.cityinfo.hide()

		else:# do not hide if settlement is hovered and a hide was previously scheduled
			ExtScheduler().rem_call(self, self.cityinfo.hide)

			self.update_settlement() # calls show()
			settlement.add_change_listener(self.update_settlement)

	def _on_settler_inhabitant_change(self, message):
		assert isinstance(message, SettlerInhabitantsChanged)
		foundlabel = self.cityinfo.child_finder('city_inhabitants')
		old_amount = int(foundlabel.text) if foundlabel.text else 0
		foundlabel.text = u' {amount:>4d}'.format(amount=old_amount+message.change)
		foundlabel.resizeToContent()

	def update_settlement(self):
		city_name_label = self.cityinfo.child_finder('city_name')
		if self.settlement.owner.is_local_player: # allow name changes
			# Update settlement on the resource overview to make sure it
			# is setup correctly for the coming calculations
			self.resource_overview.set_inventory_instance(self.settlement)
			cb = Callback(self.show_change_name_dialog, self.settlement)
			helptext = _("Click to change the name of your settlement")
			city_name_label.enable_cursor_change_on_hover()
		else: # no name changes
			cb = lambda : AmbientSoundComponent.play_special('error')
			helptext = u""
			city_name_label.disable_cursor_change_on_hover()
		self.cityinfo.mapEvents({
			'city_name': cb
		})
		city_name_label.helptext = helptext

		foundlabel = self.cityinfo.child_finder('owner_emblem')
		foundlabel.image = 'content/gui/images/tabwidget/emblems/emblem_%s.png' % (self.settlement.owner.color.name)
		foundlabel.helptext = self.settlement.owner.name

		foundlabel = self.cityinfo.child_finder('city_name')
		foundlabel.text = self.settlement.get_component(SettlementNameComponent).name
		foundlabel.resizeToContent()

		foundlabel = self.cityinfo.child_finder('city_inhabitants')
		foundlabel.text = u' {amount:>4d}'.format(amount=self.settlement.inhabitants)
		foundlabel.resizeToContent()

		self._update_cityinfo_position()

	def _update_cityinfo_position(self):
		""" Places cityinfo widget depending on resource bar dimensions.

		For a normal-sized resource bar and reasonably large resolution:
		* determine resource bar length (includes gold)
		* determine empty horizontal space between resbar end and minimap start
		* display cityinfo centered in that area if it is sufficiently large

		If too close to the minimap (cityinfo larger than length of this empty space)
		move cityinfo centered to very upper screen edge. Looks bad, works usually.
		In this case, the resbar is redrawn to put the cityinfo "behind" it visually.
		"""
		width = horizons.globals.fife.engine_settings.getScreenWidth()
		resbar = self.resource_overview.get_size()
		is_foreign = (self.settlement.owner != self.session.world.player)
		blocked = self.cityinfo.size[0] + int(1.6*self.minimap.get_size()[1])
		# minimap[1] returns width! Use 1.6*width because of the GUI around it

		if is_foreign: # other player, no resbar exists
			self.cityinfo.pos = ('center', 'top')
			xoff = +0
			yoff = +4
		elif blocked < width < resbar[0] + blocked: # large resbar / small resolution
			self.cityinfo.pos = ('center', 'top')
			xoff = +0
			yoff = -21 # upper screen edge
		else:
			self.cityinfo.pos = ('left', 'top')
			xoff = resbar[0] + (width - blocked - resbar[0]) // 2
			yoff = +4

		self.cityinfo.offset = (xoff, yoff)
		self.cityinfo.position_technique = "{pos[0]}{off[0]:+d}:{pos[1]}{off[1]:+d}".format(
				pos=self.cityinfo.pos,
				off=self.cityinfo.offset )
		self.cityinfo.hide()
		self.cityinfo.show()

	def minimap_to_front(self):
		"""Make sure the full right top gui is visible and not covered by some dialog"""
		self.widgets['minimap'].hide()
		self.widgets['minimap'].show()

	def show_diplomacy_menu(self):
		# check if the menu is already shown
		if getattr(self.get_cur_menu(), 'name', None) == "diplomacy_widget":
			self.hide_menu()
			return

		if not DiplomacyTab.is_useable(self.session.world):
			self.show_popup(_("No diplomacy possible"),
			                _("Cannot do diplomacy as there are no other players."))
			return

		tab = DiplomacyTab(self, self.session.world)
		self.show_menu(tab)

	def show_multi_select_tab(self):
		tab = TabWidget(self, tabs=[SelectMultiTab(self.session)], name='select_multi')
		self.show_menu(tab)

	def show_build_menu(self, update=False):
		"""
		@param update: set when build possiblities change (e.g. after settler upgrade)
		"""
		# check if build menu is already shown
		if hasattr(self.get_cur_menu(), 'name') and self.get_cur_menu().name == "build_menu_tab_widget":
			self.hide_menu()

			if not update: # this was only a toggle call, don't reshow
				return

		self.session.set_cursor() # set default cursor for build menu
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
		self.session.set_cursor('building', cls, None if unit is None else unit())

	def toggle_road_tool(self):
		if not isinstance(self.session.cursor, BuildingTool) or self.session.cursor._class.id != BUILDINGS.TRAIL:
			self._build(BUILDINGS.TRAIL)
		else:
			self.session.set_cursor()

	def _get_menu_object(self, menu):
		"""Returns pychan object if menu is a string, else returns menu
		@param menu: str with the guiname or pychan object.
		"""
		if isinstance(menu, str):
			menu = self.widgets[menu]
		return menu

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

		self._old_menu = self._get_menu_object(menu)
		if self._old_menu is not None:
			if hasattr(self._old_menu, "add_remove_listener"):
				self._old_menu.add_remove_listener( Callback(self.show_menu, None) )
			self._old_menu.show()
			self.minimap_to_front()

		TabWidgetChanged.broadcast(self)

	def hide_menu(self):
		self.show_menu(None)

	def toggle_menu(self, menu):
		"""Shows a menu or hides it if it is already displayed.
		@param menu: parameter supported by show_menu().
		"""
		if self.get_cur_menu() == self._get_menu_object(menu):
			self.hide_menu()
		else:
			self.show_menu(menu)

	def save(self, db):
		self.message_widget.save(db)
		self.logbook.save(db)
		self.resource_overview.save(db)

	def load(self, db):
		# hide maingui (and therefore removing the loadingscreen)
		self.main_gui.hide()

		self.message_widget.load(db)
		self.logbook.load(db)
		self.resource_overview.load(db)

		cur_settlement = LastActivePlayerSettlementManager().get_current_settlement()
		self._cityinfo_set( HoverSettlementChanged(self, cur_settlement) )

		self.minimap.draw() # update minimap to new world

	def show_change_name_dialog(self, instance):
		"""Shows a dialog where the user can change the name of a NamedComponant.
		The game gets paused while the dialog is executed."""
		self.windows.show(self._change_name_dialog, instance=instance)

	def show_save_map_dialog(self):
		"""Shows a dialog where the user can set the name of the saved map."""
		self.windows.show(self._save_map_dialog)

	def on_escape(self):
		if self.main_widget:
			self.main_widget.hide()
		else:
			return False
		return True

	def on_switch_main_widget(self, widget):
		"""The main widget has been switched to the given one (possibly None)."""
		if self.main_widget and self.main_widget != widget: # close the old one if it exists
			old_main_widget = self.main_widget
			self.main_widget = None
			old_main_widget.hide()
		self.main_widget = widget

	def display_game_speed(self, text):
		"""
		@param text: unicode string to display as speed value
		"""
		wdg = self.widgets['minimap'].findChild(name="speed_text")
		wdg.text = text
		wdg.resizeToContent()
		self.widgets['minimap'].show()

	def _on_settler_level_change(self, message):
		"""Gets called when the player changes"""
		if message.sender.owner.is_local_player:
			menu = self.get_cur_menu()
			if hasattr(menu, "name") and menu.name == "build_menu_tab_widget":
				# player changed and build menu is currently displayed
				self.show_build_menu(update=True)

			# TODO: Use a better measure then first tab
			# Quite fragile, makes sure the tablist in the mainsquare menu is updated
			if hasattr(menu, '_tabs') and isinstance(menu._tabs[0], MainSquareOverviewTab):
				instance = list(self.session.selected_instances)[0]
				instance.get_component(SelectableComponent).show_menu(jump_to_tabclass=type(menu.current_tab))

	def show_chat_dialog(self):
		"""Show a dialog where the user can enter a chat message"""
		self.windows.show(self._chat_dialog)

	def quit_session(self, force=False):
		"""Quits the current session. Usually returns to main menu afterwards.
		@param force: whether to ask for confirmation"""
		message = _("Are you sure you want to abort the running session?")

		if force or self.show_popup(_("Quit Session"), message, show_cancel_button=True):
			# Close all windows before ending the session
			self.windows.close_all()

			if self.session is not None:
				self.session.end()
				self.session = None

			self.main_gui.show()
			return True
		else:
			return False

	def toggle_pause(self):
		"""Shows in-game pause menu if the game is currently not paused.
		Else unpauses and hides the menu. Multiple layers of the 'paused' concept exist;
		if two widgets are opened which would both pause the game, we do not want to
		unpause after only one of them is closed. Uses PauseCommand and UnPauseCommand.
		"""
		self.windows.toggle(self._pausemenu)

	def toggle_help(self):
		self.windows.toggle(self._help)

	def toggle_player_stats(self):
		self.windows.toggle(self._logbook_proxy, page='players')

	def toggle_settlement_stats(self):
		self.windows.toggle(self._logbook_proxy, page='settlements')

	def toggle_ship_stats(self):
		self.windows.toggle(self._logbook_proxy, page='ships')

	def toggle_logbook(self):
		self.windows.toggle(self._logbook_proxy)

	def show_popup(self, *args, **kwargs):
		return self.windows.show_popup(*args, **kwargs)

	def show_error_popup(self, *args, **kwargs):
		return self.windows.show_error_popup(*args, **kwargs)
