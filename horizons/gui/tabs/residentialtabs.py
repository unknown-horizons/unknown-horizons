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

from horizons.util import Callback, ActionSetLoader
from horizons.constants import SETTLER
from horizons.command.uioptions import SetTaxSetting
from horizons.gui.tabs import OverviewTab
from horizons.gui.util import create_resource_icon
from horizons.component.namedcomponent import NamedComponent
from horizons.messaging import SettlerUpdate


class SettlerOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(SettlerOverviewTab, self).__init__(
			widget = 'overview_settler.xml',
			instance = instance
		)
		self.helptext = _("Settler overview")
		self.widget.findChild(name="headline").text = self.instance.settlement.get_component(NamedComponent).name
		setup_tax_slider(self.widget.child_finder('tax_slider'), self.widget.child_finder('tax_val_label'),
		                  self.instance.settlement, self.instance.level)

		self.widget.child_finder('tax_val_label').text = unicode(self.instance.settlement.tax_settings[self.instance.level])
		action_set = ActionSetLoader.get_sets()[self.instance._action_set_id]
		action_gfx = action_set.items()[0][1]
		image = action_gfx[45].keys()[0]
		self.widget.findChild(name="building_image").image = image

	def on_settler_level_change(self, message):
		assert isinstance(message, SettlerUpdate)
		setup_tax_slider(self.widget.child_finder('tax_slider'), self.widget.child_finder('tax_val_label'),
		                  self.instance.settlement, message.level)
		self.widget.child_finder('tax_val_label').text = unicode(self.instance.settlement.tax_settings[self.instance.level])
		imgs = ActionSetLoader.get_sets()[self.instance._action_set_id].items()[0][1]
		self.widget.findChild(name="building_image").image = imgs[45].keys()[0]

	def show(self):
		super(SettlerOverviewTab, self).show()
		SettlerUpdate.subscribe(self.on_settler_level_change, sender=self.instance)

	def hide(self):
		SettlerUpdate.unsubscribe(self.on_settler_level_change, sender=self.instance)
		super(SettlerOverviewTab, self).hide()

	def refresh(self):
		self.widget.child_finder('happiness').progress = self.instance.happiness
		self.widget.child_finder('inhabitants').text = u"%s/%s" % (
		                                               self.instance.inhabitants,
		                                               self.instance.inhabitants_max)
		self.widget.child_finder('taxes').text = unicode(self.instance.last_tax_payed)
		self.update_consumed_res()
		self.widget.findChild(name="headline").text = self.instance.settlement.get_component(NamedComponent).name
		events = {
				'headline': Callback(self.instance.session.ingame_gui.show_change_name_dialog, self.instance.settlement)
		         }
		self.widget.mapEvents(events)
		super(SettlerOverviewTab, self).refresh()

	def update_consumed_res(self):
		"""Updates the container that displays the needed resources of the settler"""
		container = self.widget.findChild(name="needed_res")
		# remove icons from the container
		container.removeAllChildren()

		# create new ones
		resources = self.instance.get_currently_not_consumed_resources()
		for res in resources:
			icon = create_resource_icon(res, self.instance.session.db)
			icon.max_size = icon.min_size = icon.size = (32, 32)
			container.addChild(icon)

		container.adaptLayout()

def setup_tax_slider(slider, val_label, settlement, level):
	"""Set up a slider to work as tax slider"""
	slider.scale_start = SETTLER.TAX_SETTINGS_MIN
	slider.scale_end = SETTLER.TAX_SETTINGS_MAX
	slider.step_length = SETTLER.TAX_SETTINGS_STEP
	slider.value = settlement.tax_settings[level]
	slider.stylize('book')
	def on_slider_change():
		val_label.text = unicode(slider.value)
		if settlement.tax_settings[level] != slider.value:
			SetTaxSetting(settlement, level, slider.value).execute(settlement.session)
	slider.capture(on_slider_change)
