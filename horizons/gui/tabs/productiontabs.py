# -*- coding: utf-8 -*-
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

import operator
import weakref

from fife.extensions.pychan.widgets import ABox, Icon, Label

from horizons.command.building import Tear
from horizons.command.production import ToggleActive
from horizons.component.fieldbuilder import FieldBuilder
from horizons.component.storagecomponent import StorageComponent
from horizons.constants import GAME_SPEED, PRODUCTION
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagebutton import ImageButton
from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.i18n import gettext as T, gettext_lazy as LazyT
from horizons.scheduler import Scheduler
from horizons.util.pychananimation import PychanAnimation
from horizons.util.python.callback import Callback
from horizons.world.production.producer import Producer

from .overviewtab import OverviewTab


class ProductionOverviewTab(OverviewTab):
	widget = 'overview_productionbuilding.xml'
	helptext = LazyT("Production overview")
	production_line_gui_xml = 'overview_productionline.xml'

	ACTIVE_PRODUCTION_ANIM_DIR = "content/gui/images/animations/cogs/large"
	BUTTON_BACKGROUND = "content/gui/images/buttons/msg_button.png"
	ARROW_TOP = "content/gui/icons/templates/production/production_arrow_top.png"
	ARROW_MID = "content/gui/icons/templates/production/production_arrow_start.png"
	ARROW_BOTTOM = "content/gui/icons/templates/production/production_arrow_bottom.png"
	ARROW_CONNECT_UP = "content/gui/icons/templates/production/production_arrow_connect_up.png"
	ARROW_CONNECT_DOWN = "content/gui/icons/templates/production/production_arrow_connect_down.png"
	ARROWHEAD_TOP = "content/gui/icons/templates/production/production_arrowhead_top.png"
	ARROWHEAD_MID = "content/gui/icons/templates/production/production_arrow_head.png"
	ARROWHEAD_BOTTOM = "content/gui/icons/templates/production/production_arrowhead_bottom.png"
	ARROWHEAD_CONNECT_UP = "content/gui/icons/templates/production/production_arrowhead_connect_up.png"
	ARROWHEAD_CONNECT_DOWN = "content/gui/icons/templates/production/production_arrowhead_connect_down.png"
	ICON_HEIGHT = ImageFillStatusButton.CELL_SIZE[1] + ImageFillStatusButton.PADDING

	def  __init__(self, instance):
		self._animations = []
		super(ProductionOverviewTab, self).__init__(instance=instance)

	def get_displayed_productions(self):
		"""List all possible productions of a buildings sorted by production line id.
		Overwritten in some child classes (e.g. farm tab).
		"""
		productions = self.instance.get_component(Producer).get_productions()
		return sorted(productions, key=operator.methodcaller('get_production_line_id'))

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self._refresh_utilization()

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

			centered_container = container.findChild(name='centered_production_icons')
			center_y = self._center_production_line(container, production)
			centered_container.position = (centered_container.position[0], center_y - 44 // 2)
			self._set_resource_amounts(container, production)

			if production.is_paused():
				centered_container.removeChild(centered_container.findChild(name="toggle_active_active"))
				toggle_icon = centered_container.findChild(name="toggle_active_inactive")
				toggle_icon.name = "toggle_active"
			else:
				centered_container.removeChild(centered_container.findChild(name="toggle_active_inactive"))
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
					self._animations.append(weakref.ref(anim))

			# fill it with input and output resources
			in_res_container = container.findChild(name="input_res")
			self._add_resource_icons(in_res_container, production.get_consumed_resources(), marker=True)
			out_res_container = container.findChild(name="output_res")
			self._add_resource_icons(out_res_container, production.get_produced_resources())

			# active toggle_active button
			toggle_active = ToggleActive(self.instance.get_component(Producer), production)
			centered_container.mapEvents({
				'toggle_active': Callback(toggle_active.execute, self.instance.session)
			})
			# NOTE: this command causes a refresh, so we needn't change the toggle_active-button-image
			parent_container.addChild(container)
		super(ProductionOverviewTab, self).refresh()

	def _center_production_line(self, parent_container, production):
		"""Centers in/out production line display for amount of resources each.

		@return: y value to center other gui parts (toggle icon etc.) around vertically.
		"""
		input_amount = len(production.get_consumed_resources())
		output_amount = len(production.get_produced_resources())
		# Center of production line arrows (where to place toggle icon).
		height_diff_y = max(1, output_amount, input_amount) - 1
		center_y = (self.ICON_HEIGHT // 2) * height_diff_y
		# Center input and output boxes of the production line if necessary.
		if input_amount != output_amount:
			height_diff_in = max(0, output_amount - max(1, input_amount))
			height_diff_out = max(0, input_amount - max(1, output_amount))
			center_y_in = (self.ICON_HEIGHT // 2) * height_diff_in
			center_y_out = (self.ICON_HEIGHT // 2) * height_diff_out
			input_container = parent_container.findChild(name='input_container')
			output_container = parent_container.findChild(name='output_container')
			input_container.position = (input_container.position[0], center_y_in)
			output_container.position = (output_container.position[0], center_y_out)
		# Draw and combine arrows for input and output.
		if input_amount > 0:
			self._draw_pretty_arrows(parent_container, input_amount, x=58, y=center_y, out=False)
		if output_amount > 0:
			self._draw_pretty_arrows(parent_container, output_amount, x=96, y=center_y, out=True)
		return center_y + self.ICON_HEIGHT // 2

	def _draw_pretty_arrows(self, parent_container, amount, x=0, y=0, out=False):
		"""Draws incoming or outgoing arrows for production line container."""
		if amount % 2:
			# Add center arrow for 1, 3, 5, ... but not 2, 4, ...
			if out:
				mid_arrow = Icon(image=self.__class__.ARROWHEAD_MID)
			else:
				mid_arrow = Icon(image=self.__class__.ARROW_MID)
			mid_arrow.position = (x, 17 + y)
			parent_container.insertChild(mid_arrow, 0)

		for res in xrange(amount // 2):
			# --\                      <= placed for res = 1
			# --\| <= place connector  <= placed for res = 0
			# ---O-->                  <= placed above (mid_arrow)
			# --/| <= place connector  <= placed for res = 0
			# --/                      <= placed for res = 1
			offset = -17 + (self.ICON_HEIGHT // 2) * (2 * res + (amount % 2) + 1)

			if out:
				top_arrow = Icon(image=self.__class__.ARROWHEAD_TOP)
			else:
				top_arrow = Icon(image=self.__class__.ARROW_TOP)
			top_arrow.position = (x, y - offset)
			parent_container.insertChild(top_arrow, 0)

			if out:
				bottom_arrow = Icon(image=self.__class__.ARROWHEAD_BOTTOM)
			else:
				bottom_arrow = Icon(image=self.__class__.ARROW_BOTTOM)
			bottom_arrow.position = (x, y + offset)
			parent_container.insertChild(bottom_arrow, 0)

			# Place a connector image (the | in above sketch) that vertically connects
			# the input resource arrows. We need those if the production line has more
			# than three input resources. Connectors are placed in the inner loop parts.
			place_connectors = amount > (3 + 2 * res)
			if place_connectors:
				# the connector downwards connects top_arrows
				if out:
					down_connector = Icon(image=self.__class__.ARROWHEAD_CONNECT_DOWN)
				else:
					down_connector = Icon(image=self.__class__.ARROW_CONNECT_DOWN)
				down_connector.position = (98, y - offset)
				parent_container.insertChild(down_connector, 0)
				# the connector upwards connects up_arrows
				if out:
					up_connector = Icon(image=self.__class__.ARROWHEAD_CONNECT_UP)
				else:
					up_connector = Icon(image=self.__class__.ARROW_CONNECT_UP)
				up_connector.position = (98, y + offset)
				parent_container.insertChild(up_connector, 0)

	def _set_resource_amounts(self, container, production):
		for res, amount in production.get_consumed_resources().iteritems():
			# consumed resources are negative!
			label = Label(text=unicode(-amount), margins=(0, 16))
			container.findChild(name='input_box').addChild(label)

		for res, amount in production.get_produced_resources().iteritems():
			label = Label(text=unicode(amount).rjust(2), margins=(0, 16))
			container.findChild(name='output_box').addChild(label)

	def destruct_building(self):
		self.instance.session.ingame_gui.hide_menu()
		Tear(self.instance).execute(self.instance.session)

	def _refresh_utilization(self):
		utilization = 0
		if self.instance.has_component(Producer):
			utilization = int(round(self.instance.get_component(Producer).capacity_utilization * 100))
		self.widget.child_finder('capacity_utilization').text = unicode(utilization) + u'%'

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
		Scheduler().add_new_object(Callback(self._refresh_utilization),
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


class LumberjackOverviewTab(ProductionOverviewTab):
	"""Same as ProductionOverviewTab but add a button to fill range with trees.
	"""
	def init_widget(self):
		super(LumberjackOverviewTab, self).init_widget()
		container = ABox(position=(20, 210))
		icon = Icon(name='build_all_bg')
		button = ImageButton(name='build_all_button')
		container.addChild(icon)
		container.addChild(button)
		self.widget.addChild(container)
		self.update_data()

	def update_data(self):
		field_comp = self.instance.get_component(FieldBuilder)
		icon = self.widget.child_finder('build_all_bg')
		button = self.widget.child_finder('build_all_button')

		(enough_res, missing_res) = field_comp.check_resources()
		# Disable "build menu" button if nothing would be built or construction
		# cannot be afforded by the player right now.
		if enough_res and field_comp.how_many > 0:
			icon.image = "content/gui/images/buttons/buildmenu_button_bg.png"
			button.path = 'icons/tabwidget/lumberjackcamp/tree_area_build'
		else:
			icon.image = "content/gui/images/buttons/buildmenu_button_bg_bw.png"
			button.path = 'icons/tabwidget/lumberjackcamp/no_area_build'
		button.min_size = button.max_size = button.size = (46, 46)
		button.helptext = T('Fill range with {how_many} trees').format(
			how_many=field_comp.how_many)

		res_bar = self.instance.session.ingame_gui.resource_overview

		click_cb = Callback.ChainedCallbacks(field_comp.fill_range, self.update_data)
		enter_cb = Callback(res_bar.set_construction_mode, self.instance, field_comp.total_cost)
		#TODO the tooltip should actually hide on its own. Ticket #1096
		exit_cb = Callback.ChainedCallbacks(res_bar.close_construction_mode, button.hide_tooltip)
		self.widget.mapEvents({
			button.name: click_cb,
			button.name + '/mouseEntered': enter_cb,
			button.name + '/mouseExited': exit_cb,
		})


class SmallProductionOverviewTab(ProductionOverviewTab):
	"""Only display productions for which we have a related 'field' in range.
	Requires the building class using this tab to implement get_providers().
	"""
	widget = 'overview_farm.xml'
	helptext = LazyT("Production overview")
	production_line_gui_xml = "overview_farmproductionline.xml"

	# the farm uses small buttons
	ACTIVE_PRODUCTION_ANIM_DIR = "content/gui/images/animations/cogs/small"
	BUTTON_BACKGROUND = "content/gui/images/buttons/msg_button_small.png"

	def get_displayed_productions(self):
		possible_res = set(res for field in self.instance.get_providers()
		                       for res in field.provided_resources)
		all_farm_productions = self.instance.get_component(Producer).get_productions()
		productions = {p for p in all_farm_productions
		                     for res in p.get_consumed_resources().keys()
		                   if res in possible_res}
		return sorted(productions, key=operator.methodcaller('get_production_line_id'))
