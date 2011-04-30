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

from fife.extensions import pychan

import horizons.main
from horizons.entities import Entities

from horizons.util import livingProperty, LivingObject, PychanChildFinder, Rect, Point
from horizons.util.python import Callback
from horizons.gui.mousetools import BuildingTool, SelectionTool
from horizons.gui.tabs import TabWidget, BuildTab
from horizons.gui.widgets.messagewidget import MessageWidget
from horizons.gui.widgets.minimap import Minimap
from horizons.gui.widgets.logbook import LogBook
from horizons.gui.utility import LazyWidgetsDict
from horizons.constants import RES
from horizons.command.uioptions import RenameObject
from horizons.command.misc import Chat

class IngameGui(LivingObject):
	"""Class handling all the ingame gui events."""

	gui = livingProperty()
	tabwidgets = livingProperty()
	message_widget = livingProperty()
	minimap = livingProperty()

	styles = {
		'city_info' : 'city_info',
		'change_name' : 'book',
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
		self.widgets = {}
		self.tabwidgets = {}
		self.settlement = None
		self.resource_source = None
		self.resources_needed, self.resources_usable = {}, {}
		self._old_menu = None

		self.widgets = LazyWidgetsDict(self.styles, center_widgets=False)

		cityinfo = self.widgets['city_info']
		cityinfo.child_finder = PychanChildFinder(cityinfo)
		cityinfo.position_technique = "center-10:top+5"

		self.logbook = LogBook(session)

		# self.widgets['minimap'] is the guichan gui around the actual minimap,
		# which is saved in self.minimap

		minimap = self.widgets['minimap']
		minimap.position_technique = "right-20:top+4"
		minimap.show()

		minimap_rect = Rect.init_from_topleft_and_size(minimap.position[0]+77, 55, 120, 120)

		self.minimap = Minimap(minimap_rect, self.session, \
		                       self.session.view.renderer['GenericRenderer'])
		minimap.mapEvents({
			'zoomIn' : self.session.view.zoom_in,
			'zoomOut' : self.session.view.zoom_out,
			'rotateRight' : Callback.ChainedCallbacks(self.session.view.rotate_right, self.minimap.rotate_right),
			'rotateLeft' : Callback.ChainedCallbacks(self.session.view.rotate_left, self.minimap.rotate_left),
			'speedUp' : self.session.speed_up,
			'speedDown' : self.session.speed_down
		})

		minimap_overlay = minimap.findChild(name='minimap_overlay_image')

		self.minimap.use_overlay_icon(minimap_overlay)

		self.widgets['menu_panel'].position_technique = "right+15:top+149"
		self.widgets['menu_panel'].show()
		self.widgets['menu_panel'].mapEvents({
			'destroy_tool' : self.session.destroy_tool,
			'build' : self.show_build_menu,
			'helpLink' : self.main_gui.on_help,
			'gameMenuButton' : self.main_gui.show_pause,
			'logbook' : self.logbook.toggle_visibility
		})

		self.widgets['tooltip'].hide()

		self.widgets['status'].child_finder = PychanChildFinder(self.widgets['status'])
		self.widgets['status_extra'].child_finder = PychanChildFinder(self.widgets['status_extra'])

		self.message_widget = MessageWidget(self.session, \
		                                    cityinfo.position[0] + cityinfo.size[0], 5)
		self.widgets['status_gold'].show()
		self.widgets['status_gold'].child_finder = PychanChildFinder(self.widgets['status_gold'])
		self.widgets['status_extra_gold'].child_finder = PychanChildFinder(self.widgets['status_extra_gold'])

		# map button names to build functions calls with the building id
		callbackWithArguments = pychan.tools.callbackWithArguments
		self.callbacks_build = {}
		for id,button_name,settler_level in horizons.main.db.get_building_id_buttonname_settlerlvl():
			if not settler_level in self.callbacks_build:
				self.callbacks_build[settler_level] = {}
			self.callbacks_build[settler_level][button_name] = Callback(self._build, id)

	def end(self):
		self.widgets['menu_panel'].mapEvents({
			'destroy_tool' : None,
			'build' : None,
			'helpLink' : None,
			'gameMenuButton' : None
		})

		self.widgets['minimap'].mapEvents({
			'zoomIn' : None,
			'zoomOut' : None,
			'rotateRight' : None,
			'rotateLeft' : None
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
		first = str(self.session.world.player.inventory[RES.GOLD_ID])
		lines = []
		show = False
		if self.resource_source is not None and self.resources_needed.get(RES.GOLD_ID, 0) != 0:
			show = True
			lines.append('- ' + str(self.resources_needed[RES.GOLD_ID]))
		self.status_set('gold', first)
		self.status_set_extra('gold',lines)
		self.set_status_position('gold')
		if show:
			self.widgets['status_extra_gold'].show()
		else:
			self.widgets['status_extra_gold'].hide()

	def status_set(self, label, value):
		"""Sets a value on the status bar (available res of the settlement).
		@param label: str containing the name of the label to be set.
		@param value: value the Label is to be set to.
		"""
		if isinstance(value,list):
			value = value[0]
		gui = self.widgets['status_gold'] if label == 'gold' else self.widgets['status']
		foundlabel = gui.child_finder(label + '_1')
		foundlabel._setText(unicode(value))
		foundlabel.resizeToContent()
		gui.resizeToContent()

	def status_set_extra(self,label,value):
		"""Sets a value on the extra status bar. (below normal status bar, needed res for build)
		@param label: str containing the name of the label to be set.
		@param value: value the Label is to be set to.
		"""
		bg_icon_gold = "content/gui/images/background/widgets/res_mon_extra_bg.png"
		bg_icon_res = "content/gui/images/background/widgets/res_extra_bg.png"
		if not hasattr(self, "bg_icon_pos"):
			self.bg_icon_pos = {'gold':(14,83), 'food':(0,6), 'tools':(52,6), 'boards':(104,6), 'bricks':(156,6), 'textiles':(207,6)}
			self.bgs_shown = {}
		bg_icon = pychan.widgets.Icon(image=bg_icon_gold if label == 'gold' else bg_icon_res, \
		                              position=self.bg_icon_pos[label], name='bg_icon_' + label)

		if not value:
			foundlabel = (self.widgets['status_extra_gold'] if label == 'gold' else self.widgets['status_extra']).child_finder(label + '_' + str(2))
			foundlabel.text = u''
			foundlabel.resizeToContent()
			if label in self.bgs_shown:
				(self.widgets['status_extra_gold'] if label == 'gold' else self.widgets['status_extra']).removeChild(self.bgs_shown[label])
				del self.bgs_shown[label]
			self.widgets['status_extra_gold'].resizeToContent() if label == 'gold' else self.widgets['status_extra'].resizeToContent()
			return
		if isinstance(value, str):
			value = [value]
		#for i in xrange(len(value), 3):
		#	value.append("")

		if (self.widgets['status_extra_gold'] if label == 'gold' else self.widgets['status_extra']).findChild(name='bg_icon_' + label) is None:
			(self.widgets['status_extra_gold'] if label == 'gold' else self.widgets['status_extra']).insertChild(bg_icon, 0)
			self.bgs_shown[label] = bg_icon

		for i in xrange(0,len(value)):
			foundlabel = (self.widgets['status_extra_gold'] if label == 'gold' else self.widgets['status_extra']).child_finder(name=label + '_' + str(i+2))
			foundlabel._setText(unicode(value[i]))
			foundlabel.resizeToContent()
		if label == 'gold':
			self.widgets['status_extra_gold'].resizeToContent()
		else:
			self.widgets['status_extra'].resizeToContent()

	def cityinfo_set(self, settlement):
		"""Sets the city name at top center

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

	def resourceinfo_set(self, source, res_needed = {}, res_usable = {}, res_from_ship = False):
		city = source if not res_from_ship else None
		self.cityinfo_set(city)
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
			self.resources_needed = res_needed
			self.resources_usable = res_usable
			self.update_resource_source()
			self.widgets['status'].show()

	def update_settlement(self):
		cityinfo = self.widgets['city_info']
		cityinfo.mapEvents({
			'city_name': Callback(self.show_change_name_dialog, self.settlement)
			})
		foundlabel = cityinfo.child_finder('city_name')
		foundlabel._setText(unicode(self.settlement.name))
		foundlabel.resizeToContent()
		foundlabel = self.widgets['city_info'].child_finder('city_inhabitants')
		foundlabel.text = unicode(' '+str(self.settlement.inhabitants))
		foundlabel.resizeToContent()
		self.widgets['city_info'].resizeToContent()

	def update_resource_source(self):
		"""Sets the values for resource status bar as well as the building costs"""
		self.update_gold()
		for res_id, res_name in {3 : 'textiles', 4 : 'boards', 5 : 'food', 6 : 'tools', 7 : 'bricks'}.iteritems():
			first = str(self.resource_source.inventory[res_id])
			lines = []
			show = False
			if self.resources_needed.get(res_id, 0) != 0:
				show = True
				lines.append('- ' + str(self.resources_needed[res_id]))
			self.status_set(res_name, first)
			self.status_set_extra(res_name,lines)
			self.set_status_position(res_name)
			if show:
				self.widgets['status_extra'].show()

	def ship_build(self, ship):
		"""Calls the Games build_object class."""
		self._build(1, ship)

	def minimap_to_front(self):
		self.widgets['minimap'].hide()
		self.widgets['minimap'].show()
		self.widgets['menu_panel'].hide()
		self.widgets['menu_panel'].show()

	def show_build_menu(self):
		# check if build menu is already shown
		if hasattr(self.get_cur_menu(), 'name') and self.get_cur_menu().name == "build_menu_tab_widget":
			self.hide_menu()
			return

		self.session.cursor = SelectionTool(self.session) # set cursor for build menu
		self.deselect_all()
		btabs = [BuildTab(index, self.callbacks_build[index]) for index in \
		         range(0, self.session.world.player.settler_level+1)]
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
		@param unit: weakref to the unit, that builds (e.g. ship for branch office)"""
		self.hide_menu()
		self.deselect_all()
		cls = Entities.buildings[building_id]
		if hasattr(cls, 'show_build_menu'):
			cls.show_build_menu()
		self.session.cursor = BuildingTool(self.session, cls, None if unit is None else unit())

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

	def build_load_tab(self, num):
		"""Loads a subcontainer into the build menu and changes the tabs background.
		@param num: number representing the tab to load.
		"""
		tab1 = self.widgets['build'].findChild(name=('tab'+str(self.active_build)))
		tab2 = self.widgets['build'].findChild(name=('tab'+str(num)))
		activetabimg, nonactiveimg= tab1._getImage(), tab2._getImage()
		tab1._setImage(nonactiveimg)
		tab2._setImage(activetabimg)
		contentarea = self.widgets['build'].findChild(name='content')
		contentarea.removeChild(self.widgets['build_tab'+str(self.active_build)])
		contentarea.addChild(self.widgets['build_tab'+str(num)])
		contentarea.adaptLayout()
		self.active_build = num

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
		"""Shows a dialog where the user can change the name of a NamedObject.
		The game gets paused while the dialog is executed."""
		self.session.speed_pause()
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
		self.session.speed_unpause()
		self.main_gui.on_escape = self.main_gui.show_pause
		self.widgets['change_name'].hide()

	def change_name(self, instance):
		"""Applies the change_name dialogs input and hides it"""
		new_name = self.widgets['change_name'].collectData('new_name')
		self.widgets['change_name'].findChild(name='new_name').text = u''
		if not (len(new_name) == 0 or new_name.isspace()):
			RenameObject(instance, new_name).execute(self.session)
		self._hide_change_name_dialog()

	_toggle_ingame_pause_shown = False
	def toggle_ingame_pause(self):
		"""
		Called when the hotkey for pause is pressed.
		Displays pause notification and does the actual (un)pausing.
		"""
		message = _("Hit P to continue the game or click below!")
		popup = self.main_gui.build_popup(_("Game paused"), message)
		if not self._toggle_ingame_pause_shown:
			self.session.speed_pause()
			self.main_gui.on_escape = self.toggle_ingame_pause
			popup.mapEvents({'okButton': self.toggle_ingame_pause})
			popup.show()
			self._toggle_ingame_pause_shown = True
		else:
			self.main_gui.on_escape = self.main_gui.show_pause
			popup.hide()
			self.session.speed_unpause()
			self._toggle_ingame_pause_shown = False

	def on_escape(self):
		if self.logbook.is_visible():
			self.logbook.hide()
		else:
			return False
		return True

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
				self.show_build_menu()

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
		self.main_gui.on_escape = self.main_gui.show_pause
		self.widgets['chat'].hide()

	def _do_chat(self):
		"""Actually initiates chatting and hides the dialog"""
		msg = self.widgets['chat'].findChild(name='msg').text
		Chat(msg).execute(self.session)
		self.widgets['chat'].findChild(name='msg').text = u''
		self._hide_chat_dialog()
