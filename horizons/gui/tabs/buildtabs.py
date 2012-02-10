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
from horizons.util import Callback
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.util.python.roman_numerals import int_to_roman
from horizons.world.component.storagecomponent import StorageComponent
from horizons.util.messaging.message import LastSettlementChanged

class BuildTab(TabInterface):
	"""
	Layout data is defined in image_data and text_data.
	Columns in the tabs are enumerated as follows:
	  1  2  21 22
	  3  4  23 24
	  5  6  25 26
	  7  8  27 28
	Boxes and Labels have the same number as their left upper icon.
	Check buildtab.xml for details. Icons without image are transparent.
	Only adds the background image and building icon for image_data entries,
	even if more icons are defined in the xml file.

	All image_data entries map an icon position in buildtab.xml to a building ID.
	Entries in text_data are very similar, but only exist twice each row (icons
	four times). They thus enumerate 1,3,5,7.. and 21,23,25,27.. instead.

	TODO: Implement refresh() calls to BuildTabs
	TODO: Call update_text when applying new interface language
	"""

	image_data = {
		1 : {
			 1 : 3, # tent
			 2 : 2, # storage tent
			 3 : 4, # main square
			 4 : 5, # pavilion
			 5 : 8, # lumberjack
			 6 : 17,# tree
			21 : 15,# trail
			23 : 6, # signal fire
			25 : 9, # hunter
			26 : 11,# fisher
		      },
		2 : {
			 1 : 25,
			 2 : 24,
			 3 : 20,
			 4 : 19,
			 5 : 21,
			 6 : 45,
			21 : 7,
			22 : 26,
			23 : 18,
			24 : 22,
			25 : 12,
			26 : 44,
		      },
		3 : {
			 1 : 28,
			 2 : 29,
			 3 : 35,
			 4 : 41,
			 5 : 36,
			 6 : 38,
			 7 : 32,
			21 : 30,
			22 : 31,
			23 : 37,
			24 : 50,
			25 : 39,
			26 : 49,
			27 : 53,
		      },
		4 : {
			 1 : 47,
			 2 : 48,
			 3 : 46,
			 4 : 60,
			21 : 65,
			22 : 63,
			23 : 61,
			24 : 62,
		      },
		}

	text_data = {
		1 : {
			 1 : _('Residents and infrastructure'),
			 3 : _('Services'),
			 5 : _('Companies'),
		      },
		2 : {
			 1 : _('Companies'),
			 3 : _('Fields'),
			 5 : _('Services'),
			25 : _('Military'),
		      },
		3 : {
			 1 : _('Mining'),
			 3 : _('Companies'),
			 5 : _('Fields'),
			 7 : _('Services'),
			27 : _('Military'),
		      },
		4 : {
			 1 : _('Companies'),
			 3 : _('Fields'),
		      },
		}

	last_active_build_tab = None

	def __init__(self, tabindex = 1, callback_mapping=None, session=None):
		if callback_mapping is None:
			callback_mapping = {}
		super(BuildTab, self).__init__(widget = 'buildtab.xml')
		self.init_values()
		self.session = session
		self.tabindex = tabindex
		self.callback_mapping = callback_mapping

		icon_path = 'content/gui/icons/tabwidget/buildmenu/level{incr}_%s.png'.format(incr=tabindex)
		self.button_up_image = icon_path % ('u')
		self.button_active_image = icon_path % ('a')
		self.button_down_image = icon_path % ('d')
		self.button_hover_image = icon_path % ('h')

		self.helptext = _("Increment {increment}").format(increment = int_to_roman(tabindex))

		self.init_gui()
		self.__current_settlement = None

	def init_gui(self):
		headline_lbl = self.widget.child_finder('headline')
		#i18n In English, this is Sailors, Pioneers, Settlers.
		#TODO what formatting to use? getting names from DB and adding
		# '... buildings' will cause wrong declinations all over :/
		headline_lbl.text = _('{incr_inhabitant_name}').format(incr_inhabitant_name='Sailors') #xgettext:python-format

		self.refresh()

	def update_images(self):
		"""Shows background images and building icons where defined
		(columns as follows, left to right):
		# 1,3,5,7.. | 2,4,6,8.. | 21,23,25,27.. | 22,24,26,28..
		"""
		settlement = LastActivePlayerSettlementManager().get()
		for position, building_id in self.__class__.image_data[self.tabindex].iteritems():
			button = self.widget.child_finder('button_{position}'.format(position=position))
			building = Entities.buildings[building_id]

			icon = self.widget.child_finder('icon_{position}'.format(position=position))

			#xgettext:python-format
			button.helptext = _('{building}: {description}').format(building = _(building.name),
			                                                    description = _(building.tooltip_text))

			enough_res = False # don't show building by default
			if settlement is not None: # settlement is None when the mouse has left the settlement
				res_overview =  self.session.ingame_gui.resource_overview
				cbs = ( Callback( res_overview.set_construction_mode, settlement, building.costs),
				       Callback( res_overview.close_construction_mode ) )

				# can't use mapEvents since the events are taken by the tooltips.
				# they do however provide an auxiliary way around this:
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
			lbl = self.widget.child_finder('label_{position}'.format(position=position))
			lbl.text = _(heading)

	def refresh(self):
		self.update_images()
		self.update_text()

	def on_settlement_change(self, message):
		self.refresh()

	def __remove_changelisteners(self):
		self.session.message_bus.discard_globally(LastSettlementChanged, self.on_settlement_change)
		if self.__current_settlement is not None:
			inventory = self.__current_settlement.get_component(StorageComponent).inventory
			inventory.discard_change_listener(self.refresh)

	def __add_changelisteners(self):
		self.session.message_bus.subscribe_globally(LastSettlementChanged, self.on_settlement_change)
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
