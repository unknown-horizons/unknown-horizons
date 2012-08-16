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
from operator import itemgetter

from fife.extensions.pychan.widgets import Icon, HBox, Label, Container

from horizons.command.production import AddProduction, RemoveFromQueue, CancelCurrentProduction
from horizons.gui.tabs import OverviewTab
from horizons.gui.util import create_resource_icon
from horizons.gui.widgets import OkButton, CancelButton
from horizons.util import Callback
from horizons.constants import PRODUCTIONLINES, RES, UNITS
from horizons.world.production.producer import Producer

class _BoatbuilderOverviewTab(OverviewTab):
	"""Private class all classes here inherit."""
	@property
	def producer(self):
		"""Abstract the instance, work only on components"""
		return self.instance.get_component(Producer)


class BoatbuilderTab(_BoatbuilderOverviewTab):

	SHIP_THUMBNAIL = "content/gui/icons/units/thumbnails/{type_id}.png"

	def __init__(self, instance):
		super(BoatbuilderTab, self).__init__(widget='boatbuilder.xml', instance=instance)
		self.helptext = _("Boat builder overview")

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		super(BoatbuilderTab, self).refresh()

		THUMB_PATH = "content/gui/images/objects/ships/116/%s.png"

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

			progress = math.floor(self.producer.get_production_progress() * 100)
			self.widget.findChild(name='progress').progress = progress
			self.widget.findChild(name='BB_progress_perc').text = u'{progress}%'.format(progress=progress)

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
			for place_in_queue, unit_type in enumerate(queue):
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
			name = self.instance.session.db.get_unit_type_name(produced_unit_id)
			container_active.findChild(name="headline_BB_builtship_label").text = _(name)
			container_active.findChild(name="BB_cur_ship_icon").helptext = "Storage: 4 slots, 120t \nHealth: 100"
			container_active.findChild(name="BB_cur_ship_icon").image = THUMB_PATH % produced_unit_id

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
					container_active.insertChild(container_active.button_inactive,
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
					container_active.insertChild(container_active.button_active,
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
			needed_res = production.get_consumed_resources()
			# Now sort! -amount is the positive value, drop unnecessary res (amount 0)
			needed_res = dict((res, -amount) for res, amount in needed_res.iteritems() if amount < 0)
			needed_res = sorted(needed_res.iteritems(), key=itemgetter(1), reverse=True)
			needed_res_container.removeAllChildren()
			for i, (res, amount) in enumerate(needed_res):
				icon = create_resource_icon(res, self.instance.session.db)
				icon.max_size = icon.min_size = icon.size = (16, 16)
				label = Label(name="needed_res_lbl_%s" % i)
				label.text = u'{amount}t'.format(amount=amount)
				new_hbox = HBox(name="needed_res_box_%s" % i)
				new_hbox.addChildren(icon, label)
				needed_res_container.addChild(new_hbox)

			cancel_button = self.widget.findChild(name="BB_cancel_button")
			cancel_cb = Callback(CancelCurrentProduction(self.producer).execute, self.instance.session)
			cancel_button.capture(cancel_cb, event_name="mouseClicked")

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
	def __init__(self, instance, ships, iconname, helptext):
		super(BoatbuilderSelectTab, self).__init__(
				instance=instance,
		          widget='boatbuilder_showcase.xml',
		          icon_path='content/gui/icons/tabwidget/boatbuilder/{name}_%s.png'.format(name=iconname))
		self.add_showcases(ships)
		self.helptext = helptext
		self.widget.findChild(name='headline').text = helptext
		self.init_values()

	def add_showcases(self, ships):
		showcases = self.widget.findChild(name='showcases')
		for i, (ship, prodline) in enumerate(ships):
			showcase = self.build_ship_info(i, ship, prodline)
			showcases.addChild(showcase)

	def build_ship_info(self, index, ship, prodline):
		size = (260, 90)
		widget = Container(name='showcase_%s' % index, position=(0, 20 + index*90),
		                   min_size=size, max_size=size, size=size)
		bg_icon = Icon(image='content/gui/images/background/square_80.png', name='bg_%s'%index)
		widget.addChild(bg_icon)

		icon_path = 'content/gui/images/objects/ships/76/{unit_id}.png'.format(unit_id=ship)
		unit_icon = Icon(image=icon_path, name='icon_%s'%index, position=(2, 2),
		                 helptext=_('important data'))
		widget.addChild(unit_icon)

		# if not buildable, this returns string with reason why to be displayed as helptext
		#ship_unbuildable = self.is_ship_unbuildable(ship)
		ship_unbuildable = False
		if not ship_unbuildable:
			button = OkButton(position=(60, 50), name='ok_%s'%index, helptext=_('Build this ship!'))
			button.capture(Callback(self.start_production, prodline))
		else:
			button = CancelButton(position=(60, 50), name='ok_%s'%index,
			helptext=ship_unbuildable)

		widget.addChild(button)

		#TODO since this code uses the boat builder as producer, the
		# gold cost of ships is in consumed res is always 0 since it
		# is paid from player inventory, not from the boat builder one.
		production = self.producer.create_production(prodline)
		# consumed == negative, reverse to sort in *ascending* order:
		costs = sorted(production.get_consumed_resources().iteritems(), key=itemgetter(1))
		for i, (res, amount) in enumerate(costs):
			xoffset = 103 + (i  % 2) * 55
			yoffset =  20 + (i // 2) * 20
			icon = create_resource_icon(res, self.instance.session.db)
			icon.max_size = icon.min_size = icon.size = (16, 16)
			icon.position = (xoffset, yoffset)
			label = Label(name='cost_%s_%s' % (index, i))
			if res == RES.GOLD:
				label.text = unicode(-amount)
			else:
				label.text = u'{amount:02}t'.format(amount=-amount)
			label.position = (22 + xoffset, yoffset)
			widget.addChild(icon)
			widget.addChild(label)
		return widget

	def start_production(self, prod_line_id):
		AddProduction(self.producer, prod_line_id).execute(self.instance.session)
		# show overview tab
		self.instance.session.ingame_gui.get_cur_menu()._show_tab(0)


class BoatbuilderFisherTab(BoatbuilderSelectTab):
	def __init__(self, instance):
		ships = [
			#(UNITS.FISHER_BOAT, PRODUCTIONLINES.FISHING_BOAT),
			#(UNITS.CUTTER, PRODUCTIONLINES.xxx),
			#(UNITS.HERRING_FISHER, PRODUCTIONLINES.xxx),
			#(UNITS.WHALER, PRODUCTIONLINES.xxx),
		]
		helptext = _("Fisher boats")
		super(BoatbuilderFisherTab, self).__init__(instance, ships, 'fisher', helptext)


class BoatbuilderTradeTab(BoatbuilderSelectTab):
	def __init__(self, instance):
		ships = [
			(UNITS.HUKER_SHIP, PRODUCTIONLINES.HUKER),
			#(UNITS.COURIER_BOAT, PRODUCTIONLINES.xxx),
			#(UNITS.SMALL_MERCHANT, PRODUCTIONLINES.xxx),
			#(UNITS.BIG_MERCHANT, PRODUCTIONLINES.xxx),
		]
		helptext = _("Trade boats")
		super(BoatbuilderTradeTab, self).__init__(instance, ships, 'trade', helptext)

class BoatbuilderWar1Tab(BoatbuilderSelectTab):
	def __init__(self, instance):
		ships = [
			#(UNITS.SMALL_GUNBOAT, PRODUCTIONLINES.SMALL_GUNBOAT),
			#(UNITS.NAVAL_CUTTER, PRODUCTIONLINES.NAVAL_CUTTER),
			#(UNITS.BOMBADIERE, PRODUCTIONLINES.BOMBADIERE),
			#(UNITS.SLOOP_O_WAR, PRODUCTIONLINES.SLOOP_O_WAR),
		]
		helptext = _("War boats")
		super(BoatbuilderWar1Tab, self).__init__(instance, ships, 'war1', helptext)

class BoatbuilderWar2Tab(BoatbuilderSelectTab):
	def __init__(self, instance):
		ships = [
			#(UNITS.GALLEY, PRODUCTIONLINES.GALLEY),
			#(UNITS.BIG_GUNBOAT, PRODUCTIONLINES.BIG_GUNBOAT),
			#(UNITS.CORVETTE, PRODUCTIONLINES.CORVETTE),
			(UNITS.FRIGATE, PRODUCTIONLINES.FRIGATE),
		]
		helptext = _("War ships")
		super(BoatbuilderWar2Tab, self).__init__(instance, ships, 'war2', helptext)

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
