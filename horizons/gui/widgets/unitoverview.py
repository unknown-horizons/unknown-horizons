# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
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
from horizons.util.gui import load_uh_widget, get_res_icon
from horizons.util import Callback
from horizons.gui.widgets import TooltipIcon

class StanceWidget(pychan.widgets.Container):
	"""Widget used for setting up the stance for one instance"""
	def __init__(self, **kwargs):
		super(StanceWidget, self).__init__(size=(245,50), **kwargs)
		widget = load_uh_widget('stancewidget.xml')
		self.addChild(widget)

	def init(self, instance):
		self.instance = instance
		self.toggle_stance()
		self.mapEvents({
			'aggressive': Callback(self.set_stance, 'aggressive'),
			'hold_ground': Callback(self.set_stance, 'hold_ground'),
			'none': Callback(self.set_stance, 'none'),
			'flee': Callback(self.set_stance, 'flee')
			})

	def remove(self, caller=None):
		"""Removes instance ref"""
		self.mapEvents({})
		self.instance = None

	def set_stance(self, stance):
		self.instance.set_stance(stance)
		self.toggle_stance()

	def toggle_stance(self):
		self.findChild(name='aggressive').set_inactive()
		self.findChild(name='hold_ground').set_inactive()
		self.findChild(name='none').set_inactive()
		self.findChild(name='flee').set_inactive()
		self.findChild(name=self.instance.stance).set_active()

class HealthWidget(pychan.widgets.Container):
	"""Widget that shows a health bar for an unit"""
	def __init__(self, **kwargs):
		super(HealthWidget, self).__init__(size=(50,25), **kwargs)
		widget = load_uh_widget('healthwidget.xml')
		self.addChild(widget)

	def init(self, instance):
		self.instance = instance
		self.draw_health()
		health_component = self.instance.get_component('health')
		if not health_component.has_damage_dealt_listener(self.draw_health):
			health_component.add_damage_dealt_listener(self.draw_health)

	def draw_health(self, caller=None):
		health_component = self.instance.get_component('health')
		max_health = int(health_component.max_health)
		health = int(health_component.health)
		self.findChild(name='health_label').text = unicode(str(health)+'/'+str(max_health))
		self.findChild(name='health_bar').progress = int(health * 100. / max_health)

	def remove(self, caller=None):
		health_component = self.instance.get_component('health')
		if health_component.has_damage_dealt_listener(self.draw_health):
			health_component.remove_damage_dealt_listener(self.draw_health)
		self.instance = None

class WeaponStorageWidget(pychan.widgets.HBox):
	"""Widget that shows a small overview for one instance weapons"""
	def init(self, instance):
		self.instance = instance
		self.update()

	def remove(self, caller = None):
		self.instance = None

	def update(self):
		self.removeAllChildren()
		weapons_added = False
		if hasattr(self.instance, 'get_weapon_storage'):
			storage = self.instance.get_weapon_storage()
			for weapon, amount in storage:
				weapons_added = True
				icon_image = get_res_icon(weapon)[2]
				icon_tooltip = self.instance.session.db.get_res_name(weapon)+': '+str(amount)
				icon = TooltipIcon(image = icon_image, tooltip = icon_tooltip)
				self.addChild(icon)
		if not weapons_added:
			icon_image = "content/gui/icons/resources/none.png"
			icon = TooltipIcon(image = icon_image, tooltip = _("none"))
			self.addChild(icon)

