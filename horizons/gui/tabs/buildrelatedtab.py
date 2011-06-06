# -*- coding: utf-8 -*-
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
from fife.extensions.pychan.widgets import Icon

from horizons.gui.widgets  import TooltipButton
from horizons.gui.mousetools  import BuildingTool
from horizons.gui.tabs import OverviewTab
from horizons.util.gui import load_uh_widget
from horizons.util import Callback
from horizons.entities import Entities

class BuildRelatedTab(OverviewTab):
	"""
	Adds a special tab to each production building with at least one entry in
	the table related_buildings. This tab acts as modified build menu tab and
	only displays those fields actually related to the selected building.
	Used to indicate the range of a building while e.g. building fields for it.
	"""
	relatedfields_gui_xml = 'relatedfields.xml'

	def  __init__(self, instance, icon_path = 'content/gui/icons/tabwidget/production/related_%s.png'):
		super(BuildRelatedTab, self).__init__(
		    widget = 'overview_buildrelated.xml',
		    instance = instance,
		    icon_path = 'content/gui/icons/tabwidget/production/related_%s.png'
		)
		self.tooltip = _("Build related fields")

	def refresh(self):
		"""
		This function is called by the TabWidget to redraw the widget.
		"""
		# remove old field data
		parent_container = self.widget.child_finder('related_fields')
		while len(parent_container.children) > 0:
			parent_container.removeChild(parent_container.children[0])

		# Load all related Fields of this Farm
		sql = "SELECT related_building FROM related_buildings WHERE building = ?"
		building_ids = self.instance.session.db.cached_query(sql, self.instance.id)

		container = self.__get_new_container()
		counter = 0
		for building_id in sorted(building_ids):
			if self._create_build_buttons(building_id[0], container):
				counter += 1
				if counter % 3 == 0:
				# This is here because we can only check if a building was added
					parent_container.addChild(container)
					container = self.__get_new_container()

		if counter % 3 != 0:
			# Still need to add last container
			parent_container.addChild(container)

		super(BuildRelatedTab, self).refresh()

	def __get_new_container(self):
		"""
		Loads a background container xml file. Returns the loaded widget.
		"""
		gui = load_uh_widget(self.relatedfields_gui_xml)
		container = gui.findChild(name="fields_container")
		return container


	def _create_build_buttons(self, building_id, container):
		sql = "SELECT settler_level, name FROM building WHERE id = ?"
		(level, name) = self.instance.session.db.cached_query(sql, building_id)[0]

		# Check if the level of the building is lower or same as the settler level
		if level <= self.instance.owner.settler_level:
			buildmenu_image_path = "content/gui/icons/buildmenu/"
			path = buildmenu_image_path + name.lower().replace(" ", "")

			build_button = TooltipButton(name="build"+str(building_id), \
			                             tooltip=_("Build")+" "+_(unicode(name)))
			build_button.up_image = path + ".png"
			build_button.down_image = path + "_h.png"
			build_button.hover_image = path + "_h.png"
			build_button.capture(Callback(self.buildField, building_id))

			container.findChild(name="build_button_container").addChild(build_button)

			build_button_bg = Icon(image="content/gui/images/buttons/buildmenu_button_bg.png")
			container.findChild(name="build_button_bg_container").addChild(build_button_bg)

			return True
		else:
			# No button built
			return False

	def buildField(self, building_id):
		self.hide()

		# deselect all
		for instance in self.instance.session.selected_instances:
			instance.deselect()
		self.instance.session.selected_instances.clear()

		self.instance.session.cursor = BuildingTool(self.instance.session, \
		                                            Entities.buildings[building_id], \
		                                            None)
