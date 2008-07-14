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

import game.main

class TabWidget(object):
	"""Used to create menus for buildings, ships, etc. Uses multiple tabs."""

	def __init__(self, object_id, object_list, tabs=[]):
		self.object_id = object_id
		self.object_list = object_list
		self.tabs = []
		self.widget = game.main.fife.pychan.loadXML('content/gui/tab_widget/tab_main.xml')
		self.widget.stylize('menu')
		self.widget.active = 0 # index of the currently active tab
		for index, tab in enumerate(tabs):
			widg = game.main.fife.pychan.loadXML(tab[0]) # load menu
			widg.stylize('menu')
			self.tabs.append(widg)
			button = self.widget.findChild(name=str(index)) # load button
			button.up_image = tab[1]
			button.capture(game.main.fife.pychan.tools.callbackWithArguments(self.load_tab, index))
		print self.tabs
		self.widget.findChild(name='content').addChild(self.tabs[self.widget.active])
		self.widget.findChild(name='content').adaptLayout()

	def load_tab(self, id):
		print id
		tab1 = self.widget.findChild(name=(str(id)))
		contentarea = self.widget.findChild(name='content')
		contentarea.removeChild(self.tabs[self.widget.active])
		contentarea.addChild(self.tabs[id])
		contentarea.adaptLayout()
		self.widget.active = id

	def show(self):
		self.widget.show()

	def hide(self):
		self.widget.hide()