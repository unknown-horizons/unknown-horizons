# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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
import math

from fife.extensions import pychan

import horizons.main

from tabinterface import TabInterface
from horizons.command.production import AddProduction
from horizons.gui.widgets  import TooltipButton
from horizons.gui.tabs import OverviewTab
from horizons.i18n import load_xml_translated

class BoatbuilderTab(OverviewTab):
	def __init__(self, instance):
		super(BoatbuilderTab, self).__init__(
			widget = 'tab_widget/boatbuilder/boatbuilder.xml',
			instance = instance
		)
		self.tooltip = u"Boat Builder \\n Overview"

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		super(BoatbuilderTab, self).refresh()
		progress = self.instance.get_production_progress()
		self.widget.findChild(name='progress').progress = progress*100
		self.widget.findChild(name='BB_progress_perc').text = unicode(math.floor(progress*100))+u"%"

		main_container = self.widget.findChild(name="BB_main_tab")
		container_active = self.widget.findChild(name="container_active")
		container_inactive = self.widget.findChild(name="container_inactive")
		if self.instance.is_active() or True: # debug cond
			# TODO: fill in acctual values here
			main_container.removeChild( container_inactive )
			container_active.findChild(name="BB_builtship_label").text = u"Loveboat"
			container_active.findChild(name="BB_cur_ship_icon").tooltip = "$NAME $CLASS $COST"

			if True: # if production is paused
				container_active.removeChild( \
					container_active.findChild(name="toggle_active_active") \
				)
				# TODO: make this button do sth
			else:
				container_active.removeChild( \
					container_active.findChild(name="toggle_active_inactive") \
				)
				# TODO: make this button do sth

			upgrades_box = container_active.findChild(name="BB_upgrades_box")
			upgrades_box.addChild( pychan.widgets.Label(text=u"+ love") )
			upgrades_box.addChild( pychan.widgets.Label(text=u"+ affection") )
			upgrades_box.stylize('menu_black')

			container_active.findChild(name='BB_builtship_label').stylize("headline")

			still_needed_res = {  3: 5, 4 : 42 }
			i = 1
			needed_res_container = self.widget.findChild(name="BB_needed_resources_container")
			main_container.findChild(name="BB_needed_res_label").text = _(u'Resources still needed:')
			for res, amount in still_needed_res.iteritems():
				assert i <= 3, "Only 3 still needed res for ships are currently supported"

				icon = self.instance.session.db("SELECT icon_small FROM resource WHERE id = ?", res)[0][0]
				needed_res_container.findChild(name="BB_needed_res_icon_"+str(i)).image = icon
				needed_res_container.findChild(name="BB_needed_res_lbl_"+str(i)).text = unicode(amount)+u't'
				i += 1

			# TODO: cancel building button

		else: # display sth when nothing is produced
			main_container.removeChild( container_active )
			main_container.findChild(name="BB_needed_res_label").text = u''

		self.widget.adaptLayout()

# this tab additionally requests functions for:
# * decide: show [start view] = nothing but info text, look up the xml, or [building status view]
# * get: currently built ship: name / image / upgrades
# * resources still needed:
#	(a) which ones? three most important (image, name)
#	(b) how many? sort by amount, display (amount, overall amount needed of them, image)
# * pause production (keep order and "running" running costs [...] but collect no new resources)
# * abort building process: delete task, remove all resources, display [start view] again

class BoatbuilderSelectTab(OverviewTab):

	def __init__(self, instance, tabname):
		super(BoatbuilderSelectTab, self).__init__(instance, widget = 'tab_widget/boatbuilder/' + str(tabname) + '.xml')
		self.init_values()
		self.button_up_image = 'content/gui/images/icons/hud/common/bb/%s_u.png' % tabname
		self.button_active_image = 'content/gui/images/icons/hud/common/bb/%s_a.png' % tabname
		self.button_down_image = 'content/gui/images/icons/hud/common/bb/%s_d.png' % tabname
		self.button_hover_image = 'content/gui/images/icons/hud/common/bb/%s_h.png' % tabname

class BoatbuilderFisherTab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderFisherTab, self).__init__(instance, 'fisher')
		self.tooltip = "Fisher Boats"

class BoatbuilderTradeTab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderTradeTab, self).__init__(instance, 'trade')
		self.tooltip = "Trade Boats"

class BoatbuilderWar1Tab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderWar1Tab, self).__init__(instance, 'war1')
		self.tooltip = "War Boats"

class BoatbuilderWar2Tab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderWar2Tab, self).__init__(instance, 'war2')
		self.tooltip = "War Ships"

# these tabs additionally request functions for:
# * goto: show [confirm view] tab (not accessible via tab button in the end)
#	need to provide information about the selected ship (which of the 4 buttons clicked)
# * check: mark those ship's buttons as unbuildable (close graphics) which do not meet the specified requirements.
#	the tooltips contain this info as well.

class BoatbuilderConfirmTab(OverviewTab):

	def __init__(self, instance):
		super(BoatbuilderConfirmTab, self).__init__(
			widget = 'tab_widget/boatbuilder/confirm.xml',
			instance = instance
		)
		events = { 'create_unit': self.start_production }
		self.widget.mapEvents(events)
		self.tooltip = u"Confirm order"
		self.widget.findChild(name='BB_builtship_label').stylize("headline")
		self.widget.findChild(name='headline_upgrades').stylize("headline")

	def start_production(self):
		AddProduction(self.instance, 15).execute(self.instance.session)

# this "tab" additionally requests functions for:
# * get: currently ordered ship: name / image / type (fisher/trade/war)
# * => get: currently ordered ship: description text / costs / available upgrades
#						(fisher/trade/war, builder level)
# * if resource icons not hardcoded: resource icons, sort them by amount
# UPGRADES: * checkboxes * check for boat builder level (+ research) * add. costs (get, add, display)
# * def start_production(self):  <<< actually start to produce the selected ship unit with the selected upgrades
#	(use inventory or go collect resources, switch focus to overview tab).
#	IMPORTANT: lock this button until unit is actually produced (no queue!)
