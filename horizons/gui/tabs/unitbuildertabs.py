# ###################################################
# Copyright (C) 2008-2014 The Unknown Horizons Team
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
from horizons.engine import Fife
from horizons.gui.tabs import OverviewTab
from horizons.gui.util import create_resource_icon
from horizons.gui.widgets.imagebutton import OkButton, CancelButton
from horizons.i18n import _lazy
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.constants import PRODUCTIONLINES, RES, UNITS, GAME_SPEED
from horizons.world.production.producer import Producer

class ProducerOverviewTabBase(OverviewTab):
	"""Base class for tabs displaying producer data."""
	
	@property
	def producer(self):
		"""The current instance's Producer compontent."""
		return self.instance.get_component(Producer)
	
class UnitbuilderTabBase(ProducerOverviewTabBase):
	"""Tab Baseclass that can be used by unit builders."""
	
	def show(self):
		super(UnitbuilderTabBase, self).show()
		Scheduler().add_new_object(Callback(self.refresh), self, run_in=GAME_SPEED.TICKS_PER_SECOND, loops=-1)

	def hide(self):
		super(UnitbuilderTabBase, self).hide()
		Scheduler().rem_all_classinst_calls(self)
		
	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		super(UnitbuilderTabBase, self).refresh()

		main_container = self.widget.findChild(name="UB_main_tab")
		container_active = main_container.findChild(name="container_active")
		container_inactive = main_container.findChild(name="container_inactive")
		progress_container = main_container.findChild(name="UB_progress_container")
		cancel_container = main_container.findChild(name="UB_cancel_container")

		# a Unitbuilder is considered active here if it builds sth, no matter if it's paused
		production_lines = self.producer.get_production_lines()
		if len(production_lines) > 0:
			self.show_production_is_active_container(container_active, container_inactive,
			                                         progress_container, cancel_container, production_lines)
		else:
			self.show_production_is_inactive_container(container_inactive, progress_container, 
			                                           cancel_container, container_active)
		self.widget.adaptLayout()
		
	def show_production_is_active_container(self, container_active, container_inactive, progress_container, cancel_container, production_lines):
		"""Show the container containing the active production."""
		container_active.parent.showChild(container_active)
		if (Fife.getVersion() >= (0, 4, 0)):
			container_inactive.parent.hideChild(container_inactive)
		else:
			if not container_inactive in container_inactive.parent.hidden_children:
				container_inactive.parent.hideChild(container_inactive)
				
		self.update_production_is_active_container(progress_container, container_active, cancel_container, production_lines)

	def update_production_is_active_container(self, progress_container, container_active, cancel_container, production_lines):
		"""Update the active production container."""
		self.update_progress(progress_container)
		self.update_queue(container_active)
		self.update_buttons(container_active, cancel_container)
		
		needed_res_container = self.widget.findChild(name="UB_needed_resources_container")
		self.update_needed_resources(needed_res_container)

		# Set built ship info
		production_line = self.producer._get_production(production_lines[0])
		produced_unit_id = production_line.get_produced_units().keys()[0]
		
		name = self.instance.session.db.get_unit_type_name(produced_unit_id)
		container_active.findChild(name="headline_UB_builtship_label").text = _(name)
		
		self.update_ship_icon(container_active, produced_unit_id)

		upgrades_box = container_active.findChild(name="UB_upgrades_box")
		upgrades_box.removeAllChildren()

	def show_production_is_inactive_container(self, container_inactive, progress_container, cancel_container, container_active):
		"""Hides all information on progress etc, and displays something to signal that the production is inactive."""
		container_inactive.parent.showChild(container_inactive)
		for w in (container_active, progress_container, cancel_container):
			if (Fife.getVersion() >= (0, 4, 0)):
				w.parent.hideChild(w)
			else:
				if not w in w.parent.hidden_children:
					w.parent.hideChild(w)

	def update_buttons(self, container_active, cancel_container):
		"""Show the correct active and inactive buttons, update cancel button"""
		button_active = container_active.findChild(name="toggle_active_active")
		button_inactive = container_active.findChild(name="toggle_active_inactive")
		to_active = not self.producer.is_active()

		if not to_active: # swap what we want to show and hide
			button_active, button_inactive = button_inactive, button_active
		if (Fife.getVersion() >= (0, 4, 0)):
			button_active.parent.hideChild(button_active)
		else:
			if not button_active in button_active.parent.hidden_children:
				button_active.parent.hideChild(button_active)
		button_inactive.parent.showChild(button_inactive)

		set_active_cb = Callback(self.producer.set_active, active=to_active)
		button_inactive.capture(set_active_cb, event_name="mouseClicked")
		
		cancel_container.parent.showChild(cancel_container)
		cancel_button = self.widget.findChild(name="UB_cancel_button")
		cancel_cb = Callback(CancelCurrentProduction(self.producer).execute, self.instance.session)
		cancel_button.capture(cancel_cb, event_name="mouseClicked")

	def update_ship_icon(self, container_active, produced_unit_id):
		"""Update the icon displaying the ship that is being built."""
		ship_icon = container_active.findChild(name="UB_cur_ship_icon")
		ship_icon.helptext = self.instance.session.db.get_ship_tooltip(produced_unit_id)
		ship_icon.image = self.__class__.UNIT_PREVIEW_IMAGE.format(type_id=produced_unit_id)

	def update_queue(self, container_active):
		""" Update the queue display"""
		queue = self.producer.get_unit_production_queue()
		queue_container = container_active.findChild(name="queue_container")
		queue_container.removeAllChildren()
		for place_in_queue, unit_type in enumerate(queue):
			image = self.__class__.UNIT_THUMBNAIL.format(type_id=unit_type)
			helptext = _("{ship} (place in queue: {place})").format(
		            ship=self.instance.session.db.get_unit_type_name(unit_type),
		            place=place_in_queue+1)
			# people don't count properly, always starting at 1..
			icon_name = "queue_elem_"+str(place_in_queue)
			icon = Icon(name=icon_name, image=image, helptext=helptext)
			rm_from_queue_cb = Callback(RemoveFromQueue(self.producer, place_in_queue).execute,
		                                self.instance.session)
			icon.capture(rm_from_queue_cb, event_name="mouseClicked")
			queue_container.addChild( icon )

	def update_needed_resources(self, needed_res_container):
		""" Update needed resources """
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

	def update_progress(self, progress_container):
		"""Update displayed progress"""
		progress_container.parent.showChild(progress_container)
		progress = math.floor(self.producer.get_production_progress() * 100)
		self.widget.findChild(name='progress').progress = progress
		progress_perc = self.widget.findChild(name='UB_progress_perc')
		progress_perc.text = u'{progress}%'.format(progress=progress)
