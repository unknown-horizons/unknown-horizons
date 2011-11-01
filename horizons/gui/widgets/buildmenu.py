# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2010 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

""" pychan demo app for a dynamic UH buildmenu """

#from pychan_demo import PyChanExample

from fife.extensions import pychan

_DATA = {
	1 :	{
		'Pioneer buildings' : {
			'childs'	: [
				{
					'name' : 'Herder',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Farm: Grows field crops and raises livestock.',
				},
				{
					'name' : 'Weaver',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Weaver: Turns lamb wool into cloth.',
				},
				{
					'name' : 'Clay pit',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Clay pit: Gets clay from deposit.',
				},	
				{
					'name' : 'Clay pit',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Clay pit: Gets clay from deposit.',
				},					
			],
		},
		'Other building group 1' : {
			'childs'	: [
				{
					'name' : 'Herder',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Farm: Grows field crops and raises livestock.',
				},
				{
					'name' : 'Weaver',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Weaver: Turns lamb wool into cloth.',
				},
				{
					'name' : 'Clay pit',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Clay pit: Gets clay from deposit.',
				},		
			],
		},
		'Other building group 2' : {
			'childs'	: [
				{
					'name' : 'Herder',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Farm: Grows field crops and raises livestock.',
				},
				{
					'name' : 'Weaver',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Weaver: Turns lamb wool into cloth.',
				},
				{
					'name' : 'Clay pit',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Clay pit: Gets clay from deposit.',
				},		
			],
		},				
	},
	2 : {
		'Increment 2 group' : {
			'childs'	: [
				{
					'name' : 'Herder',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Farm: Grows field crops and raises livestock.',
				},
				{
					'name' : 'Weaver',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Weaver: Turns lamb wool into cloth.',
				},			
			],
		},
	},
	3 : {
		'Increment 3 group' : {
			'childs'	: [
				{
					'name' : 'Herder',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Farm: Grows field crops and raises livestock.',
				},
				{
					'name' : 'Weaver',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Weaver: Turns lamb wool into cloth.',
				},			
			],
		},	
	},
	4 : {
		'Increment 4 group' : {
			'childs'	: [
				{
					'name' : 'Herder2',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Farm: Grows field crops and raises livestock.',
				},
				{
					'name' : 'Weaver2',
					'img' : 'farm.png',
					'img_h' : 'farm_h.png',
					'tooltip' : 'Weaver: Turns lamb wool into cloth.',
				},			
			],
		},	
	},

}

_ICON_PATH = 'gui/icons/'
_BACKGROUND_COLOR = (0,0,0,0)
_INCREMENTS = _DATA.keys()
_INCREMENTS.sort()
_INCREMENT_FIRST_SHOW = _INCREMENTS[0]

class BuildButton(object):
	""" Special widget: groups a button and a background icon 
	
	@type	container:	object
	@ivar	container:	wrapper widget, use this to add / remove this Button
	@type	icon:	object
	@ivar	icon:	icon widget, used for background gfx
	@type	widget:	object
	@ivar	widget:	the button itself	
	"""
	def __init__(self, data):
		"""
		
		@type	data:	dict
		@param	data:	various data to create the ImageButton
		"""
		self.container = pychan.widgets.Container()
		self.icon = pychan.widgets.Icon(image=_ICON_PATH+"build_button_bg.png")
		self.widget = pychan.widgets.ImageButton(
			up_image=_ICON_PATH+data['img'],
			down_image=_ICON_PATH+data['img'],
			hover_image=_ICON_PATH+data['img_h'],
		)
		self.widget.name = data['name']
		self.container.addChild(self.icon)
		self.container.addChild(self.widget)
		self.container.size = (52,52)
		self.container.base_color = _BACKGROUND_COLOR
		
		self.icon.position = (0,0)
		self.widget.position = (0,0)
		
class NavButton(object):
	""" Special widget: groups a button and a background icon
		provides listeners for mouse hover events to change
		background icon accordingly
		
		@type	container:	object
		@ivar	container:	wrapper widget, use this to add / remove this Button
		@type	icon:	object
		@ivar	icon:	icon widget, used for background gfx
		@type	widget:	object
		@ivar	widget:	the button itself		
	"""
	def __init__(self, increment, level, callback):
		""" 
		
		@type	increment:	int
		@param	increment:	increment the button represents
		@type	level:	str
		@param	level:	filename addition to get the proper button gfx
		@type	callback:	function
		@param	callback:	callback for mousePressed events
		"""
		self.callback = callback
		self.container = pychan.widgets.Container()
		self.icon = pychan.widgets.Icon(image=_ICON_PATH+"tab.png")
		self.widget = pychan.widgets.ToggleButton(
			group = 'increments',
			up_image=_ICON_PATH+"level"+level+"_a.png",
			down_image=_ICON_PATH+"level"+level+"_d.png",
			hover_image=_ICON_PATH+"level"+level+"_h.png"		
		)
		self.widget.base_color = _BACKGROUND_COLOR
		self.widget.background_color = _BACKGROUND_COLOR
		self.widget.name = increment
		self.widget.capture(self.mouse_enter, 'mouseEntered')
		self.widget.capture(self.mouse_exit, 'mouseExited')
		self.widget.capture(self.mouse_pressed, 'mousePressed')
		
		self.container.addChild(self.icon)
		self.container.addChild(self.widget)
		self.container.size = (40,48)
		self.container.base_color = _BACKGROUND_COLOR
		
		self.icon.position = (0,0)
		self.widget.position = (0,0)
		
	def mouse_enter(self, event, widget):
		""" callback for mouse enter events 
		
		@type	event:	object
		@param	event:	pychan ActionEvent
		@type	widget:	object
		@param	widget:	pychan widget which triggered the event		
		"""
		self.icon._setImage(_ICON_PATH+"tab2.png")
	def mouse_exit(self, event, widget):
		""" callback for mouse exit events 
		
		@type	event:	object
		@param	event:	pychan ActionEvent
		@type	widget:	object
		@param	widget:	pychan widget which triggered the event		
		"""
		self.icon._setImage(_ICON_PATH+"tab.png")
	def mouse_pressed(self, event, widget):
		""" callback for mouse pressed events 
		
		@type	event:	object
		@param	event:	pychan ActionEvent
		@type	widget:	object
		@param	widget:	pychan widget which triggered the event
		"""
		self.callback(widget)
		
class Category(object):
	""" Special widget, shows a group name and associated childs 
	
		data dict content (key : content):
			- name:	the name of the building
			- img: filename for "up" image
			- img_h : filename for "down" image
			- tooltip:	tooltip string
	"""
	def __init__(self, group=None, data={}):
		""" 
		@type	group:	str
		@param	group:	group name
		@type	data:	dict
		@param	data:	child definitions of that group
		"""
		self.widget = None
		self.create(group, data)
	def create(self, group=None, data={}):
		""" create the widget according to given data 
		
		@type	group:	str
		@param	group:	group name
		@type	data:	dict
		@param	data:	child definitions of that group		
		"""
		if group is None: return
		if not data: return
		
		self.group = group
		self.data = data
		
		wrapper = pychan.widgets.VBox(padding=0, opaque=0)
		wrapper.base_color = _BACKGROUND_COLOR
		lbl = pychan.widgets.Label()
		lbl.text = group
		subwrapper = pychan.widgets.HBox(padding=0, opaque=0)
		subwrapper.base_color = _BACKGROUND_COLOR
		for child in data:
			bb = BuildButton(child)
			bb.widget.capture(self.mouse_enter, "mouseEntered")
			bb.widget.capture(self.mouse_exit, "mouseExited")
			bb.widget.capture(self.selected, "mousePressed")		
			subwrapper.addChild(bb.container)
		wrapper.addChild(lbl)
		wrapper.addChild(subwrapper)
		self.widget = wrapper
	def mouse_enter(self, event, widget):
		""" callback for mouse enter on building icons
			e.g. helpful to display a tooltip
		"""
		data = self.__get_data(widget.name)
		if data: print data['tooltip']
		else: print "No tooltip found"
	def mouse_exit(self, event, widget):
		""" callback for mouse exit on building icons 
			e.g. helpful hide a former shown tooltip
		"""
		print "Exited: ", widget.name
	def selected(self, event, widget):
		""" callback for mouse pressed on building icons """
		data = self.__get_data(widget.name)
		if data: print data
		else: print "No data found"
	def __get_data(self, name):
		""" helper to turn widget name into data package 
		
		@type	name:	str
		@param	name:	widget name / building name to fetch associated data
		@type	result:	dict
		@return	result:	data package
		"""
		result = None
		for child in self.data:
			if child['name'] == name:
				result = child
				break
		return result

class Navigation(object):
	""" Special widget: shows vertical aligned buttons, representing
		the available increments		
	"""
	def __init__(self, callback=None, increments=[]):
		""" 
		@type	callback:	function
		@param	callback:	callback for increment selection events
		@type	increments:	list
		@type	increments:	list of increment levels [1,2,3 ...]
		"""
		self.widget = None
		self.callback = callback
		self.create(increments)
		self.active = None
	def create(self, increments=[]):
		""" creates the navigation widget

		@type	increments:	list
		@type	increments:	list of increment levels [1,2,3 ...]		
		"""
		if not increments: return
		self.widget = pychan.loadXML('gui/uh_buildmenu_nav.xml')
		self.widget.base_color = _BACKGROUND_COLOR
		for increment in increments:
			if increment <= 3: level = str(increment-1)
			else: level = str(0)
			nb = NavButton(increment, level, self.selection)
			self.widget.addChild(nb.container)
		
		self.widget.adaptLayout()
		self.widget.show()
	def stop(self):
		""" callback for parent widget """
		self.widget.hide()	
	def selection(self, widget):
		""" callback for selection events
		
		@type	event:	object
		@param	event:	pychan ActionEvent
		@type	widget:	object
		@param	widget:	pychan widget which triggered the event
		"""
		if self.callback is None: return
		clear = False
		if self.active is not None and self.active == widget.name:
			self.active = None
			clear = True
		else:
			self.active = widget.name
		self.callback(widget.name, clear)
	def set_position(self, parent):
		""" update navigation position 
			(pins it centered/left relative to the parent widget) 
		
		@type	parent:	object
		@param	parent:	pychan widget, parent of this navigation
		"""
		pos = parent.position
		size = self.widget.size
		p_size = parent.size
		y = pos[1] + (p_size[1] / 2 - size[1] / 2) / 2
		pos = (pos[0] - size[0], y)
		self.widget.position = pos
	def set_active(self, increment):
		""" set a nav button active, triggers buildview update """
		btn = self.widget.findChild(name=increment)
		btn._setToggled(not btn._isToggled())
		self.selection(btn)		

class BuildMenu(PyChanExample):
	""" Example entry point for B{Navigation} and B{Category} widgets """
	def __init__(self):
		""" """
		super(BuildMenu, self).__init__('gui/uh_buildmenu.xml')
		
	def start(self):
		""" load XML file and setup callbacks """
		self.widget = pychan.loadXML(self.xmlFile)
		self.widget.findChild(name="closeButton").capture(self._stop)
		self.buildview = self.widget.findChild(name="build_view")
		self.header = self.buildview.findChild(name="groupname")
		self.wrapper = self.widget.findChild(name="wrapper")
		
		self.nav = Navigation(self.update, _DATA.keys())
		self.nav.set_position(self.widget)
		
		self.nav.set_active(_INCREMENT_FIRST_SHOW)
		
		self.widget.show()
		
	def _stop(self):
		""" callback for PychanExample (closeButton) """
		self.nav.stop()
		self.stop()
		
	def update(self, increment=None, clear=False):
		""" callback for navigation selection, triggers re-draw of the
			categories
			
		@type	increment:	int
		@param	increment:	selected increment
		@type	clear:	bool
		@param	clear:	flag to just erase drawn categories
		"""
		if increment is None: return
		self.wrapper.removeAllChildren()
		self.header.text = u" "
		
		if clear: return
		
		if increment not in _DATA: return
		data = _DATA[increment]
		
		self.header.text = 10*" " + u"Increment " + str(increment)
		
		for group, childs in data.iteritems():
			category = Category(group, childs['childs'])
			self.wrapper.addChild(category.widget)
		self.wrapper.adaptLayout()
		self.buildview.adaptLayout()
		
			
