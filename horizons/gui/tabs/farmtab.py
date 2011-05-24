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
from fife.extensions import pychan

from horizons.gui.widgets  import TooltipButton
from horizons.gui.mousetools  import BuildingTool
from horizons.gui.tabs import OverviewTab
from horizons.i18n import load_xml_translated
from horizons.util import Callback
from horizons.util import Rect, Circle, Point
from horizons.util.shapes.radiusshape import RadiusRect
from horizons.world.providerhandler import ProviderHandler
from horizons import main
from horizons.entities import Entities

class BuildRelatedTab(OverviewTab):
	relatedfields_gui_xml = "relatedfields.xml"

	def  __init__(self, instance, icon_path='content/gui/icons/tabwidget/production/related_%s.png'):
		super(BuildRelatedTab, self).__init__(
			widget = 'overview_buildrelated.xml',
			instance = instance, 
			icon_path='content/gui/icons/tabwidget/production/related_%s.png'
		)
		self.tooltip = _("Build related fields")

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		
		
		# remove old field data
		parent_container = self.widget.child_finder('related_fields')
		while len(parent_container.children) > 0:
			parent_container.removeChild(parent_container.children[0])

		# Load all related Fields of this Farm
		building_ids = self.instance.session.db.cached_query("SELECT related_building FROM related_buildings where building = ?", self.instance.id)
		build_buttons = list()

		gui = load_xml_translated(self.relatedfields_gui_xml)
		container = gui.findChild(name="fields_container")
		for x,building_id in enumerate(sorted(building_ids)):
			retVal = self._create_build_buttons(building_id[0], container)
			if retVal != None:
				build_buttons.append(retVal)
				
				if x%3==0:
					container.stylize('menu_black')
					parent_container.addChild(container)
				else:
					container = gui.findChild(name="fields_container")
				
		for name, cls in build_buttons:
			self.widget.mapEvents({ name: Callback(self.buildField, cls) })
		
		super(BuildRelatedTab, self).refresh()
	
	def _create_build_buttons(self, id, container):
		building = Entities.buildings[id]( \
					session=self.instance.session, \
					x=0, y=0, \
					rotation=45, owner=self.instance.owner, \
					island=self.instance.island, \
					instance=None)
		
		# Check if the level of the building is lower or same as the settler level
		if building.level <= self.instance.owner.settler_level:
			# Display Buildings
			build_button = TooltipButton(name="build"+str(id), tooltip=_("Build")+" "+_(unicode(building.name)))
			build_button_bg = pychan.widgets.Icon(image="content/gui/images/buttons/buildmenu_button_bg.png")				
			
			buildmenu_image_path = "content/gui/icons/buildmenu/";
			
			build_button.up_image=buildmenu_image_path+building.name.lower().replace(" ", "")+".png"
			build_button.down_image=buildmenu_image_path+building.name.lower().replace(" ", "")+"_h.png"
			build_button.hover_image=buildmenu_image_path+building.name.lower().replace(" ", "")+"_h.png"
				
			container.findChild(name="build_button_container").addChild(build_button)
			container.findChild(name="build_button_bg_container").addChild(build_button_bg)
			
			return (build_button.name, building)
		else:
			return None
	
	def buildField(self, building):
		self.hide()
		
		# deselect all
		for instance in self.instance.session.selected_instances:
			instance.deselect()
		self.instance.session.selected_instances.clear()
		
		if hasattr(building, 'show_build_menu'):
			building.show_build_menu()
		self.instance.session.cursor = BuildingTool(self.instance.session, building, None)

