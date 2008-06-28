# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

from buildingtool import BuildingTool
import game.main
import fife
from living import livingObject
from messagewidget import MessageWidget

class IngameGui(livingObject):
	"""Class handling all the ingame gui events."""
	def begin(self):
		super(IngameGui, self).begin()
		self.gui = {}

		self.gui['encyclopedia'] = game.main.fife.pychan.loadXML('content/gui/encyclopedia_button.xml')
		self.toggle_visible('encyclopedia')

		self.gui['topmain'] = game.main.fife.pychan.loadXML('content/gui/top_main.xml')
		self.gui['topmain'].position = (
			game.main.fife.settings.getScreenWidth()/2 - self.gui['topmain'].size[0]/2,
			5
		)
		self.message_widget = MessageWidget(self.gui['topmain'].position[0] + self.gui['topmain'].size[0], 5)
		self.toggle_visible('topmain')

		self.gui['gamemenu'] = game.main.fife.pychan.loadXML('content/gui/gamemenu_button.xml')
		self.gui['gamemenu'].position = (
			game.main.fife.settings.getScreenWidth() - self.gui['gamemenu'].size[0] - 5,
			5
		)
		self.gui['gamemenu'].mapEvents({
			'gameMenuButton' : game.main.showPause
		})
		self.toggle_visible('gamemenu')

		self.gui['minimap_toggle'] = game.main.fife.pychan.loadXML('content/gui/minimap_toggle_button.xml')
		self.gui['minimap_toggle'].position = (
			game.main.fife.settings.getScreenWidth() - self.gui['minimap_toggle'].size[0] - 5,
			game.main.fife.settings.getScreenHeight() - self.gui['minimap_toggle'].size[1]
		)
		self.toggle_visible('minimap_toggle')
		self.gui['minimap_toggle'].mapEvents({
			'minimapToggle' : game.main.fife.pychan.tools.callbackWithArguments(self.toggle_visible, 'minimap')
		})

		self.gui['minimap'] = game.main.fife.pychan.loadXML('content/gui/minimap.xml')
		self.gui['minimap'].position = (
				game.main.fife.settings.getScreenWidth() - self.gui['minimap'].size[0] - self.gui['minimap_toggle'].size[0],
				game.main.fife.settings.getScreenHeight() - self.gui['minimap'].size[1]
		)
		self.toggle_visible('minimap')
		self.gui['minimap'].mapEvents({
			'zoomIn' : game.main.session.view.zoom_in,
			'zoomOut' : game.main.session.view.zoom_out,
			'rotateRight' : game.main.session.view.rotate_right,
			'rotateLeft' : game.main.session.view.rotate_left
		})

		self.gui['leftPanel'] = game.main.fife.pychan.loadXML('content/gui/left_panel.xml')
		self.gui['leftPanel'].position = (
			5,
			game.main.fife.settings.getScreenHeight()/2 - self.gui['minimap'].size[1]/2
		)
		self.toggle_visible('leftPanel')
		self.gui['leftPanel'].mapEvents({
			'build' : game.main.fife.pychan.tools.callbackWithArguments(self.toggle_visible, 'build')
		})

		self.gui['status'] = game.main.fife.pychan.loadXML('content/gui/status.xml')
		self.gui['build'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build.xml')
		self.gui['build'].stylize('menu')
		if game.main.fife.settings.getScreenWidth()/2 + self.gui['build'].size[0]/2 > self.gui['minimap'].position[0] :
			self.gui['build'].position = (
				self.gui['minimap'].position[0] - self.gui['build'].size[0] - 5,
				game.main.fife.settings.getScreenHeight() - self.gui['build'].size[1]
			)
		else:
			self.gui['build'].position = (
				game.main.fife.settings.getScreenWidth()/2 - self.gui['build'].size[0]/2,
				game.main.fife.settings.getScreenHeight() - self.gui['build'].size[1]
			)

		for i in range(0,6):
			self.gui['build_tab'+str(i)] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build_tab'+str(i)+'.xml')
			self.gui['build_tab'+str(i)].stylize('menu')
		self.gui['build'].findChild(name='content').addChild(self.gui['build_tab0']) #Add first menu
		self.gui['build'].findChild(name='content').adaptLayout()
		self.active_build = 0
		self.gui['build'].mapEvents({
			'servicesTab' : game.main.fife.pychan.tools.callbackWithArguments(self.build_load_tab, 0),
			'residentsTab' : game.main.fife.pychan.tools.callbackWithArguments(self.build_load_tab, 1),
			'companiesTab' : game.main.fife.pychan.tools.callbackWithArguments(self.build_load_tab, 2),
			'militaryTab' : game.main.fife.pychan.tools.callbackWithArguments(self.build_load_tab, 3),
			'streetsTab' : game.main.fife.pychan.tools.callbackWithArguments(self.build_load_tab, 4),
			'specialTab' : game.main.fife.pychan.tools.callbackWithArguments(self.build_load_tab, 5)
		})
		self.gui['build_tab0'].mapEvents({
			'store-1' : game.main.fife.pychan.tools.callbackWithArguments(self._build, 2),
		})
		self.gui['build_tab1'].mapEvents({
			'resident-1' : game.main.fife.pychan.tools.callbackWithArguments(self._build, 3),
		})
		self.gui['build_tab2'].mapEvents({
			'weaver-1' : game.main.fife.pychan.tools.callbackWithArguments(self._build, 7),
			'lumberjack-1' : game.main.fife.pychan.tools.callbackWithArguments(self._build, 8)
		})
		self.gui['build_tab4'].mapEvents({
			'street-1' : game.main.fife.pychan.tools.callbackWithArguments(self._build, 15),
			'bridge-1' : game.main.fife.pychan.tools.callbackWithArguments(self._build, 16)
		})
		self.gui['buildinfo'] = game.main.fife.pychan.loadXML('content/gui/hud_buildinfo.xml')
		self.gui['chat'] = game.main.fife.pychan.loadXML('content/gui/hud_chat.xml')
		self.gui['cityinfo'] = game.main.fife.pychan.loadXML('content/gui/hud_cityinfo.xml')
		self.gui['res'] = game.main.fife.pychan.loadXML('content/gui/hud_res.xml')
		self.gui['fertility'] = game.main.fife.pychan.loadXML('content/gui/hud_fertility.xml')
		self.gui['ship'] = game.main.fife.pychan.loadXML('content/gui/hud_ship.xml')
		self.gui['ship'].mapEvents({
			'foundSettelmentButton' : self._ship_build
		})

	def end(self):
		super(IngameGui, self).end()

		self.gui['gamemenu'].mapEvents({
			'gameMenuButton' : lambda : None
		})

		self.gui['build'].mapEvents({
			'servicesTab' : lambda : None,
			'residentsTab' : lambda : None,
			'companiesTab' : lambda : None,
			'militaryTab' : lambda : None,
			'streetsTab' : lambda : None,
			'specialTab' : lambda : None
		})
		self.gui['ship'].mapEvents({
			'foundSettelmentButton' : lambda : None
		})
		self.gui['minimap'].mapEvents({
			'zoomIn' : lambda : None,
			'zoomOut' : lambda : None,
			'rotateRight' : lambda : None,
			'rotateLeft' : lambda : None,
		})

		self.gui['minimap_toggle'].mapEvents({
			'minimapToggle' : lambda : None
		})

	def status_set(self, label, value):
		"""Sets a value on the status bar.
		@param label: str containing the name of the label to be set.
		@param value: value the Label is to be set to.
		"""
		foundlabel = self.gui['status'].findChild(name=label)
		foundlabel._setText(value)
		foundlabel.resizeToContent()
		self.gui['status'].resizeToContent()

	def cityname_set(self, name):
		"""Sets the city name at top center

		Show/Hide is handled automatically
		To hide cityname, set name to ''
		@param name: name of the city
		"""
		if(name == ''): 
			self.gui['topmain'].hide()
			return
		foundlabel = self.gui['topmain'].findChild(name='city_name')
		foundlabel._setText(name)
		foundlabel.resizeToContent()
		self.gui['topmain'].resizeToContent()
		self.gui['topmain'].show();

	def _ship_build(self):
		"""Calls the Games build_object class."""
		game.main.session.selected_instance._instance.say('')
		game.main.session.cursor = BuildingTool(game.main.session.entities.buildings[1], game.main.session.selected_instance)

	def show_ship(self, ship):
		self.gui['ship'].findChild(name='buildingNameLabel').text = ship.name+" (Ship type)"
		self.gui['ship'].show()

	def _build(self, building_id):
		"""Calls the games buildingtool class for the building_id.
		@param building_id: int with the building id that is to be built."""
		game.main.session.cursor = BuildingTool(game.main.session.entities.buildings[building_id])

	def toggle_visible(self, guiname):
		"""Toggles whether a gui is visible or not.
		@param guiname: str with the guiname.
		"""
		if self.gui[guiname].isVisible():
			self.gui[guiname].hide()
		else:
			self.gui[guiname].show()

	def build_load_tab(self, num):
		"""Loads a subcontainer into the build menu and changes the tabs background.
		@param num: number representing the tab to load.
		"""
		tab1 = self.gui['build'].findChild(name=('tab'+str(self.active_build)))
		tab2 = self.gui['build'].findChild(name=('tab'+str(num)))
		activetabimg, nonactiveimg= tab1._getImage(), tab2._getImage()
		tab1._setImage(nonactiveimg)
		tab2._setImage(activetabimg)
		contentarea = self.gui['build'].findChild(name='content')
		contentarea.removeChild(self.gui['build_tab'+str(self.active_build)])
		contentarea.addChild(self.gui['build_tab'+str(num)])
		contentarea.adaptLayout()
		self.active_build = num
