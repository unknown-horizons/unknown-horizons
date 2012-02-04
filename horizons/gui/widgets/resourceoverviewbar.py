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

from horizons.constants import RES
from horizons.world.component.storagecomponent import StorageComponent
from horizons.util.gui import load_uh_widget
from horizons.util import PychanChildFinder

class ResourceOverviewBar(object):
	"""The thing on the top left.

	http://wiki.unknown-horizons.org/w/HUD

	Features:
	- display contents of currently relevant inventory (settlement/ship) [ ]
	- always show gold of local player [ ]
	- show costs of current build [ ]
	- configure the resources to show [ ]
		- per settlement [ ]
		- switch displayed resources to construction relevant res on build [ ]
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

	def __init__(self, session):
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session
		self.gold_gui = load_uh_widget(self.__class__.GOLD_ENTRY_GUI_FILE, style="resource_bar")
		self.gold_gui.child_finder = PychanChildFinder(self.gold_gui)
		self.gui = [] # list of slots

	def load(self):
		# called when any game (also new ones) start
		# register at player inventory for gold updates
		inv = self.session.world.player.get_component(StorageComponent).inventory
		inv.add_change_listener(self._update_gold, call_listener_now=True)

		self.gold_gui.show()

	def set_inventory_instance(self, instance):
		"""Display different inventory. May change resources that are displayed"""
		print 'set instance: ', instance
		# TODO

	def set_construction_mode(self, resource_source_instance, build_costs):
		"""Show resources relevant to construction and build costs
		@param resource_source_instance: object with StorageComponent
		@param build_costs: dict, { res : amount }
		"""
		print 'set construction mode'
		#TODO
		pass

	def close_construction_mode(self):
		"""Return to normal configuration"""
		print 'close construction mode'
		# TODO
		# hide gui
		pass

	def _update_gold(self):
		"""Changelistener to upate player gold"""
		# set gold amount
		gold = self.session.world.player.get_component(StorageComponent).inventory[RES.GOLD_ID]
		gold_available_lbl = self.gold_gui.child_finder("gold_available")
		gold_available_lbl.text = text = unicode(gold)

		# reposition according to magic forumula passed down from the elders in order to support centering
		self.gold_gui.resizeToContent() # update label size
		icon_position = self.gold_gui.child_finder(name="gold_icon").position
		gold_available_lbl.position = (icon_position[0] - gold_available_lbl.size[0]/2 + 33,  51)

