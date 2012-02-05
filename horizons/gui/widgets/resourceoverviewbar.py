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

from fife.extensions import pychan

import weakref

from horizons.constants import RES
from horizons.world.component.storagecomponent import StorageComponent
from horizons.util.gui import load_uh_widget, get_res_icon
from horizons.util import PychanChildFinder
from horizons.util.python.decorators import cachedmethod


class ResourceOverviewBar(object):
	"""The thing on the top left.

	http://wiki.unknown-horizons.org/w/HUD

	Features:
	- display contents of currently relevant inventory (settlement/ship) [x]
	- always show gold of local player [x]
	- show costs of current build [x]
	- configure the resources to show [ ]
		- per settlement [ ]
		- switch displayed resources to construction relevant res on build [x]
		- res selection consistent with other res selection dlgs [ ]
			- goody: show available res

	Invariants:
	- it should be obvious that the res bar can be configured
	- it should be obvious that the res bar can be set per settlement

	Has distinguished treatment of gold because it's distinguished by a bigger icon
	and by being shown always.
	"""

	GOLD_ENTRY_GUI_FILE = "resource_overview_bar_gold.xml"
	ENTRY_GUI_FILE = "resource_overview_bar_entry.xml"

	STYLE = "resource_bar"

	DEFAULT_RESOURCES = [ RES.FOOD_ID,
	                      RES.TOOLS_ID,
	                      RES.BOARDS_ID,
	                      RES.BRICKS_ID,
	                      RES.TEXTILE_ID ]

	CONSTRUCTION_RESOURCES = [ RES.TOOLS_ID,
	                           RES.BOARDS_ID,
	                           RES.BRICKS_ID ]

	def __init__(self, session):
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session

		self.gold_gui = None # special slot because of special properties
		self.gui = [] # list of slots
		self._reset_gold_gui()
		self.resource_configurations = weakref.WeakKeyDictionary()
		self.current_instance = weakref.ref(self) # can't weakref to None
		self.construction_mode = False
		self._last_build_costs = None

	def load(self):
		# called when any game (also new ones) start
		# register at player inventory for gold updates
		inv = self.session.world.player.get_component(StorageComponent).inventory
		inv.add_change_listener(self._update_gold, call_listener_now=True)
		self.gold_gui.show()
		self._update_gold() # call once more to make pychan happy

	def set_inventory_instance(self, instance, keep_construction_mode=False):
		"""Display different inventory. May change resources that are displayed"""
		if self.current_instance() is instance and not self.construction_mode:
			return # caller is drunk yet again
		if self.construction_mode and not keep_construction_mode:
			self.close_construction_mode(update_slots=False)

		# remove old gui
		for i in self.gui:
			i.hide()
		self.gui = []

		if self.current_instance() and self.current_instance() is not self: # our None value
			inv = self.current_instance().get_component(StorageComponent).inventory
			inv.remove_change_listener(self._update_resources)

		if instance is None: # show nothing instead
			self.current_instance = weakref.ref(self) # can't weakref to None
			return

		self.current_instance = weakref.ref(instance)

		# construct new slots (fill values later)
		initial_offset = 93
		offset = 52
		resources = self._get_current_resources()
		for i, res in enumerate(resources):
			entry = load_uh_widget(self.ENTRY_GUI_FILE, style=self.__class__.STYLE)
			entry.findChild(name="entry").position = (initial_offset + offset * i, 17)
			entry.findChild(name="res_icon").image = get_res_icon(res)[2] # the 24 one
			entry.findChild(name="background_icon").tooltip = self.session.db.get_res_name(res)
			self.gui.append(entry)
			# show it just when values are entered, this appeases pychan

		# fill values
		inv = self.current_instance().get_component(StorageComponent).inventory
		inv.add_change_listener(self._update_resources, call_listener_now=True)

	def set_construction_mode(self, resource_source_instance, build_costs):
		"""Show resources relevant to construction and build costs
		@param resource_source_instance: object with StorageComponent
		@param build_costs: dict, { res : amount }
		"""
		if self.construction_mode and \
		   resource_source_instance == self.current_instance() and \
		   build_costs == self._last_build_costs:
			return # now that's not an update

		self._last_build_costs = build_costs

		self.construction_mode = True
		self.set_inventory_instance(resource_source_instance, keep_construction_mode=True)

		# label background icons
		cost_icon_gold = "content/gui/images/background/widgets/res_mon_extra_bg.png"
		cost_icon_res = "content/gui/images/background/widgets/res_extra_bg.png"

		for res, amount in build_costs.iteritems():
			assert res in self.__class__.CONSTRUCTION_RESOURCES or res == RES.GOLD_ID

			cost_label = pychan.widgets.Label(text=u"-"+unicode(amount))
			cost_label.stylize( self.__class__.STYLE )
			# add icon below end of background icon
			if res in self.__class__.CONSTRUCTION_RESOURCES:
				entry = self.CONSTRUCTION_RESOURCES.index(res)
				cur_gui = self.gui[ entry ]
				reference_icon = cur_gui.findChild(name="background_icon")
				below = reference_icon.size[1]
				cost_icon = pychan.widgets.Icon(image=cost_icon_res,
				                                position=(0, below))
				cost_label.position = (15, below) # TODO: centering
				cur_gui.addChild(cost_icon)
				cur_gui.addChild(cost_label)
			else: # must be gold
				reference_icon = self.gold_gui.findChild(name="background_icon")
				below = reference_icon.size[1]
				cost_icon = pychan.widgets.Icon(image=cost_icon_gold,
				                              position=(0, below) )
				cost_label.position = (15, below) # TODO: centering
				self.gold_gui.addChild(cost_icon)
				self.gold_gui.addChild(cost_label)

	def close_construction_mode(self, update_slots=True):
		"""Return to normal configuration"""
		self.construction_mode = False
		if update_slots:
			self.set_inventory_instance(None)
		self._reset_gold_gui()
		self._update_gold()
		self.gold_gui.show()
		self._update_gold()

	def _reset_gold_gui(self):
		if self.gold_gui is not None:
			self.gold_gui.hide()
		self.gold_gui = load_uh_widget(self.__class__.GOLD_ENTRY_GUI_FILE, style=self.__class__.STYLE)
		self.gold_gui.child_finder = PychanChildFinder(self.gold_gui)
		# set appropriate icon
		self.gold_gui.findChild(name="res_icon").image = get_res_icon(RES.GOLD_ID)[4] # the 32 one

	def _update_gold(self):
		"""Changelistener to upate player gold"""
		# set gold amount
		gold = self.session.world.player.get_component(StorageComponent).inventory[RES.GOLD_ID]
		gold_available_lbl = self.gold_gui.child_finder("gold_available")
		gold_available_lbl.text = unicode(gold)

		# reposition according to magic forumula passed down from the elders in order to support centering
		self.gold_gui.resizeToContent() # update label size
		gold_available_lbl.position = (33 - gold_available_lbl.size[0]/2,  51)


	def _update_resources(self):
		"""Same as _update_gold but for all other slots"""
		if not self.current_instance(): # instance died
			self.set_inventory_instance(None)
			return
		inv = self.current_instance().get_component(StorageComponent).inventory
		for i, res in enumerate(self._get_current_resources()):
			cur_gui = self.gui[i]

			# set amount
			label = cur_gui.findChild(name="res_available")
			label.text = unicode( inv[res] )

			# reposition according to magic forumula passed down from the elders in order to support centering
			cur_gui.show() # show to update values size values
			label.position = (24 - label.size[0]/2, 44)

	def _get_current_resources(self):
		"""Return list of resources to display now"""
		if self.construction_mode:
			return self.__class__.CONSTRUCTION_RESOURCES
		return self.resource_configurations.get(self.current_instance(),
		                                        self.__class__.DEFAULT_RESOURCES)



	##
	# CODE FOR REFERENCE
	##

	@cachedmethod
	def _get_res_background_icon_position(self):
		# currently unused since always 0
		# can be used for relative positioning of labels
		# old formula: label.position = (icon.position[0] - label.size[0]/2 + xoffset, yoffset)
		gui = load_uh_widget( self.__class__.ENTRY_GUI_FILE )
		icon = gui.findChild(name="background_icon")
		return icon.position

	@cachedmethod
	def _get_gold_background_icon_position(self):
		# see above
		gui = load_uh_widget( self.__class__.GOLD_ENTRY_GUI_FILE )
		icon = gui.findChild(name="background_icon")
		return icon.position