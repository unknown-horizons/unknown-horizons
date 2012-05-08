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

from horizons.gui.tabs.tabinterface import TabInterface

from horizons.component.namedcomponent import NamedComponent


class OverviewTab(TabInterface):
	has_stance = False
	def __init__(self, instance, widget='overviewtab.xml',
	             icon_path='content/gui/icons/tabwidget/common/building_overview_%s.png'):
		super(OverviewTab, self).__init__(widget=widget, icon_path=icon_path)
		self.instance = instance
		self.init_values()
		self.helptext = _("Overview")

		if self.__class__.has_stance:
			self.init_stance_widget()

		# set player emblem
		if self.widget.child_finder('player_emblem'):
			emblem = 'content/gui/images/tabwidget/emblems/emblem_%s.png'
			if self.instance.owner is not None:
				self.widget.child_finder('player_emblem').image = emblem % self.instance.owner.color.name
			else:
				self.widget.child_finder('player_emblem').image = emblem % 'no_player'


	def refresh(self):
		if (hasattr(self.instance, 'name') or self.instance.has_component(NamedComponent)) and self.widget.child_finder('name'):
			name_widget = self.widget.child_finder('name')
			# Named objects can't be translated.
			if self.instance.has_component(NamedComponent):
				name_widget.text = self.instance.get_component(NamedComponent).name
			else:
				name_widget.text = _(self.instance.name)

		if hasattr(self.instance, 'running_costs') and \
		   self.widget.child_finder('running_costs'):
			self.widget.child_finder('running_costs').text = \
			    unicode( self.instance.running_costs )

		self.widget.adaptLayout()

	def show(self):
		super(OverviewTab, self).show()
		if not self.instance.has_change_listener(self.refresh):
			self.instance.add_change_listener(self.refresh)
		if not self.instance.has_remove_listener(self.on_instance_removed):
			self.instance.add_remove_listener(self.on_instance_removed)
		if hasattr(self.instance, 'settlement') and \
		   self.instance.settlement is not None and \
		   not self.instance.settlement.has_change_listener(self._schedule_refresh):
			# listen for settlement name changes displayed as tab headlines
			self.instance.settlement.add_change_listener(self._schedule_refresh)

	def hide(self):
		super(OverviewTab, self).hide()
		if self.instance is not None:
			if self.instance.has_change_listener(self.refresh):
				self.instance.remove_change_listener(self.refresh)
			if self.instance.has_remove_listener(self.on_instance_removed):
				self.instance.remove_remove_listener(self.on_instance_removed)
		if hasattr(self.instance, 'settlement') and \
		   self.instance.settlement is not None and \
		   self.instance.settlement.has_change_listener(self._schedule_refresh):
			self.instance.settlement.remove_change_listener(self._schedule_refresh)

	def on_instance_removed(self):
		self.on_remove()
		self.instance = None

	def init_stance_widget(self): # call for tabs with stances
		stance_widget = self.widget.findChild(name='stance')
		stance_widget.init(self.instance)
		self.add_remove_listener(stance_widget.remove)


class GroundUnitOverviewTab(OverviewTab):
	has_stance = True
	def __init__(self, instance):
		super(GroundUnitOverviewTab, self).__init__(
			widget = 'overview_groundunit.xml',
			instance = instance)
		self.helptext = _("Unit overview")
		health_widget = self.widget.findChild(name='health')
		health_widget.init(self.instance)
		self.add_remove_listener(health_widget.remove)
		weapon_storage_widget = self.widget.findChild(name='weapon_storage')
		weapon_storage_widget.init(self.instance)
		self.add_remove_listener(weapon_storage_widget.remove)

class FireStationOverviewTab(OverviewTab):
	def  __init__(self, instance):
		super(FireStationOverviewTab, self).__init__(
			widget = 'overview_firestation.xml',
			instance = instance
		)
