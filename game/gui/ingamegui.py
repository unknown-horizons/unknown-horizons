# ###################################################
# Copyright (C) 2008 The OpenAnnoTeam
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

class IngameGui(object):
	"""Class handling all the ingame gui events."""
	def __init__(self):
		self.gui = {}
		self.gui['status'] = game.main.fife.pychan.loadXML('content/gui/status.xml')
		self.gui['build'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build.xml')
		self.gui['build_tab0'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build_tab0.xml')
		self.gui['build_tab1'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build_tab1.xml')
		self.gui['build_tab2'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build_tab2.xml')
		self.gui['build_tab3'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build_tab3.xml')
		self.gui['build_tab4'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build_tab4.xml')
		self.gui['build_tab5'] = game.main.fife.pychan.loadXML('content/gui/build_menu/hud_build_tab5.xml')
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
		self.gui['buildinfo'] = game.main.fife.pychan.loadXML('content/gui/hud_buildinfo.xml')
		self.gui['chat'] = game.main.fife.pychan.loadXML('content/gui/hud_chat.xml')
		self.gui['cityinfo'] = game.main.fife.pychan.loadXML('content/gui/hud_cityinfo.xml')
		self.gui['res'] = game.main.fife.pychan.loadXML('content/gui/hud_res.xml')
		self.gui['fertility'] = game.main.fife.pychan.loadXML('content/gui/hud_fertility.xml')
		self.gui['ship'] = game.main.fife.pychan.loadXML('content/gui/hud_ship.xml')
		self.gui['ship'].mapEvents({
			'foundSettelmentButton' : self._ship_build
		})
		self.gui['main'] = game.main.fife.pychan.loadXML('content/gui/hud_main.xml')
		self.toggle_visible('main')
		self.gui['main'].mapEvents({
			'build' : game.main.fife.pychan.tools.callbackWithArguments(self.toggle_visible, 'build'),
			'zoomIn' : game.main.game.view.zoom_in,
			'zoomOut' : game.main.game.view.zoom_out,
			'rotateRight' : game.main.game.view.rotate_right,
			'rotateLeft' : game.main.game.view.rotate_left,
			'escButton' : game.main.gui.show
		})

	def status_set(self, label, value):
		"""Sets a value on the status bar.
		@var label: str containing the name of the label to be set.
		@var value: value the Label is to be set to.
		"""
		foundlabel = self.gui['status'].findChild(name=label)
		foundlabel._setText(value)
		foundlabel.resizeToContent()
		self.gui['status'].resizeToContent()

	def _ship_build(self):
		"""Calls the Games build_object class."""
		game.main.game.selected_instance._instance.say('')
		game.main.game.cursor = BuildingTool(1, game.main.game.selected_instance)

	def toggle_visible(self, guiname):
		"""Toggles whether a gui is visible or not.
		@var guiname: str with the guiname.
		"""
		if self.gui[guiname].isVisible():
			self.gui[guiname].hide()
		else:
			self.gui[guiname].show()

	def build_menu_show(self, num):
		"""Shows the selected build menu
		@var num: int with the menu id
		"""
		self.active_build.hide()
		self.active_build = self.gui['build' + str(num)]
		self.active_build.show()

	def build_load_tab(self, num):
		"""Loads a subcontainer into the build menu and changes the tabs background.
		@var num: number representing the tab to load.
		"""
		tab1 = self.gui['build'].findChild(name=('tab'+str(self.active_build)))
		tab2 = self.gui['build'].findChild(name=('tab'+str(num)))
		activetabimg, nonactiveimg= tab1._getImage(), tab2._getImage()
		tab1._setImage(nonactiveimg)
		tab2._setImage(activetabimg)
		contentarea = self.gui['build'].findChild(name='content')
		contentarea.removeChild(self.gui['build_tab'+str(self.active_build)])
		#self.gui['build_tab'+str(self.active_build)].hide()
		#self.gui['build_tab'+str(num)].show()
		contentarea.addChild(self.gui['build_tab'+str(num)])
		contentarea.adaptLayout()
		self.active_build = num
