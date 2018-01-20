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

from horizons.command.uioptions import SetTaxSetting
from horizons.component.namedcomponent import NamedComponent
from horizons.constants import SETTLER
from horizons.gui.util import create_resource_icon, get_happiness_icon_and_helptext
from horizons.i18n import gettext_lazy as LazyT
from horizons.messaging import SettlerUpdate
from horizons.util.loaders.actionsetloader import ActionSetLoader
from horizons.util.python.callback import Callback

from .overviewtab import OverviewTab


class SettlerOverviewTab(OverviewTab):
	widget = 'overview_settler.xml'
	helptext = LazyT("Settler overview")

	def init_widget(self):
		super().init_widget()
		name = self.instance.settlement.get_component(NamedComponent).name
		self.widget.findChild(name="headline").text = name
		setup_tax_slider(self.widget.child_finder('tax_slider'),
		                 self.widget.child_finder('tax_val_label'),
		                 self.instance.settlement,
		                 self.instance.level)

		taxes = self.instance.settlement.tax_settings[self.instance.level]
		self.widget.child_finder('tax_val_label').text = str(taxes)
		action_set = ActionSetLoader.get_set(self.instance._action_set_id)
		action_gfx = list(action_set.items())[0][1]
		image = list(action_gfx[45].keys())[0]
		self.widget.findChild(name="building_image").image = image

	def on_settler_level_change(self, message):
		assert isinstance(message, SettlerUpdate)
		setup_tax_slider(self.widget.child_finder('tax_slider'),
		                 self.widget.child_finder('tax_val_label'),
		                 self.instance.settlement,
		                 message.level)
		taxes = self.instance.settlement.tax_settings[self.instance.level]
		self.widget.child_finder('tax_val_label').text = str(taxes)
		imgs = list(ActionSetLoader.get_set(self.instance._action_set_id).items())[0][1]
		self.widget.findChild(name="building_image").image = list(imgs[45].keys())[0]

	def show(self):
		super().show()
		SettlerUpdate.subscribe(self.on_settler_level_change, sender=self.instance)

	def hide(self):
		SettlerUpdate.discard(self.on_settler_level_change, sender=self.instance)
		super().hide()

	def refresh(self):
		image, helptext = get_happiness_icon_and_helptext(self.instance.happiness, self.instance.session)
		self.widget.child_finder('happiness_label').image = image
		self.widget.child_finder('happiness_label').helptext = helptext
		self.widget.child_finder('happiness').progress = self.instance.happiness
		self.widget.child_finder('inhabitants').text = "{}/{}".format(
		                                               self.instance.inhabitants,
		                                               self.instance.inhabitants_max)
		self.widget.child_finder('taxes').text = str(self.instance.last_tax_payed)
		self.update_consumed_res()
		name = self.instance.settlement.get_component(NamedComponent).name
		self.widget.findChild(name="headline").text = name
		events = {
				'headline': Callback(self.instance.session.ingame_gui.show_change_name_dialog,
				                     self.instance.settlement)
		         }
		self.widget.mapEvents(events)
		super().refresh()

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
	step_count = int((SETTLER.TAX_SETTINGS_MAX - SETTLER.TAX_SETTINGS_MIN) / SETTLER.TAX_SETTINGS_STEP)
	slider.steps = [SETTLER.TAX_SETTINGS_MIN + SETTLER.TAX_SETTINGS_STEP * i for i in
			range(step_count)]
	slider.value = settlement.tax_settings[level]
	def on_slider_change():
		val_label.text = str(slider.value)
		if settlement.tax_settings[level] != slider.value:
			SetTaxSetting(settlement, level, slider.value).execute(settlement.session)
	slider.capture(on_slider_change)
