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

from fife.extensions.pychan.widgets import Icon, ImageButton

from horizons.gui.tabs import OverviewTab
from horizons.gui.util import load_uh_widget
from horizons.util import Callback
from horizons.entities import Entities
from horizons.component.selectablecomponent import SelectableComponent

class BuildRelatedTab(OverviewTab):
	"""
	Adds a special tab to each production building with at least one entry in
	the table related_buildings. This tab acts as modified build menu tab and
	only displays those buildings actually related to the selected building.
	Examples: tree for lumberjack; pavilion, school, etc. for inhabitants.
	"""
	template_gui_xml = 'related_buildings_container.xml'

	def  __init__(self, instance, widget='related_buildings.xml',
	              icon_path='content/gui/icons/tabwidget/production/related_%s.png'):
		super(BuildRelatedTab, self).__init__(widget=widget, instance=instance, icon_path=icon_path)
		self.helptext = _("Build related buildings")

	def refresh(self):
		"""
		This function is called by the TabWidget to redraw the widget.
		"""
		# remove old data
		parent_container = self.widget.child_finder('related_buildings')
		while len(parent_container.children) > 0:
			parent_container.removeChild(parent_container.children[0])

		# load all related buildings from DB
		building_ids = self.instance.session.db.get_related_building_ids_for_menu(self.instance.id)
		sorted_ids = sorted([(b, Entities.buildings[b].settler_level) for b in building_ids], key=lambda x : x[1])
		container = self.__get_new_container()
		self.current_row = min(building[1] for building in sorted_ids)
		for building_id, level in sorted_ids:
			if level <= self.instance.owner.settler_level: # available in build menu?
				button = self._create_build_buttons(building_id, container)
				# check whether to start new line (for new increment row)
				if level > self.current_row:
					self.current_row = level
					parent_container.addChild(container)
					container = self.__get_new_container()
				container.findChild(name="build_button_container").addChild(button)
				button_bg = Icon(image="content/gui/images/buttons/buildmenu_button_bg.png")
				container.findChild(name="build_button_bg_container").addChild(button_bg)
		# Still need to add last container
		parent_container.addChild(container)
		super(BuildRelatedTab, self).refresh()

	def __get_new_container(self):
		"""
		Loads a background container xml file. Returns the loaded widget.
		"""
		gui = load_uh_widget(self.template_gui_xml)
		return gui.findChild(name="buildings_container")

	def _create_build_buttons(self, building_id, container):
		# {{mode}} in double braces because it is replaced as a second step
		path = "content/gui/icons/buildmenu/{id:03d}{{mode}}.png".format(id=building_id)
		helptext = self.instance.session.db.get_building_tooltip(building_id)
		build_button = ImageButton(name="build{id}".format(id=building_id), helptext=helptext)
		build_button.up_image = path.format(mode='')
		build_button.down_image = build_button.hover_image = path.format(mode='_h')
		build_button.capture(Callback(self.build_related, building_id))
		return build_button

	def build_related(self, building_id):
		self.hide()
		# deselect all
		for instance in self.instance.session.selected_instances:
			instance.get_component(SelectableComponent).deselect()
		self.instance.session.selected_instances.clear()

		self.instance.session.set_cursor('building', Entities.buildings[building_id],
		                                             ship=None,
		                                             build_related=self.instance)
