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

import math
import operator

from horizons.command.production import AddProduction, RemoveFromQueue, CancelCurrentProduction
from horizons.gui.tabs import OverviewTab
from horizons.util.gui import get_res_icon
from horizons.util import Callback
from horizons.constants import PRODUCTIONLINES
from horizons.world.production.producer import Producer
from fife.extensions.pychan.widgets import Icon

class _BoatbuilderOverviewTab(OverviewTab):
	"""Private class all classes here inherit."""
	@property
	def producer(self):
		"""Abstract the instance, work only on components"""
		return self.instance.get_component(Producer)


class BoatbuilderTab(_BoatbuilderOverviewTab):

	SHIP_THUMBNAIL = "content/gui/icons/unit_thumbnails/{type_id}.png"

	def __init__(self, instance):
		super(BoatbuilderTab, self).__init__(
			widget = 'boatbuilder.xml',
			instance = instance
		)
		self.helptext = _("Boat builder overview")

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		super(BoatbuilderTab, self).refresh()

		main_container = self.widget.findChild(name="BB_main_tab")
		container_active = main_container.findChild(name="container_active")
		container_inactive = main_container.findChild(name="container_inactive")
		progress_container = main_container.findChild(name="BB_progress_container")
		cancel_container = main_container.findChild(name="BB_cancel_container")
		needed_res_container = self.widget.findChild(name="BB_needed_resources_container")

		# a boatbuilder is considered active here if it build sth, no matter if it's paused
		production_lines = self.producer.get_production_lines()

		if production_lines:

			if cancel_container is None:
				main_container.addChild(main_container.cancel_container)
				cancel_container = main_container.cancel_container

			if needed_res_container is None:
				main_container.insertChildBefore(main_container.needed_res_container, cancel_container)
				needed_res_container = main_container.needed_res_container

			# Set progress
			if progress_container is None:
				main_container.insertChildBefore( main_container.progress_container, self.widget.findChild(name="BB_needed_resources_container"))
				progress_container = main_container.progress_container

			progress = self.producer.get_production_progress()
			self.widget.findChild(name='progress').progress = progress*100
			self.widget.findChild(name='BB_progress_perc').text = unicode(math.floor(progress*100))+u"%"

			# remove other container, but save it
			if container_inactive is not None:
				main_container.container_inactive = container_inactive
				main_container.removeChild( container_inactive )
			if container_active is None:
				main_container.insertChildBefore( main_container.container_active, progress_container)
				container_active = main_container.container_active

			# Update boatbuilder queue
			queue = self.producer.get_unit_production_queue()
			queue_container = container_active.findChild(name="queue_container")
			queue_container.removeAllChildren()
			for i in enumerate(queue):
				place_in_queue, unit_type = i
				image = self.__class__.SHIP_THUMBNAIL.format(type_id=unit_type)
				#xgettext:python-format
				helptext = _(u"{ship} (place in queue: {place})").format(
				               ship=self.instance.session.db.get_unit_type_name(unit_type),
				               place=place_in_queue+1 )
				# people don't count properly, always starting at 1..
				icon_name = "queue_elem_"+str(place_in_queue)
				icon = Icon(name=icon_name, image=image, helptext=helptext)
				icon.capture(
				  Callback(RemoveFromQueue(self.producer, place_in_queue).execute, self.instance.session),
				  event_name="mouseClicked"
				)
				queue_container.addChild( icon )

			# Set built ship info
			produced_unit_id = self.producer._get_production(production_lines[0]).get_produced_units().keys()[0]
			produced_unit_id = self.producer._get_production(production_lines[0]).get_produced_units().keys()[0]
			(name,) = self.instance.session.db.cached_query("SELECT name FROM unit WHERE id = ?", produced_unit_id)[0]
			container_active.findChild(name="headline_BB_builtship_label").text = _(name)
			container_active.findChild(name="BB_cur_ship_icon").helptext = "Storage: 4 slots, 120t \nHealth: 100"
			container_active.findChild(name="BB_cur_ship_icon").image = "content/gui/images/objects/ships/116/%s.png" % (produced_unit_id)

			button_active = container_active.findChild(name="toggle_active_active")
			button_inactive = container_active.findChild(name="toggle_active_inactive")

			if not self.producer.is_active(): # if production is paused
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
				  'toggle_active_inactive' : Callback(self.producer.set_active, active=True)
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
				  'toggle_active_active' : Callback(self.producer.set_active, active=False)
				})
			upgrades_box = container_active.findChild(name="BB_upgrades_box")
			for child in upgrades_box.children[:]:
				upgrades_box.removeChild(child)
#			upgrades_box.addChild( pychan.widgets.Label(text=u"+ love") )
#			upgrades_box.addChild( pychan.widgets.Label(text=u"+ affection") )
# no upgrades in 2010.1 release ---^
			upgrades_box.stylize('menu_black')

			# Update needed resources
			production = self.producer.get_productions()[0]
			still_needed_res = production.get_consumed_resources()
			# Now sort!
			still_needed_res = sorted(still_needed_res.iteritems(), key=operator.itemgetter(1))
			main_container.findChild(name="BB_needed_res_label").text = _('Resources still needed:')
			i = 0
			for res, amount in still_needed_res:
				if amount == 0:
					continue # Don't show res that are not really needed anymore
				assert i <= 3, "Only 3 still needed res for ships are currently supported"

				icon = get_res_icon(res)[3]
				needed_res_container.findChild(name="BB_needed_res_icon_"+str(i+1)).image = icon
				needed_res_container.findChild(name="BB_needed_res_lbl_"+str(i+1)).text = unicode(-1*amount)+u't' # -1 makes them positive
				i += 1
				if i >= 3:
					break
			for j in xrange(i, 3):
				# these are not filled by a resource, so we need to make it invisible
				needed_res_container.findChild(name="BB_needed_res_icon_"+str(j+1)).image = None
				needed_res_container.findChild(name="BB_needed_res_lbl_"+str(j+1)).text = u""

			cancel_button = self.widget.findChild(name="BB_cancel_button")
			cancel_button.capture(
			  Callback(CancelCurrentProduction(self.producer).execute, self.instance.session),
			  event_name="mouseClicked"
			)

		else: # display sth when nothing is produced
			# remove other container, but save it
			if container_active is not None:
				main_container.container_active = container_active
				main_container.removeChild( container_active )
			if container_inactive is None:
				main_container.insertChildBefore( main_container.container_inactive, progress_container)
				container_inactive = main_container.container_inactive

			if progress_container is not None:
				main_container.progress_container = progress_container
				main_container.removeChild(progress_container)

			if needed_res_container is not None:
				main_container.needed_res_container = needed_res_container
				main_container.removeChild(needed_res_container)

			if cancel_container is not None:
				main_container.cancel_container = cancel_container
				main_container.removeChild(cancel_container)


		self.widget.adaptLayout()

# this tab additionally requests functions for:
# * decide: show [start view] = nothing but info text, look up the xml, or [building status view]
# * get: currently built ship: name / image / upgrades
# * resources still needed:
#	(a) which ones? three most important (image, name)
#	(b) how many? sort by amount, display (amount, overall amount needed of them, image)
# * pause production (keep order and "running" running costs [...] but collect no new resources)
# * abort building process: delete task, remove all resources, display [start view] again

class BoatbuilderSelectTab(_BoatbuilderOverviewTab):

	def __init__(self, instance, tabname):
		super(BoatbuilderSelectTab, self).__init__(instance=instance, widget = 'boatbuilder_' + str(tabname) + '.xml')
		self.init_values()
		bb_image_path = 'content/gui/icons/tabwidget/boatbuilder/'+str(tabname)+'_%s.png'
		self.button_up_image = bb_image_path % 'u'
		self.button_active_image = bb_image_path % 'a'
		self.button_down_image = bb_image_path % 'd'
		self.button_hover_image = bb_image_path % 'h'

	def start_production(self, prod_line_id):
		AddProduction(self.producer, prod_line_id).execute(self.instance.session)
		# show overview tab
		self.instance.session.ingame_gui.get_cur_menu()._show_tab(0)

class BoatbuilderFisherTab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderFisherTab, self).__init__(instance, 'fisher')
		self.helptext = _("Fisher boats")
		# TODO: generalize this hard coded value
		events = { 'BB_build_fisher_1' : Callback(self.start_production, PRODUCTIONLINES.FISHING_BOAT) }
		self.widget.mapEvents(events)

class BoatbuilderTradeTab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderTradeTab, self).__init__(instance, 'trade')
		events = { 'BB_build_trade_1' : Callback(self.start_production, PRODUCTIONLINES.HUKER) }
		self.helptext = _("Trade boats")
		self.widget.mapEvents(events)

class BoatbuilderWar1Tab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderWar1Tab, self).__init__(instance, 'war1')
		events = { 'BB_build_war1_1' : Callback(self.start_production, PRODUCTIONLINES.FRIGATE) }
		self.helptext = _("War boats")
		self.widget.mapEvents(events)

class BoatbuilderWar2Tab(BoatbuilderSelectTab):

	def __init__(self, instance):
		super(BoatbuilderWar2Tab, self).__init__(instance, 'war2')
		self.helptext = _("War ships")

# these tabs additionally request functions for:
# * goto: show [confirm view] tab (not accessible via tab button in the end)
#	need to provide information about the selected ship (which of the 4 buttons clicked)
# * check: mark those ship's buttons as unbuildable (close graphics) which do not meet the specified requirements.
#	the tooltips contain this info as well.

class BoatbuilderConfirmTab(_BoatbuilderOverviewTab):

	def __init__(self, instance):
		super(BoatbuilderConfirmTab, self).__init__(
			widget = 'boatbuilder_confirm.xml',
			instance = instance
		)
		events = { 'create_unit': self.start_production }
		self.widget.mapEvents(events)
		self.helptext = _("Confirm order")

	def start_production(self):
		AddProduction(self.producer, 15).execute(self.instance.session)

# this "tab" additionally requests functions for:
# * get: currently ordered ship: name / image / type (fisher/trade/war)
# * => get: currently ordered ship: description text / costs / available upgrades
#						(fisher/trade/war, builder level)
# * if resource icons not hardcoded: resource icons, sort them by amount
# UPGRADES: * checkboxes * check for boat builder level (+ research) * add. costs (get, add, display)
# * def start_production(self):  <<< actually start to produce the selected ship unit with the selected upgrades
#	(use inventory or go collect resources, switch focus to overview tab).
#	IMPORTANT: lock this button until unit is actually produced (no queue!)
