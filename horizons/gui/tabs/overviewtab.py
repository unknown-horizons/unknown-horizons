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
import weakref
import pychan

import horizons.main

from tabinterface import TabInterface
from horizons.util import Callback
from horizons.constants import RES, SETTLER, BUILDINGS
from horizons.gui.widgets  import TooltipButton
from horizons.command.production import ToggleActive
from horizons.command.building import Tear
from horizons.gui.widgets.imagefillstatusbutton import ImageFillStatusButton
from horizons.gui.utility import create_resource_icon
from horizons.i18n import load_xml_translated


class OverviewTab(TabInterface):
	def __init__(self, instance, widget = 'tab_widget/tab_overview.xml'):
		super(OverviewTab, self).__init__(widget)
		self.instance = instance
		self.init_values()
		self.button_up_image = 'content/gui/images/icons/hud/common/building_overview_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/building_overview_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/building_overview_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/building_overview_h.png'
		self.tooltip = u"Overview"

	def refresh(self):
		if hasattr(self.instance, 'name'):
			name_widget = self.widget.child_finder('name')
			name_widget.text = _(unicode(self.instance.name))
		self.widget.adaptLayout()

	def show(self):
		super(OverviewTab, self).show()
		if not self.instance.has_change_listener(self.refresh):
			self.instance.add_change_listener(self.refresh)
		if not self.instance.has_remove_listener(self.hide):
			self.instance.add_remove_listener(self.hide)

	def hide(self):
		super(OverviewTab, self).hide()
		if self.instance.has_change_listener(self.refresh):
			self.instance.remove_change_listener(self.refresh)
		if self.instance.has_remove_listener(self.hide):
			self.instance.remove_remove_listener(self.hide)


class BranchOfficeOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(BranchOfficeOverviewTab, self).__init__(
			widget = 'tab_widget/tab_branch_overview.xml',
			instance = instance
		)
		self.button_up_image = 'content/gui/images/icons/hud/common/building_overview_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/building_overview_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/building_overview_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/building_overview_h.png'
		self.tooltip = u"Branch Office \\n Overview"


class ShipOverviewTab(OverviewTab):
	def __init__(self, instance):
		super(ShipOverviewTab, self).__init__(
			widget = 'tab_widget/tab_overview_ship.xml',
			instance = instance
		)
		self.button_up_image = 'content/gui/images/icons/hud/common/ship_inv_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/ship_inv_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/ship_inv_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/ship_inv_h.png'
		self.widget.findChild(name='name').stylize("headline")
		self.tooltip = u"Ship Overview"

	def refresh(self):
		# show rename when you click on name
		events = {
			'name': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.instance)
		}

		# check if we can display the foundSettlement-anchor
		islands = self.instance.session.world.get_islands_in_radius(self.instance.position, self.instance.radius)
		if len(islands) > 0:
			events['foundSettelment'] = Callback(self.instance.session.ingame_gui._build, \
			                                     BUILDINGS.BRANCH_OFFICE_CLASS, \
			                                     weakref.ref(self.instance) )
			self.widget.child_finder('bg_button').set_active()
			self.widget.child_finder('foundSettelment').set_active()
		else:
			events['foundSettelment'] = None
			self.widget.child_finder('bg_button').set_inactive()
			self.widget.child_finder('foundSettelment').set_inactive()

		self.widget.mapEvents(events)
		super(ShipOverviewTab, self).refresh()


class ProductionOverviewTab(OverviewTab):
	production_line_gui_xml = "tab_widget/tab_production_line.xml"

	def  __init__(self, instance):
		super(ProductionOverviewTab, self).__init__(
			widget = 'buildings_gui/production_building_overview.xml',
			instance = instance
		)
		self.button_up_image = 'content/gui/images/icons/hud/common/building_overview_u.png'
		self.button_active_image = 'content/gui/images/icons/hud/common/building_overview_a.png'
		self.button_down_image = 'content/gui/images/icons/hud/common/building_overview_d.png'
		self.button_hover_image = 'content/gui/images/icons/hud/common/building_overview_h.png'
		self.tooltip = u"Production Overview"

		self.destruct_button = TooltipButton(name="destruct_button", up_image="content/gui/images/background/delete.png", down_image="content/gui/images/background/delete_h.png", hover_image="content/gui/images/background/delete_h.png", tooltip="Destroy Building", position=(190,330))
		self.widget.addChild(self.destruct_button)
		self.widget.mapEvents( { 'destruct_button' : self.destruct_building } )

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		costs = 0
		if hasattr(self.instance, 'running_costs'):
			costs = self.instance.running_costs
		self.widget.child_finder('running_costs').text = unicode(costs)

		cap_util = 0
		if hasattr(self.instance, 'capacity_utilisation'):
			cap_util = int(round( self.instance.capacity_utilisation * 100))
		self.widget.child_finder('capacity_utilisation').text = unicode(cap_util) + u'%'

		# remove old production line data
		parent_container = self.widget.child_finder('production_lines')
		while len(parent_container.children) > 0:
			parent_container.removeChild(parent_container.children[0])

		# create a container for each production
		# sort by production line id to have a consistent (basically arbitrary) order
		for production in sorted(self.instance._get_productions(), \
		                         key=(lambda x: x.get_production_line_id())):
			gui = load_xml_translated(self.production_line_gui_xml)
			container = gui.findChild(name="production_line_container")
			if production.is_paused():
				container.removeChild( container.findChild(name="toggle_active_active") )
				container.findChild(name="toggle_active_inactive").name = "toggle_active"
			else:
				container.removeChild( container.findChild(name="toggle_active_inactive") )
				container.findChild(name="toggle_active_active").name = "toggle_active"

			# fill it with input and output resources
			in_res_container = container.findChild(name="input_res")
			for in_res in production.get_consumed_resources():
				in_res_container.addChild( ImageFillStatusButton.init_for_res(in_res, \
				                                    self.instance.inventory[in_res], horizons.main.db, \
				                                    use_inactive_icon=False) )
			out_res_container = container.findChild(name="output_res")
			for out_res in production.get_produced_res():
				out_res_container.addChild( ImageFillStatusButton.init_for_res(out_res, \
				                                    self.instance.inventory[out_res], horizons.main.db, \
				                                    use_inactive_icon=False) )

			# active toggle_active button
			container.mapEvents( { 'toggle_active': ToggleActive(self.instance, production).execute } )
			# NOTE: this command causes a refresh, so we needn't change the toggle_active-button-image
			container.stylize('menu_black')
			parent_container.addChild(container)
		super(ProductionOverviewTab, self).refresh()

	def destruct_building(self):
		self.instance.session.ingame_gui.hide_menu()
		if self.destruct_button.gui.isVisible():
			self.destruct_button.hide_tooltip()
		Tear(self.instance).execute()


class SettlerOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(SettlerOverviewTab, self).__init__(
			widget = 'tab_widget/tab_overview_settler.xml',
			instance = instance
		)
		self.tooltip = u"Settler Overview"
		_setup_tax_slider(self.widget.child_finder('tax_slider'), self.instance.settlement)

	def refresh(self):
		self.widget.child_finder('happiness').progress = self.instance.happiness
		self.widget.child_finder('inhabitants').text = unicode( "%s/%s" % ( \
			self.instance.inhabitants, self.instance.inhabitants_max ) )
		self.widget.child_finder('taxes').text = unicode(self.instance.last_tax_payed)
		self.update_consumed_res()
		super(SettlerOverviewTab, self).refresh()

	def update_consumed_res(self):
		"""Updates the container that displays the needed resources of the settler"""
		container = self.widget.findChild(name="needed_res")
		# remove icons from the container
		container.removeChildren(*container.children)

		# create new ones
		resources = self.instance.get_currently_not_consumed_resources()
		for res in resources:
			icon = create_resource_icon(res, horizons.main.db)
			container.addChild(icon)

		container.adaptLayout()

class MarketPlaceOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(MarketPlaceOverviewTab, self).__init__(
			widget = 'tab_widget/tab_overview_marketplace.xml',
			instance = instance
		)
		_setup_tax_slider(self.widget.child_finder('tax_slider'), self.instance.settlement)
		self.tooltip = u"Market Place Overview"

	def refresh(self):
		super(MarketPlaceOverviewTab, self).refresh()



###
# Minor utility functions

def _setup_tax_slider(slider, settlement):
	"""Set up a slider to work as tax slider"""
	slider.setScaleStart(SETTLER.TAX_SETTINGS_MIN)
	slider.setScaleEnd(SETTLER.TAX_SETTINGS_MAX)
	slider.setStepLength(SETTLER.TAX_SETTINGS_STEP)
	slider.setValue(settlement.tax_setting)
	slider.stylize('book')
	def on_slider_change():
		tax = round( slider.getValue() / 0.5 ) * 0.5
		slider.setValue(tax)
		settlement.tax_setting = tax
	slider.capture(on_slider_change)
