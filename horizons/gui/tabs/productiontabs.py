# -*- coding: utf-8 -*-
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

import operator
import weakref

from fife.extensions.pychan.widgets import Icon, Label

from horizons.command.production import ToggleActive
from horizons.command.building import Tear
from horizons.constants import GAME_SPEED, PRODUCTION
from horizons.gui.tabs import OverviewTab
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.scheduler import Scheduler
from horizons.util.python.callback import Callback
from horizons.util.pychananimation import PychanAnimation
from horizons.component.storagecomponent import StorageComponent
from horizons.world.production.producer import Producer


class ProductionOverviewTab(OverviewTab):
	ACTIVE_PRODUCTION_ANIM_DIR = "content/gui/images/animations/cogs/large"
	BUTTON_BACKGROUND = "content/gui/images/buttons/msg_button.png"
	ARROW_TOP = "content/gui/icons/templates/production/production_arrow_top.png"
	ARROW_MID = "content/gui/icons/templates/production/production_arrow_start.png"
	ARROW_BOTTOM = "content/gui/icons/templates/production/production_arrow_bottom.png"
	ARROW_CONNECT_UP = "content/gui/icons/templates/production/production_arrow_connect_up.png"
	ARROW_CONNECT_DOWN = "content/gui/icons/templates/production/production_arrow_connect_down.png"

	def  __init__(self, instance, widget='overview_productionbuilding.xml',
		         production_line_gui_xml='overview_productionline.xml'):
		super(ProductionOverviewTab, self).__init__(widget=widget, instance=instance)
		self.helptext = _("Production overview")
		self.production_line_gui_xml = production_line_gui_xml
		self._animations = []

	def get_displayed_productions(self):
		"""List all possible productions of a buildings sorted by production line id.
		Overwritten in some child classes (e.g. farm tab).
		"""
		productions = self.instance.get_component(Producer).get_productions()
		return sorted(productions, key=operator.methodcaller('get_production_line_id'))

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self._refresh_utilisation()

		# remove old production line data
		parent_container = self.widget.child_finder('production_lines')
		while parent_container.children:
			child = parent_container.children[-1]
			if hasattr(child, "anim"):
				child.anim.stop()
				del child.anim
			parent_container.removeChild(child)

		# create a container for each production
		# sort by production line id to have a consistent (basically arbitrary) order
		for production in self.get_displayed_productions():
			# we need to be notified of small production changes
			# that aren't passed through the instance
			production.add_change_listener(self._schedule_refresh, no_duplicates=True)

			gui = load_uh_widget(self.production_line_gui_xml)
			# fill in values to gui reflecting the current game state
			container = gui.findChild(name="production_line_container")
			self._set_resource_amounts(container, production)

			centered_container = container.findChild(name='centered_production_icons')
			self._connect_multiple_input_res_for_production(centered_container, container, production)

			if production.is_paused():
				centered_container.removeChild( centered_container.findChild(name="toggle_active_active") )
				toggle_icon = centered_container.findChild(name="toggle_active_inactive")
				toggle_icon.name = "toggle_active"
			else:
				centered_container.removeChild( centered_container.findChild(name="toggle_active_inactive") )
				toggle_icon = centered_container.findChild(name="toggle_active_active")
				toggle_icon.name = "toggle_active"

				if production.get_state() == PRODUCTION.STATES.producing:
					bg = Icon(image=self.__class__.BUTTON_BACKGROUND)
					bg.position = toggle_icon.position
					centered_container.addChild(bg)
					centered_container.removeChild(toggle_icon) # fix z-ordering
					centered_container.addChild(toggle_icon)
					anim = PychanAnimation(toggle_icon, self.__class__.ACTIVE_PRODUCTION_ANIM_DIR)
					centered_container.anim = anim
					anim.start(1.0/12, -1) # always start anew, people won't notice
					self._animations.append( weakref.ref( anim ) )

			# fill it with input and output resources
			in_res_container = container.findChild(name="input_res")
			self._add_resource_icons(in_res_container, production.get_consumed_resources(), marker=True)
			out_res_container = centered_container.findChild(name="output_res")
			self._add_resource_icons(out_res_container, production.get_produced_resources())

			# active toggle_active button
			toggle_active = ToggleActive(self.instance.get_component(Producer), production)
			centered_container.mapEvents({
				'toggle_active': Callback(toggle_active.execute, self.instance.session)
			})
			# NOTE: this command causes a refresh, so we needn't change the toggle_active-button-image
			container.stylize('menu_black')
			parent_container.addChild(container)
		super(ProductionOverviewTab, self).refresh()

	def _connect_multiple_input_res_for_production(self, centered_container, container, production):
		"""Draws incoming arrows for production line container."""
		input_amount = len(production.get_consumed_resources())
		if input_amount == 0:
			# Do not draw input arrows if there is no input
			return

		# center the production line
		icon_height = ImageFillStatusButton.CELL_SIZE[1] + ImageFillStatusButton.PADDING
		center_y = (icon_height // 2) * (input_amount - 1)
		centered_container.position = (0, center_y)

		if input_amount % 2:
			# Add center arrow for 1, 3, 5, ... but not 2, 4, ...
			mid_arrow = Icon(image=self.__class__.ARROW_MID)
			mid_arrow.position = (58, 17 + center_y)
			container.insertChild(mid_arrow, 0)

		for res in xrange(input_amount // 2):
			# --\                      <= placed for res = 1
			# --\| <= place connector  <= placed for res = 0
			# ---O-->                  <= placed above
			# --/| <= place connector  <= placed for res = 0
			# --/                      <= placed for res = 1
			offset = -17 + (icon_height // 2) * (2 * res + (input_amount % 2) + 1)

			top_arrow = Icon(image=self.__class__.ARROW_TOP)
			top_arrow.position = (58, center_y - offset)
			container.insertChild(top_arrow, 0)

			bottom_arrow = Icon(image=self.__class__.ARROW_BOTTOM)
			bottom_arrow.position = (58, center_y + offset)
			container.insertChild(bottom_arrow, 0)

			# Place a connector image (the | in above sketch) that vertically connects
			# the input resource arrows. We need those if the production line has more
			# than three input resources. Connectors are placed in the inner loop parts.
			place_connectors = (1 + 2 * res) < (input_amount // 2)
			if place_connectors:
				# the connector downwards connects top_arrows
				down_connector = Icon(image=self.__class__.ARROW_CONNECT_DOWN)
				down_connector.position = (98, center_y - offset)
				container.insertChild(down_connector, 0)
				# the connector upwards connects up_arrows
				up_connector = Icon(image=self.__class__.ARROW_CONNECT_UP)
				up_connector.position = (98, center_y + offset)
				container.insertChild(up_connector, 0)

	def _set_resource_amounts(self, container, production):
		for res, amount in production.get_consumed_resources().iteritems():
			# consumed resources are negative!
			label = Label(text=unicode(-amount), margins=(0, 15))
			container.findChild(name='input_box').addChild(label)

		for res, amount in production.get_produced_resources().iteritems():
			label = Label(text=unicode(amount).rjust(2), margins=(0, 15))
			container.findChild(name='output_box').addChild(label)

	def destruct_building(self):
		self.instance.session.ingame_gui.hide_menu()
		Tear(self.instance).execute(self.instance.session)

	def _refresh_utilisation(self):
		utilisation = 0
		if self.instance.has_component(Producer):
			utilisation = int(round(self.instance.get_component(Producer).capacity_utilisation * 100))
		self.widget.child_finder('capacity_utilisation').text = unicode(utilisation) + u'%'

	def _add_resource_icons(self, container, resources, marker=False):
		calculate_position = lambda amount: (amount * 100) // inventory.get_limit(res)
		for res in resources:
			inventory = self.instance.get_component(StorageComponent).inventory
			filled = calculate_position(inventory[res])
			marker_level = calculate_position(-resources[res]) if marker else 0
			image_button = ImageFillStatusButton.init_for_res(self.instance.session.db, res,
					inventory[res], filled, marker=marker_level, use_inactive_icon=False, uncached=True)
			container.addChild(image_button)

	def show(self):
		super(ProductionOverviewTab, self).show()
		Scheduler().add_new_object(Callback(self._refresh_utilisation),
		                           self, run_in=GAME_SPEED.TICKS_PER_SECOND, loops=-1)

	def hide(self):
		super(ProductionOverviewTab, self).hide()
		self._cleanup()

	def on_instance_removed(self):
		self._cleanup()
		super(ProductionOverviewTab, self).on_instance_removed()

	def _cleanup(self):
		Scheduler().rem_all_classinst_calls(self)
		for production in self.get_displayed_productions():
			production.discard_change_listener(self._schedule_refresh)
		for anim in self._animations:
			if anim():
				anim().stop()
		self._animations = []


class SmallProductionOverviewTab(ProductionOverviewTab):
	"""Only display productions for which we have a related 'field' in range.
	Requires the building class using this tab to implement get_providers().
	"""
	# the farm uses small buttons
	ACTIVE_PRODUCTION_ANIM_DIR = "content/gui/images/animations/cogs/small"
	BUTTON_BACKGROUND = "content/gui/images/buttons/msg_button_small.png"
	def  __init__(self, instance):
		super(SmallProductionOverviewTab, self).__init__(
			instance=instance,
			widget='overview_farm.xml',
			production_line_gui_xml="overview_farmproductionline.xml"
		)
		self.helptext = _("Production overview")

	def get_displayed_productions(self):
		possible_res = set(res for field in self.instance.get_providers()
		                       for res in field.provided_resources)
		all_farm_productions = self.instance.get_component(Producer).get_productions()
		productions = set([p for p in all_farm_productions
		                     for res in p.get_consumed_resources().keys()
		                   if res in possible_res])
		return sorted(productions, key=operator.methodcaller('get_production_line_id'))
