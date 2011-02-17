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
import math

from fife.extensions import pychan

from horizons.command.production import AddProduction
from horizons.gui.widgets  import TooltipButton
from horizons.gui.tabs import OverviewTab
from horizons.i18n import load_xml_translated
from horizons.util import Callback

class BoatbuilderTab(OverviewTab):
	def __init__(self, instance):
		super(BoatbuilderTab, self).__init__(
			widget = 'boatbuilder.xml',
			instance = instance
		)
		self.tooltip = _("Boat builder overview")

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		super(BoatbuilderTab, self).refresh()
		progress = self.instance.get_production_progress()
		self.widget.findChild(name='progress').progress = progress*100
		self.widget.findChild(name='BB_progress_perc').text = unicode(math.floor(progress*100))+u"%"

		main_container = self.widget.findChild(name="BB_main_tab")
		container_active = self.widget.findChild(name="container_active")
		container_inactive = self.widget.findChild(name="container_inactive")
		progress_container = main_container.findChild(name="BB_progress_container")

		# a boatbuilder is considered active here, if he build sth, no matter if it's paused
		if self.instance.get_production_lines():
			# TODO: fill in actual values here

			# remove other container, but save it
			if container_inactive is not None:
				main_container.container_inactive = container_inactive
				main_container.removeChild( container_inactive )
			if container_active is None:
				main_container.insertChildBefore( main_container.container_active, progress_container)
				container_active = main_container.container_active
			container_active.findChild(name="BB_builtship_label").text = u"Fishing boat"
			container_active.findChild(name="BB_cur_ship_icon").tooltip = "Used by: Fisher\nStorage: 1 slot of 1t\nSpeed: average\nHealth: 40"

			button_active = container_active.findChild(name="toggle_active_active")
			button_inactive = container_active.findChild(name="toggle_active_inactive")

			if not self.instance.is_active(): # if production is paused
				# remove active button, if it's there, and save a reference to it
				if button_active is not None:
					container_active.button_active = button_active
					container_active.removeChild( button_active )
				# restore inactive button, if it isn't in the gui
				if button_inactive is None:
					# insert at the end
					container_active.insertChild(container_active.button_inactive, \
					                             len(container_active.children))
				container_active.mapEvents({
				  'toggle_active_inactive' : Callback(self.instance.set_active, active=True)
				})
				# TODO: make this button do sth
			else:
				# remove inactive button, if it's there, and save a reference to it
				if button_inactive is not None:
					container_active.button_inactive = button_inactive
					container_active.removeChild( button_inactive )
				# restore active button, if it isn't in the gui
				if button_active is None:
					# insert at the end
					container_active.insertChild(container_active.button_active, \
					                             len(container_active.children))

				container_active.mapEvents({
				  'toggle_active_active' : Callback(self.instance.set_active, active=False)
				})
			upgrades_box = container_active.findChild(name="BB_upgrades_box")
			for child in upgrades_box.children[:]:
				upgrades_box.removeChild(child)
#			upgrades_box.addChild( pychan.widgets.Label(text=u"+ love") )
#			upgrades_box.addChild( pychan.widgets.Label(text=u"+ affection") )
# no upgrades in 2010.1 release ---^
			upgrades_box.stylize('menu_black')

				# TODO: make this button do sth
			container_active.findChild(name='BB_builtship_label').stylize("headline")

			# Update needed resources
			production = self.instance._productions.values()[0]
			still_needed_res = production.get_consumed_resources()
			i = 1
			needed_res_container = self.widget.findChild(name="BB_needed_resources_container")
			main_container.findChild(name="BB_needed_res_label").text = _('Resources still needed:')
			for res, amount in still_needed_res.iteritems():
				assert i <= 3, "Only 3 still needed res for ships are currently supported"

				icon = self.instance.session.db("SELECT icon_small FROM resource WHERE id = ?", res)[0][0]
				needed_res_container.findChild(name="BB_needed_res_icon_"+str(i)).image = icon
				needed_res_container.findChild(name="BB_needed_res_lbl_"+str(i)).text = unicode(-1*amount)+u't' # -1 make them positive
				i += 1

			# TODO: cancel building button
	#		print "Cancelbutton search.."
			cancel_button = self.widget.findChild(name="BB_cancel_button")
	#		print "Found:", cancel_button
			cancel_button.capture(self.instance.cancel_all_productions, event_name="mouseClicked")
	#		print cancel_button.isCaptured()

		else: # display sth when nothing is produced
			# remove other container, but save it
			if container_active is not None:
				main_container.container_active = container_active
				main_container.removeChild( container_active )
			if container_inactive is None:
				main_container.insertChildBefore( main_container.container_inactive, progress_container)
				container_inactive = main_container.container_inactive


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
		super(BoatbuilderSelectTab, self).__init__(instance, widget = 'boatbuilder_' + str(tabname) + '.xml')
		self.init_values()
		bb_image_path = 'content/gui/icons/tabwidget/boatbuilder/'+str(tabname)+'_%s.png'
		self.button_up_image = bb_image_path % 'u'
		self.button_active_image = bb_image_path % 'a'
		self.button_down_image = bb_image_path % 'd'
		self.button_hover_image = bb_image_path % 'h'
		for i in xrange(1,5): # xml names start at 1.  v--- ship names in small caps
			self.widget.findChild(name='BB_'+str(tabname)+'_ship'+str(i)).stylize('headline')
	def start_production(self, prod_line_id):
		AddProduction(self.instance, prod_line_id).execute(self.instance.session)
		# show overview tab
		self.instance.session.ingame_gui.get_cur_menu()._show_tab(0)

class BoatbuilderFisherTab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderFisherTab, self).__init__(instance, 'fisher')
		self.tooltip = _("Fisher boats")
		# TODO: generalize this hard coded value
		events = { 'BB_build_fisher_1' : Callback(self.start_production, 15) }
		self.widget.mapEvents(events)

class BoatbuilderTradeTab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderTradeTab, self).__init__(instance, 'trade')
		self.tooltip = _("Trade boats")

class BoatbuilderWar1Tab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderWar1Tab, self).__init__(instance, 'war1')
		self.tooltip = _("War boats")

class BoatbuilderWar2Tab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderWar2Tab, self).__init__(instance, 'war2')
		self.tooltip = _("War ships")

# these tabs additionally request functions for:
# * goto: show [confirm view] tab (not accessible via tab button in the end)
#	need to provide information about the selected ship (which of the 4 buttons clicked)
# * check: mark those ship's buttons as unbuildable (close graphics) which do not meet the specified requirements.
#	the tooltips contain this info as well.

class BoatbuilderConfirmTab(OverviewTab):

	def __init__(self, instance):
		super(BoatbuilderConfirmTab, self).__init__(
			widget = 'boatbuilder_confirm.xml',
			instance = instance
		)
		events = { 'create_unit': self.start_production }
		self.widget.mapEvents(events)
		self.tooltip = _("Confirm order")
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
