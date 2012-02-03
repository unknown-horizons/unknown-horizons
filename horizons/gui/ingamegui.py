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

import re
import horizons.main
from fife.extensions import pychan

from horizons.entities import Entities
from horizons.util import livingProperty, LivingObject, PychanChildFinder
from horizons.util.python import Callback
from horizons.gui.mousetools import BuildingTool
from horizons.gui.tabs import TabWidget, BuildTab, DiplomacyTab, SelectMultiTab
from horizons.gui.widgets.messagewidget import MessageWidget
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.widgets.logbook import LogBook
from horizons.gui.widgets.playersoverview import PlayersOverview
from horizons.gui.widgets.playerssettlements import PlayersSettlements
from horizons.gui.widgets.playersships import PlayersShips
from horizons.gui.widgets.choose_next_scenario import ScenarioChooser
from horizons.util.gui import LazyWidgetsDict
from horizons.constants import BUILDINGS, RES
from horizons.command.uioptions import RenameObject
from horizons.command.misc import Chat
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.world.component.namedcomponent import SettlementNameComponent
from horizons.world.component.storagecomponent import StorageComponent

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
		'chat' : 'book',
		'status'            : 'resource_bar',
		'status_gold'       : 'resource_bar',
		'status_extra'      : 'resource_bar',
		'status_extra_gold' : 'resource_bar',
	}

	def __init__(self, session, gui):
		super(IngameGui, self).__init__()
		self.session = session
		self.main_gui = gui
		self.main_widget = None
		self.tabwidgets = {}
		self.settlement = None
		self.resource_source = None
		self.resources_needed, self.resources_usable = {}, {}
		self._old_menu = None

		self.widgets = LazyWidgetsDict(self.styles, center_widgets=False)

		cityinfo = self.widgets['city_info']
		cityinfo.child_finder = PychanChildFinder(cityinfo)

		# special settings for really small resolutions
		width = horizons.main.fife.engine_settings.getScreenWidth()
		x = 'center'
		y = 'top'
		x_offset = -10
		y_offset = +4
		if width < 800:
			x = 'left'
			x_offset = 10
			y_offset = +66
		elif width < 1020:
			x_offset = (1000 - width) / 2
		cityinfo.position_technique = "%s%+d:%s%+d" % (x, x_offset, y, y_offset) # usually "center-10:top+4"

		self.logbook = LogBook(self.session)
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
		                       targetrenderer=horizons.main.fife.targetrenderer,
		                       imagemanager=horizons.main.fife.imagemanager,
		                       session=self.session,
		                       world=self.session.world,
		                       view=self.session.view)
		minimap.mapEvents({
			'zoomIn' : self.session.view.zoom_in,
			'zoomOut' : self.session.view.zoom_out,
			'rotateRight' : Callback.ChainedCallbacks(self.session.view.rotate_right, self.minimap.rotate_right),
			'rotateLeft' : Callback.ChainedCallbacks(self.session.view.rotate_left, self.minimap.rotate_left),
			'speedUp' : self.session.speed_up,
			'speedDown' : self.session.speed_down,

			'destroy_tool' : self.session.toggle_destroy_tool,
			'build' : self.show_build_menu,
			'diplomacyButton' : self.show_diplomacy_menu,
			'gameMenuButton' : self.main_gui.toggle_pause,
			'logbook' : self.logbook.toggle_visibility
		})

		minimap.show()
		#minimap.position_technique = "right+15:top+153"

		self.widgets['tooltip'].hide()

		self.widgets['status'].child_finder = PychanChildFinder(self.widgets['status'])
		self.widgets['status_extra'].child_finder = PychanChildFinder(self.widgets['status_extra'])

		self.message_widget = MessageWidget(self.session)
		self.widgets['status_gold'].show()
		self.widgets['status_gold'].child_finder = PychanChildFinder(self.widgets['status_gold'])
		self.widgets['status_extra_gold'].child_finder = PychanChildFinder(self.widgets['status_extra_gold'])

		# map buildings to build functions calls with their building id.
		# This is necessary because BuildTabs have no session.
		self.callbacks_build = dict()
		for building_id in Entities.buildings.iterkeys():
			self.callbacks_build[building_id] = Callback(self._build, building_id)

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
		self.hide_menu()
		super(IngameGui, self).end()

	def update_gold(self):
		player_gold = self.session.world.player.get_component(StorageComponent).inventory[RES.GOLD_ID]
		self.status_set('gold', player_gold)

		gold_needed = self.resources_needed.get(RES.GOLD_ID, None) # defaults to None if key not found
		show = False
		amount = None
		if self.resource_source is not None and gold_needed is not None:
			show = True
			amount = u'-{amount}'.format(amount = gold_needed)
		self.status_set_extra('gold', amount)

		self.set_status_position('gold')
		if show:
			self.widgets['status_extra_gold'].show()
		else:
			self.widgets['status_extra_gold'].hide()

	def status_set(self, res, value):
		"""Sets a value on the status bar (available res of the player/settlement).
		@param res: str containing the name of the label to be set (usually a resource name).
		@param value: value the Label is to be set to.
		"""
		gui = self.widgets['status_gold'] if res == 'gold' else self.widgets['status']
		# labels: tools_1 = inventory amount, tools_2 = cost of to-be-built building
		foundlabel = gui.child_finder('{res}_1'.format(res=res))
		foundlabel.text = unicode(value)
		foundlabel.resizeToContent()
		gui.resizeToContent()

	def status_set_extra(self, res, value):
		"""Sets a value on the extra status bar. (below normal status bar, needed res for build)
		@param res: str containing the name of the label to be set (usually a resource name).
		@param value: value the Label is to be set to. Gets converted to unicode. None if empty.
		"""
		bg_icon_gold = "content/gui/images/background/widgets/res_mon_extra_bg.png"
		bg_icon_res = "content/gui/images/background/widgets/res_extra_bg.png"

		if res == 'gold':
			extra_widget = self.widgets['status_extra_gold']
		else:
			extra_widget = self.widgets['status_extra']

		if not hasattr(self, "bg_icon_pos"):
			self.bg_icon_pos = {'gold':(14,83), 'food':(0,6), 'tools':(52,6), 'boards':(104,6), 'bricks':(156,6), 'textiles':(207,6)}
			self.bgs_shown = {}
		bg_icon = pychan.widgets.Icon(image=bg_icon_gold if res == 'gold' else bg_icon_res, \
		                              position=self.bg_icon_pos[res], name='bg_icon_{res}'.format(res=res))

		# labels: tools_1 = inventory amount, tools_2 = cost of to-be-built building
		if value is None:
			foundlabel = extra_widget if res == 'gold' else extra_widget.child_finder('{res}_2'.format(res=res))
			foundlabel.text = u''
			foundlabel.resizeToContent()
			if res in self.bgs_shown:
				extra_widget.removeChild(self.bgs_shown[res])
				del self.bgs_shown[res]
			return

		if extra_widget.findChild(name='bg_icon_{res}'.format(res=res)) is None:
			extra_widget.insertChild(bg_icon, 0)
			self.bgs_shown[res] = bg_icon

		# labels: tools_1 = inventory amount, tools_2 = cost of to-be-built building
		foundlabel = extra_widget.child_finder(name='{res}_2'.format(res=res))
		foundlabel.text = unicode(value)
		foundlabel.resizeToContent()
		extra_widget.resizeToContent()

	def cityinfo_set(self, settlement):
		"""Sets the city name at top center of screen.

		Show/Hide is handled automatically
		To hide cityname, set name to ''
		@param settlement: Settlement class providing the information needed
		"""
		if settlement is self.settlement:
			return
		if self.settlement is not None:
			self.settlement.remove_change_listener(self.update_settlement)
		self.settlement = settlement
		if settlement is None:
			self.widgets['city_info'].hide()
		else:
			self.widgets['city_info'].show()
			self.update_settlement()
			settlement.add_change_listener(self.update_settlement)

	def resourceinfo_set(self, source, res_needed = None, res_usable = None):
		if source is not self.resource_source:
			if self.resource_source is not None:
				self.resource_source.remove_change_listener(self.update_resource_source)
			if source is None or self.session.world.player != source.owner:
				self.widgets['status'].hide()
				self.widgets['status_extra'].hide()
				self.resource_source = None
				self.update_gold()
		if source is not None and self.session.world.player == source.owner:
			if source is not self.resource_source:
				source.add_change_listener(self.update_resource_source)
			self.resource_source = source
			self.resources_needed = {} if not res_needed else res_needed
			self.resources_usable = {} if not res_usable else res_usable
			self.update_resource_source()
			self.widgets['status'].show()

	def update_settlement(self):
		cityinfo = self.widgets['city_info']
		cityinfo.mapEvents({
			'city_name': Callback(self.show_change_name_dialog, self.settlement)
			})

		foundlabel = cityinfo.child_finder('owner_emblem')
		foundlabel.image = 'content/gui/images/tabwidget/emblems/emblem_%s.png' % (self.settlement.owner.color.name)
		foundlabel.tooltip = unicode(self.settlement.owner.name)

		foundlabel = cityinfo.child_finder('city_name')
		foundlabel.text = unicode(self.settlement.get_component(SettlementNameComponent).name)
		foundlabel.resizeToContent()

		foundlabel = cityinfo.child_finder('city_inhabitants')
		foundlabel.text = unicode(' %s' % (self.settlement.inhabitants))
		foundlabel.resizeToContent()

		cityinfo.adaptLayout()

	def update_resource_source(self):
		"""Sets the values for resource status bar as well as the building costs"""
		self.update_gold()
		for res_id, res_name in {3 : 'textiles', 4 : 'boards', 5 : 'food', 6 : 'tools', 7 : 'bricks'}.iteritems():
			inventory_res = self.resource_source.get_component(StorageComponent).inventory[res_id]
			self.status_set(res_name, inventory_res)

			res_needed = self.resources_needed.get(res_id, None) # defaults to None if key not found
			show = False
			amount = None
			if res_needed is not None:
				show = True
				amount = u'-{amount}'.format(amount = res_needed)
			self.status_set_extra(res_name, amount)

			self.set_status_position(res_name)
			if show:
				self.widgets['status_extra'].show()

	def minimap_to_front(self):
		self.widgets['minimap'].hide()
		self.widgets['minimap'].show()

	def show_diplomacy_menu(self):
		# check if the menu is already shown
		if hasattr(self.get_cur_menu(), 'name') and self.get_cur_menu().name == "diplomacy_widget":
			self.hide_menu()
			return
		players = set(self.session.world.players)
		players.add(self.session.world.pirate)
		players.discard(self.session.world.player)
		players.discard(None) # e.g. when the pirate is disabled
		if len(players) == 0: # this dialog is pretty useless in this case
			self.main_gui.show_popup(_("No diplomacy possible"), \
			                         _("Cannot do diplomacy as there are no other players."))
			return

		dtabs = []
		for player in players:
			dtabs.append(DiplomacyTab(player))
		tab = TabWidget(self, tabs=dtabs, name="diplomacy_widget")
		self.show_menu(tab)

	def show_multi_select_tab(self):
		tab = TabWidget(self, tabs = [SelectMultiTab(self.session)], name = 'select_multi')
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

		if not any( (settlement.owner == self.session.world.player) for settlement in self.session.world.settlements):
			# player has not built any settlements yet. Accessing the build menu at such a point
			# indicates a mistake in the mental model of the user. Display a hint.
			tab = TabWidget(self, tabs=[ TabInterface(widget="buildtab_no_settlement.xml") ])
		else:
			btabs = [BuildTab(index+1, self.callbacks_build, self.session) for index in \
							 range(self.session.world.player.settler_level+1)]
			tab = TabWidget(self, tabs=btabs, name="build_menu_tab_widget", \
											active_tab=BuildTab.last_active_build_tab)
		self.show_menu(tab)

	def deselect_all(self):
		for instance in self.session.selected_instances:
			instance.deselect()
		self.session.selected_instances.clear()

	def _build(self, building_id, unit = None):
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
		if not isinstance(self.session.cursor, BuildingTool) or self.session.cursor._class.id != BUILDINGS.TRAIL_CLASS:
			if isinstance(self.session.cursor, BuildingTool):
				print self.session.cursor._class.id, BUILDINGS.TRAIL_CLASS
			self._build(BUILDINGS.TRAIL_CLASS)
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
			self._old_menu.hide()

		self._old_menu = self._get_menu_object(menu)
		if self._old_menu is not None:
			self._old_menu.show()
			self.minimap_to_front()

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

	def set_status_position(self, resource_name):
		icon_name = resource_name + '_icon'
		for i in xrange(1, 3):
			lbl_name = resource_name + '_' + str(i)
			# tools_1 = inventory amount, tools_2 = cost of to-be-built building
			if resource_name == 'gold':
				self._set_label_position('status_gold', lbl_name, icon_name, 33, 31 + i*20)
			else:
				self._set_label_position('status', lbl_name, icon_name, 24, 31 + i*20)

	def _set_label_position(self, widget, lbl_name, icon_name, xoffset, yoffset):
		icon  = self.widgets[widget].child_finder(icon_name)
		label = self.widgets[widget].child_finder(lbl_name)
		label.position = (icon.position[0] - label.size[0]/2 + xoffset, yoffset)

	def save(self, db):
		self.message_widget.save(db)
		self.logbook.save(db)

	def load(self, db):
		self.message_widget.load(db)
		self.logbook.load(db)

		self.minimap.draw() # update minimap to new world

	def show_change_name_dialog(self, instance):
		"""Shows a dialog where the user can change the name of a NamedComponant.
		The game gets paused while the dialog is executed."""
		events = {
			'okButton': Callback(self.change_name, instance),
			'cancelButton': self._hide_change_name_dialog
		}
		self.main_gui.on_escape = self._hide_change_name_dialog
		changename = self.widgets['change_name']
		newname = changename.findChild(name='new_name')
		changename.mapEvents(events)
		newname.capture(Callback(self.change_name, instance))
		changename.show()
		newname.requestFocus()

	def _hide_change_name_dialog(self):
		"""Escapes the change_name dialog"""
		self.main_gui.on_escape = self.main_gui.toggle_pause
		self.widgets['change_name'].hide()

	def change_name(self, instance):
		"""Applies the change_name dialogs input and hides it.
		If the new name has length 0 or only contains blanks, the old name is kept.
		"""
		new_name = self.widgets['change_name'].collectData('new_name')
		self.widgets['change_name'].findChild(name='new_name').text = u''
		if not (len(new_name) == 0 or new_name.isspace()):
			RenameObject(instance, new_name).execute(self.session)
		self._hide_change_name_dialog()

	def show_save_map_dialog(self):
		"""Shows a dialog where the user can set the name of the saved map."""
		events = {
			'okButton': self.save_map,
			'cancelButton': self._hide_save_map_dialog
		}
		self.main_gui.on_escape = self._hide_save_map_dialog
		dialog = self.widgets['save_map']
		name = dialog.findChild(name = 'map_name')
		name.text = u''
		dialog.mapEvents(events)
		name.capture(Callback(self.save_map))
		dialog.show()
		name.requestFocus()

	def _hide_save_map_dialog(self):
		"""Closes the map saving dialog."""
		self.main_gui.on_escape = self.main_gui.toggle_pause
		self.widgets['save_map'].hide()

	def save_map(self):
		"""Saves the map and hides the dialog."""
		name = self.widgets['save_map'].collectData('map_name')
		if re.match('^[a-zA-Z0-9_-]+$', name):
			self.session.save_map(name)
			self._hide_save_map_dialog()
		else:
			#xgettext:python-format
			message = _('Valid map names are in the following form: {expression}').format(expression='[a-zA-Z0-9_-]+')
			#xgettext:python-format
			advice = _('Try a name that only contains letters and numbers.')
			self.session.gui.show_error_popup(_('Error'), message, advice)

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

	def _player_settler_level_change_listener(self):
		"""Gets called when the player changes"""
		menu = self.get_cur_menu()
		if hasattr(menu, "name"):
			if menu.name == "build_menu_tab_widget":
				# player changed and build menu is currently displayed
				self.show_build_menu(update=True)

	def show_chat_dialog(self):
		"""Show a dialog where the user can enter a chat message"""
		events = {
			'okButton': self._do_chat,
			'cancelButton': self._hide_chat_dialog
		}
		self.main_gui.on_escape = self._hide_chat_dialog

		self.widgets['chat'].mapEvents(events)
		self.widgets['chat'].findChild(name='msg').capture( self._do_chat )
		self.widgets['chat'].show()
		self.widgets['chat'].findChild(name="msg").requestFocus()

	def _hide_chat_dialog(self):
		"""Escapes the chat dialog"""
		self.main_gui.on_escape = self.main_gui.toggle_pause
		self.widgets['chat'].hide()

	def _do_chat(self):
		"""Actually initiates chatting and hides the dialog"""
		msg = self.widgets['chat'].findChild(name='msg').text
		Chat(msg).execute(self.session)
		self.widgets['chat'].findChild(name='msg').text = u''
		self._hide_chat_dialog()
