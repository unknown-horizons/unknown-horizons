# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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
from typing import List, Tuple

from fife import fife
from fife.extensions.pychan.widgets import Container, HBox, Icon, Label

from horizons.command.production import AddProduction, CancelCurrentProduction, RemoveFromQueue
from horizons.constants import GAME_SPEED, PRODUCTIONLINES, RES, UNITS
from horizons.gui.util import create_resource_icon
from horizons.gui.widgets.imagebutton import CancelButton, OkButton
from horizons.i18n import gettext as T, gettext_lazy as LazyT
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.world.production.producer import Producer

from .overviewtab import OverviewTab


class ProducerOverviewTabBase(OverviewTab):
	"""Base class for tabs displaying producer data."""

	@property
	def producer(self):
		"""The current instance's Producer compontent."""
		return self.instance.get_component(Producer)


class UnitbuilderTabBase(ProducerOverviewTabBase):
	"""Tab Baseclass that can be used by unit builders."""

	def show(self):
		super().show()
		Scheduler().add_new_object(Callback(self.refresh), self, run_in=GAME_SPEED.TICKS_PER_SECOND, loops=-1)

	def hide(self):
		super().hide()
		Scheduler().rem_all_classinst_calls(self)

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		super().refresh()

		main_container = self.widget.findChild(name="UB_main_tab")
		container_active = main_container.findChild(name="container_active")
		container_inactive = main_container.findChild(name="container_inactive")
		progress_container = main_container.findChild(name="UB_progress_container")
		cancel_container = main_container.findChild(name="UB_cancel_container")

		# a Unitbuilder is considered active here if it builds sth, no matter if it's paused
		production_lines = self.producer.get_production_lines()
		if production_lines:
			self.show_production_is_active_container(container_active, container_inactive,
			                                         progress_container, cancel_container, production_lines)
		else:
			self.show_production_is_inactive_container(container_inactive, progress_container,
			                                           cancel_container, container_active)
		self.widget.adaptLayout()

	def show_production_is_active_container(self, container_active, container_inactive, progress_container, cancel_container, production_lines):
		"""Show the container containing the active production."""
		container_active.parent.showChild(container_active)
		container_inactive.parent.hideChild(container_inactive)

		self.update_production_is_active_container(progress_container, container_active, cancel_container, production_lines)

	def update_production_is_active_container(self, progress_container, container_active, cancel_container, production_lines):
		"""Update the active production container."""
		self.update_progress(progress_container)
		self.update_queue(container_active)
		self.update_buttons(container_active, cancel_container)

		needed_res_container = self.widget.findChild(name="UB_needed_resources_container")
		self.update_needed_resources(needed_res_container)

		# Set built unit info
		production_line = self.producer._get_production(production_lines[0])
		produced_unit_id = list(production_line.get_produced_units().keys())[0]

		name = self.instance.session.db.get_unit_type_name(produced_unit_id)
		container_active.findChild(name="headline_UB_builtunit_label").text = T(name)

		self.update_unit_icon(container_active, produced_unit_id)

		upgrades_box = container_active.findChild(name="UB_upgrades_box")
		upgrades_box.removeAllChildren()

	def show_production_is_inactive_container(self, container_inactive, progress_container, cancel_container, container_active):
		"""Hides all information on progress etc, and displays something to signal that the production is inactive."""
		container_inactive.parent.showChild(container_inactive)
		for w in (container_active, progress_container, cancel_container):
			w.parent.hideChild(w)

	def update_buttons(self, container_active, cancel_container):
		"""Show the correct active and inactive buttons, update cancel button"""
		button_active = container_active.findChild(name="toggle_active_active")
		button_inactive = container_active.findChild(name="toggle_active_inactive")
		to_active = not self.producer.is_active()

		if not to_active: # swap what we want to show and hide
			button_active, button_inactive = button_inactive, button_active
			button_active.parent.hideChild(button_active)

		button_inactive.parent.showChild(button_inactive)

		set_active_cb = Callback(self.producer.set_active, active=to_active)
		button_inactive.capture(set_active_cb, event_name="mouseClicked")

		cancel_container.parent.showChild(cancel_container)
		cancel_button = self.widget.findChild(name="UB_cancel_button")
		cancel_cb = Callback(CancelCurrentProduction(self.producer).execute, self.instance.session)
		cancel_button.capture(cancel_cb, event_name="mouseClicked")

	def update_unit_icon(self, container_active, produced_unit_id):
		"""Update the icon displaying the unit that is being built."""
		unit_icon = container_active.findChild(name="UB_cur_unit_icon")
		unit_icon.helptext = self.instance.session.db.get_unit_tooltip(produced_unit_id)
		unit_icon.image = self.__class__.UNIT_PREVIEW_IMAGE.format(type_id=produced_unit_id)

	def update_queue(self, container_active):
		""" Update the queue display"""
		queue = self.producer.get_unit_production_queue()
		queue_container = container_active.findChild(name="queue_container")
		queue_container.removeAllChildren()
		for place_in_queue, unit_type in enumerate(queue):
			image = self.__class__.UNIT_THUMBNAIL.format(type_id=unit_type)
			helptext = T("{ship} (place in queue: {place})").format(
		            ship=self.instance.session.db.get_unit_type_name(unit_type),
		            place=place_in_queue + 1)
			# people don't count properly, always starting at 1..
			icon_name = "queue_elem_" + str(place_in_queue)

			try:
				icon = Icon(name=icon_name, image=image, helptext=helptext)
			except fife.NotFound as e:
				# It's possible that this error was raised from a missing thumbnail asset,
				# so we check against that now and use a fallback thumbnail instead
				if 'content/gui/icons/thumbnails/' in e.what():
					# actually load the fallback unit image
					image = self.__class__.UNIT_THUMBNAIL.format(type_id="unknown_unit")
					icon = Icon(name=icon_name, image=image, helptext=helptext)
				else:
					raise

			rm_from_queue_cb = Callback(RemoveFromQueue(self.producer, place_in_queue).execute,
		                                self.instance.session)
			icon.capture(rm_from_queue_cb, event_name="mouseClicked")
			queue_container.addChild(icon)

	def update_needed_resources(self, needed_res_container):
		""" Update needed resources """
		production = self.producer.get_productions()[0]
		needed_res = production.get_consumed_resources()
		# Now sort! -amount is the positive value, drop unnecessary res (amount 0)
		needed_res = {res: -amount for res, amount in needed_res.items() if amount < 0}
		needed_res = sorted(needed_res.items(), key=itemgetter(1), reverse=True)
		needed_res_container.removeAllChildren()
		for i, (res, amount) in enumerate(needed_res):
			icon = create_resource_icon(res, self.instance.session.db)
			icon.max_size = icon.min_size = icon.size = (16, 16)
			label = Label(name="needed_res_lbl_{}".format(i))
			label.text = '{amount}t'.format(amount=amount)
			new_hbox = HBox(name="needed_res_box_{}".format(i))
			new_hbox.addChildren(icon, label)
			needed_res_container.addChild(new_hbox)

	def update_progress(self, progress_container):
		"""Update displayed progress"""
		progress_container.parent.showChild(progress_container)
		progress = math.floor(self.producer.get_production_progress() * 100)
		self.widget.findChild(name='progress').progress = progress
		progress_perc = self.widget.findChild(name='UB_progress_perc')
		progress_perc.text = '{progress}%'.format(progress=progress)


class BoatbuilderTab(UnitbuilderTabBase):
	widget = 'boatbuilder.xml'
	helptext = LazyT("Boat builder overview")

	UNIT_THUMBNAIL = "content/gui/icons/thumbnails/{type_id}.png"
	UNIT_PREVIEW_IMAGE = "content/gui/images/objects/ships/116/{type_id}.png"

# this tab additionally requests functions for:
# * decide: show [start view] = nothing but info text, look up the xml, or [building status view]
# * get: currently built ship: name / image / upgrades
# * resources still needed:
#	(a) which ones? three most important (image, name)
#	(b) how many? sort by amount, display (amount, overall amount needed of them, image)
# * pause production (keep order and "running" running costs [...] but collect no new resources)
# * abort building process: delete task, remove all resources, display [start view] again


class BoatbuilderSelectTab(ProducerOverviewTabBase):
	widget = 'boatbuilder_showcase.xml'

	def init_widget(self):
		super().init_widget()
		self.widget.findChild(name='headline').text = self.helptext

		showcases = self.widget.findChild(name='showcases')
		for i, (ship, prodline) in enumerate(self.ships):
			showcase = self.build_ship_info(i, ship, prodline)
			showcases.addChild(showcase)

	def build_ship_info(self, index, ship, prodline):
		size = (260, 90)
		widget = Container(name='showcase_{}'.format(index), position=(0, 20 + index * 90),
		                   min_size=size, max_size=size, size=size)
		bg_icon = Icon(image='content/gui/images/background/square_80.png', name='bg_{}'.format(index))
		widget.addChild(bg_icon)

		image = 'content/gui/images/objects/ships/76/{unit_id}.png'.format(unit_id=ship)
		helptext = self.instance.session.db.get_unit_tooltip(ship)
		unit_icon = Icon(image=image, name='icon_{}'.format(index), position=(2, 2),
		                 helptext=helptext)
		widget.addChild(unit_icon)

		# if not buildable, this returns string with reason why to be displayed as helptext
		#ship_unbuildable = self.is_ship_unbuildable(ship)
		ship_unbuildable = False
		if not ship_unbuildable:
			button = OkButton(position=(60, 50), name='ok_{}'.format(index), helptext=T('Build this ship!'))
			button.capture(Callback(self.start_production, prodline))
		else:
			button = CancelButton(position=(60, 50), name='ok_{}'.format(index),
			helptext=ship_unbuildable)

		widget.addChild(button)

		# Get production line info
		production = self.producer.create_production_line(prodline)
		# consumed == negative, reverse to sort in *ascending* order:
		costs = sorted(production.consumed_res.items(), key=itemgetter(1))
		for i, (res, amount) in enumerate(costs):
			xoffset = 103 + (i % 2) * 55
			yoffset = 20 + (i // 2) * 20
			icon = create_resource_icon(res, self.instance.session.db)
			icon.max_size = icon.min_size = icon.size = (16, 16)
			icon.position = (xoffset, yoffset)
			label = Label(name='cost_{}_{}'.format(index, i))
			if res == RES.GOLD:
				label.text = str(-amount)
			else:
				label.text = '{amount:02}t'.format(amount=-amount)
			label.position = (22 + xoffset, yoffset)
			widget.addChild(icon)
			widget.addChild(label)
		return widget

	def start_production(self, prod_line_id):
		AddProduction(self.producer, prod_line_id).execute(self.instance.session)
		# show overview tab
		self.instance.session.ingame_gui.get_cur_menu().show_tab(0)


class BoatbuilderFisherTab(BoatbuilderSelectTab):
	icon_path = 'icons/tabwidget/boatbuilder/fisher'
	helptext = LazyT("Fisher boats")

	ships = [
		#(UNITS.FISHER_BOAT, PRODUCTIONLINES.FISHING_BOAT),
		#(UNITS.CUTTER, PRODUCTIONLINES.CUTTER),
		#(UNITS.HERRING_FISHER, PRODUCTIONLINES.HERRING_FISHER),
		#(UNITS.WHALER, PRODUCTIONLINES.WHALER),
	] # type: List[Tuple[int, int]]


class BoatbuilderTradeTab(BoatbuilderSelectTab):
	icon_path = 'icons/tabwidget/boatbuilder/trade'
	helptext = LazyT("Trade boats")

	ships = [
		(UNITS.HUKER_SHIP, PRODUCTIONLINES.HUKER),
		#(UNITS.COURIER_BOAT, PRODUCTIONLINES.COURIER_BOAT),
		#(UNITS.SMALL_MERCHANT, PRODUCTIONLINES.SMALL_MERCHANT),
		#(UNITS.BIG_MERCHANT, PRODUCTIONLINES.BIG_MERCHANT),
	]


class BoatbuilderWar1Tab(BoatbuilderSelectTab):
	icon_path = 'icons/tabwidget/boatbuilder/war1'
	helptext = LazyT("War boats")

	ships = [
		#(UNITS.SMALL_GUNBOAT, PRODUCTIONLINES.SMALL_GUNBOAT),
		#(UNITS.NAVAL_CUTTER, PRODUCTIONLINES.NAVAL_CUTTER),
		#(UNITS.BOMBADIERE, PRODUCTIONLINES.BOMBADIERE),
		#(UNITS.SLOOP_O_WAR, PRODUCTIONLINES.SLOOP_O_WAR),
	] # type: List[Tuple[int, int]]


class BoatbuilderWar2Tab(BoatbuilderSelectTab):
	icon_path = 'icons/tabwidget/boatbuilder/war2'
	helptext = LazyT("War ships")

	ships = [
		#(UNITS.GALLEY, PRODUCTIONLINES.GALLEY),
		#(UNITS.BIG_GUNBOAT, PRODUCTIONLINES.BIG_GUNBOAT),
		#(UNITS.CORVETTE, PRODUCTIONLINES.CORVETTE),
		(UNITS.FRIGATE, PRODUCTIONLINES.FRIGATE),
	]


# these tabs additionally request functions for:
# * goto: show [confirm view] tab (not accessible via tab button in the end)
#	need to provide information about the selected ship (which of the 4 buttons clicked)
# * check: mark those ship's buttons as unbuildable (close graphics) which do not meet the specified requirements.
#	the tooltips contain this info as well.

class BoatbuilderConfirmTab(ProducerOverviewTabBase):
	widget = 'boatbuilder_confirm.xml'
	helptext = LazyT("Confirm order")

	def init_widget(self):
		super().init_widget()
		events = {'create_unit': self.start_production}
		self.widget.mapEvents(events)

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
