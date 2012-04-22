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

from horizons.entities import Entities
from horizons.gui.tabs.tabinterface import TabInterface
from horizons.command.building import Build
from horizons.constants import BUILDINGS
from horizons.util import Callback
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.util.python.roman_numerals import int_to_roman
from horizons.component.storagecomponent import StorageComponent
from horizons.messaging import NewPlayerSettlementHovered

class BuildTab(TabInterface):
	"""
	Layout data is defined in image_data and text_data.
	Columns in the tabs are enumerated as follows:
	  01  11  21  31
	  02  12  22  32
	  03  13  23  33
	  04  14  24  34
	Boxes and Labels have the same number as their left upper icon.
	Check buildtab.xml for details. Icons without image are transparent.
	Only adds the background image and building icon for image_data entries,
	even if more icons are defined in the xml file.

	All image_data entries map an icon position in buildtab.xml to a building ID.
	Entries in text_data are very similar and use the same positioning.
	A label with position 1 will display right above the icon at position 1.
	"""
	lazy_loading = True

	image_data = {
		1 : {
			 1 : BUILDINGS.RESIDENTIAL,
			 2 : BUILDINGS.MAIN_SQUARE,
			 3 : BUILDINGS.LUMBERJACK,
			11 : BUILDINGS.STORAGE,
			12 : BUILDINGS.PAVILION,
			13 : BUILDINGS.TREE,
			21 : BUILDINGS.TRAIL,
			22 : BUILDINGS.SIGNAL_FIRE,
			23 : BUILDINGS.HUNTER,
			31 : BUILDINGS.LOOKOUT,
			33 : BUILDINGS.FISHER,
		      },
		2 : {
			 1 : BUILDINGS.CLAY_PIT,
			 2 : BUILDINGS.FARM,
			 3 : BUILDINGS.VILLAGE_SCHOOL,
			11 : BUILDINGS.BRICKYARD,
			12 : BUILDINGS.POTATO_FIELD,
			13 : BUILDINGS.FIRE_STATION,
			21 : BUILDINGS.WEAVER,
			22 : BUILDINGS.PASTURE,
			23 : BUILDINGS.BOATBUILDER,
			31 : BUILDINGS.DISTILLERY,
			32 : BUILDINGS.SUGARCANE_FIELD,
			33 : BUILDINGS.WOODEN_TOWER,
		      },
		3 : {
			 1 : BUILDINGS.IRON_MINE,
			 2 : BUILDINGS.SALT_PONDS,
			 3 : BUILDINGS.TOBACCO_FIELD,
			 4 : BUILDINGS.TAVERN,
			11 : BUILDINGS.SMELTERY,
			12 : BUILDINGS.BUTCHERY,
			13 : BUILDINGS.CATTLE_RUN,
			21 : BUILDINGS.TOOLMAKER,
			22 : BUILDINGS.TOBACCONIST,
			23 : BUILDINGS.PIGSTY,
			24 : BUILDINGS.BARRACKS,
			31 : BUILDINGS.CHARCOAL_BURNER,
			32 : BUILDINGS.BLENDER,
			33 : BUILDINGS.SPICE_FIELD,
		      },
		4 : {
			 1 : BUILDINGS.WINDMILL,
			 2 : BUILDINGS.CORN_FIELD,
			11 : BUILDINGS.BAKERY,
			12 : BUILDINGS.COCOA_FIELD,
			21 : BUILDINGS.VINTNER,
			22 : BUILDINGS.VINEYARD,
			31 : BUILDINGS.PASTRY_SHOP,
			32 : BUILDINGS.ALVEARIES,
		      },
		}

	text_data = {
		1 : {
			 1 : _('Residents and infrastructure'),
			 2 : _('Services'),
			 3 : _('Companies'),
		      },
		2 : {
			 1 : _('Companies'),
			 2 : _('Fields'),
			 3 : _('Services'),
			23 : _('Military'),
		      },
		3 : {
			 1 : _('Mining'),
			 2 : _('Companies'),
			 3 : _('Fields'),
			 4 : _('Services'),
			24 : _('Military'),
		      },
		4 : {
			 1 : _('Companies'),
			 2 : _('Fields'),
		      },
		}

	last_active_build_tab = None

	def __init__(self, tabindex=1, callback_mapping=None, session=None,
	             icon_path='content/gui/icons/tabwidget/buildmenu/level{incr}_%s.png'):
		if callback_mapping is None:
			callback_mapping = {}
		super(BuildTab, self).__init__(widget='buildtab.xml', icon_path=icon_path.format(incr=tabindex))
		self.session = session
		self.tabindex = tabindex
		self.callback_mapping = callback_mapping

		self.helptext = _("Increment {increment}").format(increment = int_to_roman(self.tabindex))

	def _lazy_loading_init(self):
		super(BuildTab, self)._lazy_loading_init()
		self.init_gui()
		self.__current_settlement = None

	def init_gui(self):
		headline_lbl = self.widget.child_finder('headline')
		headline_lbl.text = _(self.session.db.get_settler_name(self.tabindex-1))

		self.refresh()

	def update_images(self):
		"""Shows background images and building icons where defined
		(columns as follows, left to right):
		# 1,2,3,4.. | 11,12,13,14.. | 21,22,23,24.. | 31,32,33,34..
		"""
		settlement = LastActivePlayerSettlementManager().get()
		for position, building_id in self.__class__.image_data[self.tabindex].iteritems():
			button = self.widget.child_finder('button_{position:02d}'.format(position=position))
			building = Entities.buildings[building_id]

			icon = self.widget.child_finder('icon_{position:02d}'.format(position=position))

			#xgettext:python-format
			button.helptext = self.session.db.get_building_tooltip(building_id)

			enough_res = False # don't show building by default
			if settlement is not None: # settlement is None when the mouse has left the settlement
				res_overview =  self.session.ingame_gui.resource_overview
				cbs = ( Callback( res_overview.set_construction_mode, settlement, building.costs),
				       Callback( res_overview.close_construction_mode ) )

				# can't use mapEvents since the events are taken by the tooltips.
				# they do however provide an auxiliary way around this:
				button.clear_entered_callbacks()
				button.clear_exited_callbacks()
				button.add_entered_callback(cbs[0])
				button.add_exited_callback(cbs[1])

				(enough_res, missing_res) = Build.check_resources({}, building.costs, settlement.owner, [settlement])
			#check whether to disable build menu icon (not enough res available)
			#TODO this does not refresh right now, the icons should get active
			# as soon as enough res are available!
			if enough_res:
				icon.image = "content/gui/images/buttons/buildmenu_button_bg.png"
				path = "content/gui/icons/buildmenu/{id:03d}{{mode}}.png".format(id=building_id)
				button.down_image = path.format(mode='_h')
				button.hover_image = path.format(mode='_h')
			else:
				icon.image = "content/gui/images/buttons/buildmenu_button_bg_bw.png"
				path = "content/gui/icons/buildmenu/greyscale/{id:03d}{{mode}}.png".format(id=building_id)
				button.down_image = path.format(mode='')
				button.hover_image = path.format(mode='')
			button.up_image = path.format(mode='')

			button.capture(self.callback_mapping[building_id])

	def update_text(self):
		"""Shows labels where defined (1-7 left column, 20-27 right column).
		Separated from actual build menu because called on language update.
		"""
		for position, heading in self.__class__.text_data[self.tabindex].iteritems():
			lbl = self.widget.child_finder('label_{position:02d}'.format(position=position))
			lbl.text = _(heading)

	def refresh(self):
		self.update_images()
		self.update_text()

	def on_settlement_change(self, message):
		if message.settlement is not None:
			# only react to new actual settlements, else we have no res source
			self.refresh()

	def __remove_changelisteners(self):
		NewPlayerSettlementHovered.discard(self.on_settlement_change)
		if self.__current_settlement is not None:
			inventory = self.__current_settlement.get_component(StorageComponent).inventory
			inventory.discard_change_listener(self.refresh)

	def __add_changelisteners(self):
		NewPlayerSettlementHovered.subscribe(self.on_settlement_change)
		if self.__current_settlement is not None:
			inventory = self.__current_settlement.get_component(StorageComponent).inventory
			if not inventory.has_change_listener(self.refresh):
				inventory.add_change_listener(self.refresh)

	def show(self):
		self.__remove_changelisteners()
		self.__current_settlement = LastActivePlayerSettlementManager().get()
		self.__add_changelisteners()
		self.__class__.last_active_build_tab = self.tabindex - 1 # build tabs start at 1
		super(BuildTab, self).show()

	def hide(self):
		self.__remove_changelisteners()
		super(BuildTab, self).hide()
