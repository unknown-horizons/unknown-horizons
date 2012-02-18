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
from fife.extensions import pychan
import json
import weakref
import functools

import horizons.main

from horizons.constants import RES
from horizons.world.component.storagecomponent import StorageComponent
from horizons.util.gui import load_uh_widget, get_res_icon, create_resource_selection_dialog
from horizons.util import PychanChildFinder, Callback
from horizons.util.python.decorators import cachedmethod
from horizons.util.messaging.message import ResourceBarResize
from horizons.extscheduler import ExtScheduler
from horizons.world.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager


class ResourceOverviewBar(object):
	"""The thing on the top left.

	http://wiki.unknown-horizons.org/w/HUD

	Features:
	- display contents of currently relevant inventory (settlement/ship) [x]
	- always show gold of local player [x]
	- show costs of current build [x]
	- configure the resources to show [x]
		- per settlement [x]
		- add new slots [x]
		- switch displayed resources to construction relevant res on build [x]
		- res selection consistent with other res selection dlgs [x]

	Invariants:
	- it should be obvious that the res bar can be configured
	- it should be obvious that the res bar can be set per settlement

	Has distinguished treatment of gold because it's distinguished by a bigger icon
	and by being shown always.
	"""

	GOLD_ENTRY_GUI_FILE = "resource_overview_bar_gold.xml"
	ENTRY_GUI_FILE = "resource_overview_bar_entry.xml"

	STYLE = "resource_bar"

	DEFAULT_RESOURCES = [ RES.TOOLS_ID,
	                      RES.BOARDS_ID,
	                      RES.BRICKS_ID,
	                      RES.FOOD_ID,
	                      RES.TEXTILE_ID,
	                      RES.SALT_ID]

	# order should match the above, else confuses players when in build mode
	CONSTRUCTION_RESOURCES = { # per settler increment
	  0: [ RES.TOOLS_ID, RES.BOARDS_ID ],
	  1: [ RES.TOOLS_ID, RES.BOARDS_ID, RES.BRICKS_ID ],
	  2: [ RES.TOOLS_ID, RES.BOARDS_ID, RES.BRICKS_ID ],
	  3: [ RES.TOOLS_ID, RES.BOARDS_ID, RES.BRICKS_ID ],
	}

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
		self._do_show_dummy = False

		self._update_default_configuration()

	def end(self):
		self.set_inventory_instance( None, force_update=True )
		self.current_instance = weakref.ref(self)
		ExtScheduler().rem_all_classinst_calls(self)
		self.resource_configurations.clear()
		self.gold_gui = None
		self.gui = None
		self._custom_default_resources = None

	def _update_default_configuration(self):
		# user defined variante of DEFAULT_RESOURCES (will be preferred)
		self._custom_default_resources = None
		setting = horizons.main.fife.get_uh_setting("ResourceOverviewBarConfiguration")
		if setting: # parse it if there is something
			config = json.loads(setting)
			if config: # actually use it if it was parseable
				self._custom_default_resources = config

	def save(self, db):
		for obj, config in self.resource_configurations.iteritems():
			for position, res in enumerate(config):
				db("INSERT INTO resource_overview_bar(object, position, resource) VALUES(?, ?, ?)",
				   obj.worldid, position, res)

	def load(self, db):
		from horizons.util import WorldObject
		for obj in db("SELECT DISTINCT object FROM resource_overview_bar"):
			obj = obj[0]
			l = []
			for pos, res in db("SELECT position, resource FROM resource_overview_bar where object=?", obj):
				l.append( (pos, res) )
			obj = WorldObject.get_object_by_id(obj)
			self.resource_configurations[obj] = [ i[1] for i in sorted(l) ]

		# called when any game (also new ones) start
		# register at player inventory for gold updates
		inv = self.session.world.player.get_component(StorageComponent).inventory
		inv.add_change_listener(self._update_gold, call_listener_now=True)
		self.gold_gui.show()
		self._update_gold() # call once more to make pychan happy

		self.set_inventory_instance(None)

	def redraw(self):
		self.set_inventory_instance(self.current_instance(), force_update=True)

	def set_inventory_instance(self, instance, keep_construction_mode=False, force_update=False):
		"""Display different inventory. May change resources that are displayed"""
		if self.current_instance() is instance and not self.construction_mode and not force_update:
			return # caller is drunk yet again
		if self.construction_mode and not keep_construction_mode:
			# stop construction mode, immediately update view, which will be a normal view
			self.close_construction_mode(update_slots=False)

		# reconstruct general gui

		# remove old gui
		for i in self.gui:
			i.hide()
		self._hide_resource_selection_dialog()
		self.gui = []

		inv = self._get_current_inventory()
		if inv is not None:
			inv.remove_change_listener(self._update_resources)

		if instance in (None, self): # show nothing instead
			self.current_instance = weakref.ref(self) # can't weakref to None
			self._do_show_dummy = False # don't save dummy value
			return

		self.current_instance = weakref.ref(instance)

		# construct new slots (fill values later)
		initial_offset = 93
		offset = 52
		resources = self._get_current_resources()
		addition = [-1] if self._do_show_dummy or not resources else [] # add dummy at end for adding stuff
		for i, res in enumerate( resources + addition ):
			entry = load_uh_widget(self.ENTRY_GUI_FILE, style=self.__class__.STYLE)
			entry.findChild(name="entry").position = (initial_offset + offset * i, 17)
			background_icon = entry.findChild(name="background_icon")
			background_icon.add_entered_callback( Callback(self._show_resource_selection_dialog, i) )

			if res != -1:
				helptext = self.session.db.get_res_name(res)
				icon = entry.findChild(name="res_icon")
				icon.num = i
				icon.image = get_res_icon(res)[2] # the 24 one
				icon.capture(self._on_res_slot_click, event_name = 'mouseClicked')
			else:
				helptext = _("Click to add a new slot")
				entry.show() # this will not be filled as the other res
			background_icon.helptext = helptext

			self.gui.append(entry)
			# show it just when values are entered, this appeases pychan

		# fill values
		inv = self._get_current_inventory()
		# update on all changes as well as now
		inv.add_change_listener(self._update_resources, call_listener_now=True)

	def set_construction_mode(self, resource_source_instance, build_costs):
		"""Show resources relevant to construction and build costs
		@param resource_source_instance: object with StorageComponent
		@param build_costs: dict, { res : amount }
		"""
		if resource_source_instance is None:
			# Build moved out of settlement. This is usually not sane and an interaction error.
			# Use this heuristically computed settlement to fix preconditions.
			resource_source_instance = LastActivePlayerSettlementManager().get()
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

		res_list = self._get_current_resources()

		for res, amount in build_costs.iteritems():
			assert res in res_list or res == RES.GOLD_ID

			cost_label = pychan.widgets.Label(text=u"-"+unicode(amount))
			cost_label.stylize( self.__class__.STYLE )
			# add icon below end of background icon
			if res in res_list:
				entry = res_list.index(res)
				cur_gui = self.gui[ entry ]
				reference_icon = cur_gui.findChild(name="background_icon")
				below = reference_icon.size[1]
				cost_icon = pychan.widgets.Icon(image=cost_icon_res,
				                                position=(0, below))
				cost_label.position = (15, below) # TODO: centering
				cur_gui.addChild(cost_icon)
				cur_gui.addChild(cost_label)
				cur_gui.resizeToContent() # container needs to be bigger now
			else: # must be gold
				reference_icon = self.gold_gui.findChild(name="background_icon")
				below = reference_icon.size[1]
				cost_icon = pychan.widgets.Icon(image=cost_icon_gold,
				                              position=(0, below) )
				cost_label.position = (15, below) # TODO: centering
				self.gold_gui.addChild(cost_icon)
				self.gold_gui.addChild(cost_label)
				self.gold_gui.resizeToContent()


	def close_construction_mode(self, update_slots=True):
		"""Return to normal configuration"""
		self.construction_mode = False
		if update_slots:
			self.set_inventory_instance(None)
		self._reset_gold_gui()
		self._update_gold()
		self.gold_gui.show()
		self._update_gold(force=True)

	def _reset_gold_gui(self):
		if self.gold_gui is not None:
			self.gold_gui.hide()
		self.gold_gui = load_uh_widget(self.__class__.GOLD_ENTRY_GUI_FILE, style=self.__class__.STYLE)
		self.gold_gui.child_finder = PychanChildFinder(self.gold_gui)
		# set appropriate icon
		self.gold_gui.findChild(name="res_icon").image = get_res_icon(RES.GOLD_ID)[4] # the 32 one

	def _update_gold(self, force=False):
		"""Changelistener to upate player gold"""
		# can be called pretty often (e.g. if there's an settlement.inventory.alter() in a loop)
		# only update every 0.2 sec at most
		scheduled_attr = "_gold_upate_scheduled"
		if not hasattr(self, scheduled_attr):
			setattr(self, scheduled_attr, True)
			ExtScheduler().add_new_object(Callback(self._update_gold, True), self, run_in=0.02)
			return
		elif not force:
			return # these calls we want to suppress, wait for scheduled call

		delattr(self, scheduled_attr)

		# set gold amount
		gold = self.session.world.player.get_component(StorageComponent).inventory[RES.GOLD_ID]
		gold_available_lbl = self.gold_gui.child_finder("gold_available")
		gold_available_lbl.text = unicode(gold)

		# reposition according to magic forumula passed down from the elders in order to support centering
		self.gold_gui.resizeToContent() # update label size
		gold_available_lbl.position = (33 - gold_available_lbl.size[0]/2,  51)

	def _update_resources(self):
		"""Same as _update_gold but for all other slots"""
		if self.current_instance() in (None, self): # instance died
			self.set_inventory_instance(None)
			return
		inv = self._get_current_inventory()
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
			lvl = self.session.world.player.settler_level
			res_list = self.__class__.CONSTRUCTION_RESOURCES[lvl]
			# also add additional res that might be needed
			res_list += [ res for res in self._last_build_costs if \
			              res not in res_list and res != RES.GOLD_ID ]
			return res_list
		# prefer user defaults over general defaults
		default = self._custom_default_resources if self._custom_default_resources else self.__class__.DEFAULT_RESOURCES
		# prefer specific setting over any defaults
		return self.resource_configurations.get(self.current_instance(), default)

	def _get_current_inventory(self):
		if not (self.current_instance() in (None, self)): # alive and set
			return self.current_instance().get_component(StorageComponent).inventory
		else:
			return None


	###
	# Resource slot selection

	def _show_resource_selection_dialog(self, slot_num):
		"""Shows gui for selecting a resource for slot slot_num"""
		self._hide_resource_selection_dialog()
		inv = self._get_current_inventory()
		if inv is None:
			return

		self._show_dummy_slot()

		# set mousetool to get notified on clicks outside the resbar area
		if not isinstance(self.session.cursor, ResBarMouseTool):
			def on_away_click():
				self._hide_resource_selection_dialog()
				self._hide_dummy_slot()
			self.session.cursor = ResBarMouseTool(self.session, self.session.cursor,
			                                      on_away_click)


		on_click = functools.partial(self._set_resource_slot, slot_num)
		cur_res = self._get_current_resources()
		res_filter = lambda res_id : res_id not in cur_res
		dlg = create_resource_selection_dialog(on_click, inv, self.session.db,
		                                       widget='resbar_resource_selection.xml',
		                                       res_filter=res_filter)

		# position dlg below slot
		cur_gui = self.gui[slot_num]
		background_icon = cur_gui.findChild(name="background_icon")
		dlg.position = (cur_gui.position[0] + background_icon.position[0],
		                cur_gui.position[1] + background_icon.position[1] + background_icon.size[1] )
		dlg.findChild(name="make_default_btn").capture(self._make_configuration_default)
		reset_default_btn = dlg.findChild(name="reset_default_btn")
		# this is a quadruple-use button.
		# If there is no user set default, restore to factory default
		# If the current config is different from user default, set to default
		# If this is the current user set config, remove user set config and fall back to factory default
		# If there is no user set config and the current config is the system default,
		# the button should be disabled, but the first case below is shown because
		# we can't disable it
		if self._custom_default_resources is None:
			reset_default_btn.text = _("Reset to default")
			reset_default_btn.helptext = _("Reset this configuration to the factory default.")
			reset_default_btn.capture(Callback(self._drop_settlement_resource_configuration))

		elif self._custom_default_resources != self._get_current_resources():
			reset_default_btn.text = _("Reset to default")
			reset_default_btn.helptext = _("Reset this settlement's displayed resources to the default configuration you have saved.")
			reset_default_btn.capture(Callback(self._drop_settlement_resource_configuration))

		else:
			reset_default_btn.text = _("Reset to factory")
			reset_default_btn.helptext = _("Reset the default configuration (which you see here) to the factory default for all settlements.")
			cb = Callback.ChainedCallbacks(
			  self._drop_settlement_resource_configuration, # remove specific config
			  Callback(self._make_configuration_default, reset=True) # remove global config
			)
			reset_default_btn.capture( cb )

		dlg.show()
		self._res_selection_dialog = dlg

	def _make_configuration_default(self, reset=False):
		"""Saves current resources as default via game settings"""
		if reset:
			config = [] # meaning invalid
		else:
			config = json.dumps(self._get_current_resources())
		horizons.main.fife.set_uh_setting("ResourceOverviewBarConfiguration", config)
		horizons.main.fife.save_settings()
		self._update_default_configuration()
		AmbientSoundComponent.play_special("success")
		if reset: # in the other case, it's already set
			self.redraw()

	def _drop_settlement_resource_configuration(self):
		"""Forget resource configuration for a settlement"""
		if self.current_instance() in self.resource_configurations:
			del self.resource_configurations[self.current_instance()]
		self.redraw()

	def _set_resource_slot(self, slot_num, res_id):
		"""Show res_id in slot slot_num
		@param slot_num: starting at 0, will be added as new slot if greater than no of slots
		@param res_id: a resource id or 0 for remove slot
		"""
		self._hide_resource_selection_dialog()
		res_copy = self._get_current_resources()[:]
		number_of_slots_changed = False
		if slot_num < len(res_copy): # change existing slot
			if res_id == 0: # remove it
				del res_copy[slot_num]
				number_of_slots_changed = True
			else: # actual slot change
				res_copy[slot_num] = res_id
		else: # addition
			if res_id == 0: # that would mean adding an empty slot
				pass
			else:
				number_of_slots_changed = True
				res_copy += [res_id]

		self.resource_configurations[self.current_instance()] = res_copy

		self.redraw()

		if isinstance(self.session.cursor, ResBarMouseTool):
			self.session.cursor.reset()
			self._hide_dummy_slot()

		if number_of_slots_changed:
			self.session.message_bus.broadcast( ResourceBarResize(self) )

	def _hide_resource_selection_dialog(self):
		if hasattr(self, "_res_selection_dialog"):
			self._res_selection_dialog.hide()
			del self._res_selection_dialog

	def _show_dummy_slot(self):
		"""Show the dummy button at the end to allow for addition of slots"""
		if self._do_show_dummy:
			return # already visible
		self._do_show_dummy = True
		self.redraw()

	def _hide_dummy_slot(self):
		self._do_show_dummy = False
		self.redraw()

	def _on_res_slot_click(self, widget, event):
		"""Called when you click on a resource slot in the bar (not the selection dialog)"""
		if event.getButton() == fife.MouseEvent.RIGHT:
			self._set_resource_slot(widget.num, 0)

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


from horizons.gui.mousetools import NavigationTool
class ResBarMouseTool(NavigationTool):
	"""Temporary mousetool for resource selection.
	Terminates self on mousePressed and restores old tool"""
	def __init__(self, session, old_tool, on_click):
		super(ResBarMouseTool, self).__init__(session)
		if old_tool: # can be None in corner cases
			old_tool.disable()
		self.old_tool = old_tool
		self.on_click = on_click

	def mousePressed(self, evt):
		self.on_click()
		self.reset()

	def reset(self):
		"""Enable old tol again"""
		if self.old_tool:
			self.session.cursor = self.old_tool
		self.remove()
		if self.old_tool:
			self.old_tool.enable()
		else:
			self.session.set_cursor()
