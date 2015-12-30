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
from boatbuildertabs import UnitbuilderTabBase, ProducerOverviewTabBase

class GroundunitbuilderTab(UnitbuilderTabBase):
	widget = 'groundunitbuilder.xml'
	helptext = _lazy("Groundunit builder overview")

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

class GroundunitbuilderSelectTab(ProducerOverviewTabBase):
	widget = 'groundunitbuilder_showcase.xml'

	def init_widget(self):
		super(GroundunitbuilderSelectTab, self).init_widget()
		self.widget.findChild(name='headline').text = self.helptext

		showcases = self.widget.findChild(name='showcases')
		for i, (groundunit, prodline) in enumerate(self.groundunits):
			showcase = self.build_groundunit_info(i, groundunit, prodline)
			showcases.addChild(showcase)

	def build_groundunit_info(self, index, groundunit, prodline):
		size = (260, 90)
		widget = Container(name='showcase_%s' % index, position=(0, 20 + index*90),
		                   min_size=size, max_size=size, size=size)
		bg_icon = Icon(image='content/gui/images/background/square_80.png', name='bg_%s'%index)
		widget.addChild(bg_icon)

		image = 'content/gui/images/objects/ships/76/{unit_id}.png'.format(unit_id=ship)
		helptext = self.instance.session.db.get_groundunit_tooltip(ship)
		unit_icon = Icon(image=image, name='icon_%s'%index, position=(2, 2),
		                 helptext=helptext)
		widget.addChild(unit_icon)

		# if not buildable, this returns string with reason why to be displayed as helptext
		#ship_unbuildable = self.is_ship_unbuildable(ship)
		groundunit_unbuildable = False
		if not groundunit_unbuildable:
			button = OkButton(position=(60, 50), name='ok_%s'%index, helptext=_('Build this groundunit!'))
			button.capture(Callback(self.start_production, prodline))
		else:
			button = CancelButton(position=(60, 50), name='ok_%s'%index,
			helptext=groundunit_unbuildable)

		widget.addChild(button)

		# Get production line info
		production = self.producer.create_production_line(prodline)
		# consumed == negative, reverse to sort in *ascending* order:
		costs = sorted(production.consumed_res.iteritems(), key=itemgetter(1))
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
		self.instance.session.ingame_gui.get_cur_menu().show_tab(0)

class GroundunitSoldiersTab(GroundunitbuilderSelectTab):
	icon_path = 'icons/tabwidget/boatbuilder/trade'
	helptext = _lazy("Swordman")

	groundunits = [
		(UNITS.SWORDSMAN, PRODUCTIONLINES.SWORDSMAN),
	]

# these tabs additionally request functions for:
# * goto: show [confirm view] tab (not accessible via tab button in the end)
#	need to provide information about the selected ship (which of the 4 buttons clicked)
# * check: mark those ship's buttons as unbuildable (close graphics) which do not meet the specified requirements.
#	the tooltips contain this info as well.

class GroundunitbuilderConfirmTab(ProducerOverviewTabBase):
	widget = 'groundunit_confirm.xml'
	helptext = _lazy("Confirm order")

	def init_widget(self):
		super(GroundunitbuilderConfirmTab, self).init_widget()
		events = { 'create_unit': self.start_production }
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
