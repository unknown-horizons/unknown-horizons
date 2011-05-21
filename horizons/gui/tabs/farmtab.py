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
from horizons.world.building.nature import Field
from horizons.world.building.building import BasicBuilding
from horizons.world.providerhandler import ProviderHandler
from horizons import main
from horizons.entities import Entities

class BuildingRelatedFieldsTab(OverviewTab):
	relatedfields_gui_xml = "relatedfields.xml"

	def  __init__(self, instance, icon_path='content/gui/icons/tabwidget/production/related_%s.png'):
		super(BuildingRelatedFieldsTab, self).__init__(
			widget = 'overview_buildingrelatedfields.xml',
			instance = instance, 
			icon_path='content/gui/icons/tabwidget/production/related_%s.png'
		)
		self.tooltip = _("Building related Fields")

	def refresh(self):
		"""This function is called by the TabWidget to redraw the widget."""
		
		
		# remove old field data
		parent_container = self.widget.child_finder('related_fields')
		while len(parent_container.children) > 0:
			parent_container.removeChild(parent_container.children[0])

		# Load all related Fields of this Farm
		building_ids = main.db.cached_query("SELECT id FROM building where class_type = ?", "Field")

		for _id in sorted(building_ids):
			gui = load_xml_translated(self.relatedfields_gui_xml)
			container = gui.findChild(name="fields_container")
			
			building = Entities.buildings[_id[0]]( \
				session=self.instance.session, \
				x=0, y=0, \
				rotation=45, owner=self.instance.owner, \
				island=self.instance.island, \
				instance=None)
			
			# Display Buildings
			build_button = TooltipButton(name="build"+str(_id[0]), tooltip=_("Build"))
			
			buildmenu_image_path = "content/gui/icons/buildmenu/";
			if building.name.lower().find("potato") > -1:
				build_button.up_image=buildmenu_image_path+"potatoes.png"
				build_button.down_image=buildmenu_image_path+"potatoes_h.png"
				build_button.hover_image=buildmenu_image_path+"potatoes_h.png"
			else:
				build_button.up_image=buildmenu_image_path+building.name.lower().replace(" ", "")+".png"
				build_button.down_image=buildmenu_image_path+building.name.lower().replace(" ", "")+"_h.png"
				build_button.hover_image=buildmenu_image_path+building.name.lower().replace(" ", "")+"_h.png"
				
			container.findChild(name="build_button_container").addChild(build_button)
			
			container.findChild(name="name").text = unicode(building.name)
			
			container.stylize('menu_black')
			parent_container.addChild(container)
			
			self.widget.mapEvents({ 'build'+str(_id[0]): Callback(self.buildField, building) })

		super(BuildingRelatedFieldsTab, self).refresh()
	
	def buildField(self, building):
		self.hide()
		
		# deselect all
		for instance in self.instance.session.selected_instances:
			instance.deselect()
		self.instance.session.selected_instances.clear()
		
		if hasattr(building, 'show_build_menu'):
			building.show_build_menu()
		self.instance.session.cursor = BuildingTool(self.instance.session, building, None)

