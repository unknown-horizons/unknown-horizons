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
import itertools
import functools

import horizons.main

from horizons.constants import TIER, RES
from horizons.component.storagecomponent import StorageComponent
from horizons.gui.util import load_uh_widget, get_res_icon_path, create_resource_selection_dialog
from horizons.util import PychanChildFinder, Callback
from horizons.util.python.decorators import cachedmethod
from horizons.extscheduler import ExtScheduler
from horizons.component.ambientsoundcomponent import AmbientSoundComponent
from horizons.util.lastactiveplayersettlementmanager import LastActivePlayerSettlementManager
from horizons.messaging import NewPlayerSettlementHovered, ResourceBarResize, TabWidgetChanged
from horizons.world.player import Player


class ResourceOverviewBar(object):
	"""The thing on the top left.

	http://wiki.unknown-horizons.org/w/HUD

	Features:
	- display contents of currently relevant inventory (settlement/ship)
	- always show gold of local player
	- show costs of current build
	- configure the resources to show
		- per settlement
		- add new slots
		- switch displayed resources to construction relevant res on build
		- res selection consistent with other res selection dlgs

	Invariants:
	- it should be obvious that the res bar can be configured
	- it should be obvious that the res bar can be set per settlement

	Has distinguished treatment of gold because it's distinguished by a bigger icon
	and by being shown always.
	"""

	GOLD_ENTRY_GUI_FILE = "resource_overview_bar_gold.xml"
	ENTRY_GUI_FILE = "resource_overview_bar_entry.xml"

	STATS_GUI_FILE = "resource_overview_bar_stats.xml"

	STYLE = "resource_bar"

	DEFAULT_RESOURCES = [ RES.TOOLS,
	                      RES.BOARDS,
	                      RES.BRICKS,
	                      RES.FOOD,
	                      RES.TEXTILE,
	                      RES.SALT]

	# order should match the above, else confuses players when in build mode
	CONSTRUCTION_RESOURCES = { # per inhabitant tier
	  TIER.SAILORS:  [ RES.TOOLS, RES.BOARDS ],
	  TIER.PIONEERS: [ RES.TOOLS, RES.BOARDS, RES.BRICKS ],
	  TIER.SETTLERS: [ RES.TOOLS, RES.BOARDS, RES.BRICKS ],
	  TIER.CITIZENS: [ RES.TOOLS, RES.BOARDS, RES.BRICKS ],
	}

	def __init__(self, session):
		from horizons.session import Session
		assert isinstance(session, Session)
		self.session = session

		# special slot because of special properties
		self.gold_gui = load_uh_widget(self.__class__.GOLD_ENTRY_GUI_FILE, style=self.__class__.STYLE)
		self.gold_gui.balance_visible = False
		self.gold_gui.child_finder = PychanChildFinder(self.gold_gui)
		gold_icon = self.gold_gui.child_finder("res_icon")
		gold_icon.image = get_res_icon_path(RES.GOLD)
		gold_icon.max_size = gold_icon.min_size = gold_icon.size = (32, 32)
		self.gold_gui.mapEvents({
		  "resbar_gold_container/mouseClicked/stats" : self._toggle_stats,
		  })
		self.gold_gui.helptext = _("Click to show statistics")
		self.stats_gui = None

		self.gui = [] # list of slots
		self.resource_configurations = weakref.WeakKeyDictionary()
		self.current_instance = weakref.ref(self) # can't weakref to None
		self.construction_mode = False
		self._last_build_costs = None
		self._do_show_dummy = False

		self._update_default_configuration()

		NewPlayerSettlementHovered.subscribe(self._on_different_settlement)
		TabWidgetChanged.subscribe(self._on_tab_widget_changed)

		# set now and then every few sec
		ExtScheduler().add_new_object(self._update_balance_display, self, run_in=0)
		ExtScheduler().add_new_object(self._update_balance_display, self, run_in=Player.STATS_UPDATE_INTERVAL, loops=-1)

	def end(self):
		self.set_inventory_instance( None, force_update=True )
		self.current_instance = weakref.ref(self)
		ExtScheduler().rem_all_classinst_calls(self)
		self.resource_configurations.clear()
		self.gold_gui = None
		self.gui = None
		self._custom_default_resources = None
		NewPlayerSettlementHovered.unsubscribe(self._on_different_settlement)
		TabWidgetChanged.unsubscribe(self._on_tab_widget_changed)

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

		self.set_inventory_instance(
		  LastActivePlayerSettlementManager().get(get_current_pos=True))

	def redraw(self):
		self.set_inventory_instance(self.current_instance(), force_update=True)

	def _on_different_settlement(self, message):
		self.set_inventory_instance(message.settlement)

	def set_inventory_instance(self, instance, keep_construction_mode=False, force_update=False):
		"""Display different inventory. May change resources that are displayed"""
		if self.current_instance() is instance and not self.construction_mode and not force_update:
			return # caller is drunk yet again
		if self.construction_mode and not keep_construction_mode:
			# stop construction mode, immediately update view, which will be a normal view
			self.close_construction_mode(update_slots=False)

		# reconstruct general gui

		# remove old gui (keep entries for reuse)
		for i in self.gui:
			i.hide()
		self._hide_resource_selection_dialog()

		inv = self._get_current_inventory()
		if inv is not None:
			inv.remove_change_listener(self._update_resources)

		if instance in (None, self): # show nothing instead
			self.current_instance = weakref.ref(self) # can't weakref to None
			self._do_show_dummy = False # don't save dummy value
			return

		self.current_instance = weakref.ref(instance)

		# construct new slots (fill values later)
		load_entry = lambda : load_uh_widget(self.ENTRY_GUI_FILE, style=self.__class__.STYLE)
		initial_offset = 101
		offset = 52
		resources = self._get_current_resources()
		addition = [-1] if self._do_show_dummy or not resources else [] # add dummy at end for adding stuff
		for i, res in enumerate( resources + addition ):
			try: # get old slot
				entry = self.gui[i]
				if res == -1: # can't reuse dummy slot, need default data
					self.gui[i] = entry = load_entry()
			except IndexError: # need new one
				entry = load_entry()
				self.gui.append(entry)

			entry.findChild(name="entry").position = (initial_offset + offset * i, 17)
			background_icon = entry.findChild(name="entry")
			background_icon.capture(Callback(self._show_resource_selection_dialog, i), 'mouseEntered', 'resbar')

			if res != -1:
				helptext = self.session.db.get_res_name(res)
				icon = entry.findChild(name="res_icon")
				icon.num = i
				icon.image = get_res_icon_path(res)
				icon.max_size = icon.min_size = icon.size = (24, 24)
				icon.capture(self._on_res_slot_click, event_name='mouseClicked')
			else:
				helptext = _("Click to add a new slot")
				entry.show() # this will not be filled as the other res
			background_icon.helptext = helptext

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
		cost_icon_gold = "content/gui/images/background/widgets/resbar_stats_bottom.png"
		cost_icon_res = "content/gui/images/background/widgets/res_extra_bg.png"

		res_list = self._get_current_resources()

		# remove old one before, avoids duplicates
		self._drop_cost_labels()

		for res, amount in build_costs.iteritems():
			assert res in res_list or res == RES.GOLD

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
				cur_gui.cost_gui = [cost_label, cost_icon]

				cur_gui.resizeToContent() # container needs to be bigger now
			else: # must be gold
				# there is an icon with scales there, use its positioning
				reference_icon = self.gold_gui.child_finder("balance_background")
				cost_icon = pychan.widgets.Icon(image=cost_icon_gold,
				                              position=(reference_icon.x, reference_icon.y))
				cost_label.position = (23, 74) # TODO: centering

				self.gold_gui.addChild(cost_icon)
				self.gold_gui.addChild(cost_label)
				self.gold_gui.cost_gui = [cost_label, cost_icon]

				self.gold_gui.resizeToContent()

	def close_construction_mode(self, update_slots=True):
		"""Return to normal configuration"""
		self.construction_mode = False
		if update_slots: # cleanup
			self._drop_cost_labels()
			self.set_inventory_instance(None)
		#self._update_gold()
		self.gold_gui.show()
		self._update_gold(force=True)

		# reshow last settlement
		self.set_inventory_instance( LastActivePlayerSettlementManager().get(get_current_pos=True) )

	def _drop_cost_labels(self):
		"""Removes all labels below the slots indicating building costs"""
		for entry in itertools.chain(self.gui, [self.gold_gui]):
			if hasattr(entry, "cost_gui"): # get rid of possible cost labels
				for elem in entry.cost_gui:
					entry.removeChild(elem)
				del entry.cost_gui

	def _update_gold(self, force=False):
		"""Changelistener to upate player gold"""
		# can be called pretty often (e.g. if there's an settlement.inventory.alter() in a loop)
		# only update every 0.3 sec at most
		scheduled_attr = "_gold_upate_scheduled"
		if not hasattr(self, scheduled_attr):
			setattr(self, scheduled_attr, True)
			ExtScheduler().add_new_object(Callback(self._update_gold, force=True), self, run_in=0.3)
			return
		elif not force:
			return # these calls we want to suppress, wait for scheduled call

		delattr(self, scheduled_attr)

		# set gold amount
		gold = self.session.world.player.get_component(StorageComponent).inventory[RES.GOLD]
		gold_available_lbl = self.gold_gui.child_finder("gold_available")
		gold_available_lbl.text = unicode(gold)
		# reposition according to magic forumula passed down from the elders in order to support centering
		gold_available_lbl.resizeToContent() # this sets new size values
		gold_available_lbl.position = (42 - gold_available_lbl.size[0]/2,  51)

		self.gold_gui.resizeToContent() # update label size

	def _update_balance_display(self):
		"""Updates balance info below gold icon"""
		balance = self.session.world.player.get_balance_estimation()
		balance_lbl = self.gold_gui.child_finder("balance")
		balance_lbl.text = u"{sign}{balance}".format(balance=balance, sign=u'+' if balance >= 0 else u'')
		balance_lbl.resizeToContent()
		# 38
		balance_lbl.position = (70 - balance_lbl.size[0],  74) # see _update_gold

		self.gold_gui.resizeToContent() # update label size

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
			cur_gui.adaptLayout() # update size values (e.g. if amount of digits changed)
			cur_gui.show()
			label.position = (24 - label.size[0]/2, 44)

	def _get_current_resources(self):
		"""Return list of resources to display now"""
		if self.construction_mode:
			lvl = self.session.world.player.settler_level
			res_list = self.__class__.CONSTRUCTION_RESOURCES[lvl]
			# also add additional res that might be needed
			res_list += [ res for res in self._last_build_costs if
			              res not in res_list and res != RES.GOLD ]
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
			self.session.cursor = ResBarMouseTool(self.session, self.session.cursor,
			                                      self.close_resource_selection_mode)


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
		self.close_construction_mode()
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

		if number_of_slots_changed:
			ResourceBarResize.broadcast(self)

	def _hide_resource_selection_dialog(self):
		if hasattr(self, "_res_selection_dialog"):
			self._res_selection_dialog.hide()
			del self._res_selection_dialog

	def close_resource_selection_mode(self):
		"""Fully disable resource selection mode"""
		self._hide_resource_selection_dialog()
		self._hide_dummy_slot()

	def _on_tab_widget_changed(self, msg=None):
		if hasattr(self, "_res_selection_dialog"):
			self.close_resource_selection_mode()

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

	def _toggle_stats(self):
		if self.stats_gui is None or not self.stats_gui.isVisible():
			self._show_stats()
		else:
			self._hide_stats()

	def _show_stats(self):
		"""Show data below gold icon when balance label is clicked"""
		if self.stats_gui is None:
			reference_icon = self.gold_gui.child_finder("balance_background")
			self.stats_gui = load_uh_widget( self.__class__.STATS_GUI_FILE )
			self.stats_gui.child_finder = PychanChildFinder(self.stats_gui)
			self.stats_gui.position = (reference_icon.x + self.gold_gui.x,
			                           reference_icon.y + self.gold_gui.y)
			self.stats_gui.mapEvents({
			  'resbar_stats_container/mouseClicked/stats' : self._toggle_stats
			  })

			images = [ # these must correspond to the entries in _update_stats
				"content/gui/images/resbar_stats/gold_icon.png",
				"content/gui/images/resbar_stats/tools_icon.png",
				"content/gui/images/resbar_stats/tools_icon.png",
				"content/gui/images/resbar_stats/tools_icon.png",
				"content/gui/images/resbar_stats/scales_icon.png",
			  ]

			for num, image in enumerate(images):
				# keep in sync with comment there until we can use that data:
				# ./content/gui/xml/ingame/hud/resource_overview_bar_stats.xml
				box = pychan.widgets.HBox(padding=0, min_size=(70,0), name="resbar_stats_line_%s"%num)
				box.addChild( pychan.widgets.Icon(image=image) )
				box.addSpacer( pychan.widgets.Spacer() )
				box.addChild( pychan.widgets.Label(name="resbar_stats_entry_%s"%num) )
				# workaround for fife font bug, probably http://fife.trac.cvsdude.com/engine/ticket/666
				box.addChild( pychan.widgets.Label(text=u" ") )

				if num < len(images)-1: # regular one
					self.stats_gui.child_finder("entries_box").addChild(box)
				else: # last one
					self.stats_gui.child_finder("bottom_box").addChild(box)

		self._update_stats()
		self.stats_gui.show()

		ExtScheduler().add_new_object(self._update_stats, self, run_in=Player.STATS_UPDATE_INTERVAL, loops=-1)

	def _update_stats(self):
		# fill in valies of stats, must correspond to images in _show_stats
		format_display = lambda x : (u"+" if x >= 0 else u"") + unicode(x)
		data = self.session.world.player.get_statistics()
		# TODO: mark as expense
		self.stats_gui.child_finder("resbar_stats_line_0").helptext = _("Running costs")
		self.stats_gui.child_finder("resbar_stats_entry_0").text = format_display(-data.running_costs)

		# TODO: mark as income
		self.stats_gui.child_finder("resbar_stats_line_1").helptext = _("Taxes")
		self.stats_gui.child_finder("resbar_stats_entry_1").text = format_display(data.taxes)

		# TODO: mark as expense
		self.stats_gui.child_finder("resbar_stats_line_2").helptext = _("Buy expenses")
		self.stats_gui.child_finder("resbar_stats_entry_2").text = format_display(-data.buy_expenses)

		# TODO: mark as income
		self.stats_gui.child_finder("resbar_stats_line_3").helptext = _("Sell income")
		self.stats_gui.child_finder("resbar_stats_entry_3").text = format_display(data.sell_income)


		self.stats_gui.child_finder("resbar_stats_line_4").helptext = _("Balance")
		self.stats_gui.child_finder("resbar_stats_entry_4").text = format_display(data.balance)


	def _hide_stats(self):
		"""Inverse of show_stats"""
		ExtScheduler().rem_call(self, self._update_stats)
		if self.stats_gui is not None:
			self.stats_gui.hide()

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
		# this click should still count, especially in case the res
		# selection dialog has been closed by other means than clicking
		self.session.cursor.mousePressed(evt)

	def reset(self):
		"""Enable old tool again"""
		if self.old_tool:
			self.session.cursor = self.old_tool
		self.remove()
		if self.old_tool:
			self.old_tool.enable()
		else:
			self.session.set_cursor()
