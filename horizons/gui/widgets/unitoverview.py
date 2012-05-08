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

from fife.extensions import pychan

from horizons.gui.util import load_uh_widget, get_res_icon_path
from horizons.util import Callback
from fife.extensions.pychan.widgets import Icon
from horizons.command.unit import SetStance
from horizons.extscheduler import ExtScheduler
from horizons.component.healthcomponent import HealthComponent
from horizons.component.stancecomponent import DEFAULT_STANCES

class StanceWidget(pychan.widgets.Container):
	"""Widget used for setting up the stance for one instance"""
	def __init__(self, **kwargs):
		super(StanceWidget, self).__init__(size=(245,50), **kwargs)
		widget = load_uh_widget('stancewidget.xml')
		self.addChild(widget)
		ExtScheduler().add_new_object(self.refresh, self, run_in=0.3, loops=-1)

	def init(self, instance):
		self.instance = instance
		self.toggle_stance()
		events = dict( (i.NAME, Callback(self.set_stance, i) ) for i in DEFAULT_STANCES )
		self.mapEvents( events )

	def beforeShow(self):
		super(StanceWidget, self).beforeShow()
		ExtScheduler().rem_all_classinst_calls(self)
		ExtScheduler().add_new_object(self.refresh, self, run_in=1, loops=-1)

	def refresh(self):
		if not self.isVisible():
			# refresh not needed
			ExtScheduler().rem_all_classinst_calls(self)
			return
		self.toggle_stance()

	def remove(self, caller=None):
		"""Removes instance ref"""
		ExtScheduler().rem_all_classinst_calls(self)
		self.mapEvents({})
		self.instance = None

	def set_stance(self, stance):
		SetStance(self.instance, stance).execute(self.instance.session)
		self.toggle_stance()

	def toggle_stance(self):
		for stance in DEFAULT_STANCES:
			self.findChild(name=stance.NAME).set_inactive()
		self.findChild(name=self.instance.stance.NAME).set_active()

class HealthWidget(pychan.widgets.Container):
	"""Widget that shows a health bar for an unit"""
	def __init__(self, **kwargs):
		super(HealthWidget, self).__init__(size=(50,25), **kwargs)
		widget = load_uh_widget('healthwidget.xml')
		self.addChild(widget)

	def init(self, instance):
		self.instance = instance
		self.draw_health()
		health_component = self.instance.get_component(HealthComponent)
		if not health_component.has_damage_dealt_listener(self.draw_health):
			health_component.add_damage_dealt_listener(self.draw_health)

	def draw_health(self, caller=None):
		health_component = self.instance.get_component(HealthComponent)
		max_health = int(health_component.max_health)
		health = int(health_component.health)
		self.findChild(name='health_label').text = "{health}/{max_health}".format(health=health, max_health=max_health)
		self.findChild(name='health_bar').progress = int(health * 100. / max_health)

	def remove(self, caller=None):
		health_component = self.instance.get_component(HealthComponent)
		if health_component.has_damage_dealt_listener(self.draw_health):
			health_component.remove_damage_dealt_listener(self.draw_health)
		self.instance = None

class WeaponStorageWidget(pychan.widgets.HBox):
	"""Widget that shows a small overview for one instance weapons"""
	def init(self, instance):
		self.instance = instance
		self.update()

	def remove(self, caller=None):
		self.instance = None

	def update(self):
		self.removeAllChildren()
		weapons_added = False
		if hasattr(self.instance, 'get_weapon_storage'):
			storage = self.instance.get_weapon_storage()
			for weapon, amount in storage:
				weapons_added = True
				icon_image = get_res_icon_path(weapon, 24)
				icon_tooltip = self.instance.session.db.get_res_name(weapon)+': '+str(amount)
				icon = Icon(image=icon_image, helptext=icon_tooltip)
				self.addChild(icon)
		if not weapons_added:
			icon_image = "content/gui/icons/resources/none.png"
			icon = Icon(image=icon_image, helptext=_("none"))
			self.addChild(icon)

