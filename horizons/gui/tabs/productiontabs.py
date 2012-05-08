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

import weakref
from fife.extensions import pychan

from horizons.command.production import ToggleActive
from horizons.command.building import Tear
from horizons.constants import GAME_SPEED, PRODUCTION
from horizons.gui.tabs import OverviewTab
from horizons.gui.util import load_uh_widget
from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.scheduler import Scheduler
from horizons.util import Callback
from horizons.util.pychananimation import PychanAnimation
from horizons.component.storagecomponent import StorageComponent
from horizons.world.production.producer import Producer


class ProductionOverviewTab(OverviewTab):
	ACTIVE_PRODUCTION_ANIM_DIR = "content/gui/images/animations/cogs/large"
	BUTTON_BACKGROUND = "content/gui/images/buttons/msg_button.png"

	def  __init__(self, instance, widget='overview_productionbuilding.xml',
		         production_line_gui_xml='overview_productionline.xml'):
		super(ProductionOverviewTab, self).__init__(
			widget = widget,
			instance = instance
		)
		self.helptext = _("Production overview")
		self.production_line_gui_xml = production_line_gui_xml
		self._animations = []

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		self._refresh_utilisation()

		# remove old production line data
		parent_container = self.widget.child_finder('production_lines')
		while len(parent_container.children) > 0:
			child = parent_container.children[-1]
			if hasattr(child, "anim"):
				child.anim.stop()
				del child.anim
			parent_container.removeChild( child )

		# create a container for each production
		# sort by production line id to have a consistent (basically arbitrary) order
		for production in sorted(self.instance.get_component(Producer).get_productions(), \
								             key=(lambda x: x.get_production_line_id())):

			# we need to be notified of small production changes, that aren't passed through the instance
			production.add_change_listener(self._schedule_refresh, no_duplicates=True)

			gui = load_uh_widget(self.production_line_gui_xml)
			# fill in values to gui reflecting the current game state
			container = gui.findChild(name="production_line_container")
			if production.is_paused():
				container.removeChild( container.findChild(name="toggle_active_active") )
				toggle_icon = container.findChild(name="toggle_active_inactive")
				toggle_icon.name = "toggle_active"
			else:
				container.removeChild( container.findChild(name="toggle_active_inactive") )
				toggle_icon = container.findChild(name="toggle_active_active")
				toggle_icon.name = "toggle_active"

				if production.get_state() == PRODUCTION.STATES.producing:
					bg = pychan.widgets.Icon(image=self.__class__.BUTTON_BACKGROUND)
					bg.position = toggle_icon.position
					container.addChild(bg)
					container.removeChild(toggle_icon) # fix z-ordering
					container.addChild(toggle_icon)
					anim = PychanAnimation(toggle_icon, self.__class__.ACTIVE_PRODUCTION_ANIM_DIR)
					container.anim = anim
					anim.start(1.0/12, -1) # always start anew, people won't notice
					self._animations.append( weakref.ref( anim ) )

			# fill it with input and output resources
			in_res_container = container.findChild(name="input_res")
			self._add_resource_icons(in_res_container, production.get_consumed_resources())
			out_res_container = container.findChild(name="output_res")
			self._add_resource_icons(out_res_container, production.get_produced_resources())

			# fix pychans lack of dynamic container sizing
			# the container in the xml must provide a height attribute, that is valid for
			# one resource.
			max_res_in_one_line = max(len(production.get_produced_resources()), \
			                          len(production.get_consumed_resources()))
			container.height = max_res_in_one_line * container.height


			# active toggle_active button
			container.mapEvents( \
			  { 'toggle_active': \
			    Callback(ToggleActive(self.instance.get_component(Producer), production).execute, self.instance.session) \
			    } )
			# NOTE: this command causes a refresh, so we needn't change the toggle_active-button-image
			container.stylize('menu_black')
			parent_container.addChild(container)
		super(ProductionOverviewTab, self).refresh()

	def destruct_building(self):
		self.instance.session.ingame_gui.hide_menu()
		Tear(self.instance).execute(self.instance.session)

	def _refresh_utilisation(self):
		utilisation = 0
		if self.instance.has_component(Producer):
			utilisation = int(round(self.instance.get_component(Producer).capacity_utilisation * 100))
		self.widget.child_finder('capacity_utilisation').text = unicode(utilisation) + u'%'

	def _add_resource_icons(self, container, resources):
		for res in resources:
			inventory = self.instance.get_component(StorageComponent).inventory
			filled = (inventory[res] * 100) // inventory.get_limit(res)
			container.addChild(
				ImageFillStatusButton.init_for_res(self.instance.session.db, res,
					inventory[res], filled, use_inactive_icon=False, uncached=True))

	def show(self):
		super(ProductionOverviewTab, self).show()
		Scheduler().add_new_object(Callback(self._refresh_utilisation), self, run_in = GAME_SPEED.TICKS_PER_SECOND, loops = -1)

	def hide(self):
		super(ProductionOverviewTab, self).hide()
		self._cleanup()

	def on_instance_removed(self):
		self._cleanup()
		super(ProductionOverviewTab, self).on_instance_removed()

	def _cleanup(self):
		Scheduler().rem_all_classinst_calls(self)
		for production in self.instance.get_component(Producer).get_productions():
			production.discard_change_listener(self._schedule_refresh)
		for anim in self._animations:
			if anim():
				anim().stop()
		self._animations = []


class FarmProductionOverviewTab(ProductionOverviewTab):
	# the farm uses small buttons
	ACTIVE_PRODUCTION_ANIM_DIR = "content/gui/images/animations/cogs/small"
	BUTTON_BACKGROUND = "content/gui/images/buttons/msg_button_small.png"
	def  __init__(self, instance):
		super(FarmProductionOverviewTab, self).__init__(
			instance = instance,
			widget = 'overview_farm.xml',
			production_line_gui_xml = "overview_farmproductionline.xml"
		)
		self.helptext = _("Production overview")
