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

from fife.fife import Color

STYLES = {
'default': {
		'default': {
			'border_size': 0,
			'margins': (0, 0),
			'base_color': Color(40, 40, 40, 0),
			'foreground_color': Color( 80, 80, 40, 0),
			'background_color': Color(0, 0, 0, 0),
			'selection_color': Color(80, 80, 40, 192),
			'font': '14_black',
		},
		'Button': {
			'background_color': Color(255, 255, 255, 32),
			'foreground_color': Color(80, 80, 40, 192),
			'base_color': Color(80, 80, 40, 64),
			'border_size': 1,
			'margins': (10, 5),
		},
		('Icon', 'ImageButton'): {
			'border_size': 0,
		},
		'CheckBox': {
			'background_color': Color(255, 255, 255, 64),
			'foreground_color': Color(80, 80, 40),
			'base_color': Color(0, 0, 0, 0),
			'font': '14_black',
			'border_size': 0,
		},
		('Slider', 'StepSlider'): {
			'base_color': Color(80, 80, 40, 128),
		},
		'TextField': {
			'selection_color': Color(255, 255, 255),
			'background_color': Color(255, 255, 255, 64),
			'base_color': Color(0, 0, 0, 0),
			'foreground_color': Color(80, 80, 40),
			'font': '14_black',
		},
		'ListBox': {
			'foreground_color': Color(80, 80, 40),
			'selection_color': Color(255, 255, 255, 128),
			'font': '14_black',
		},
		'ScrollArea': {
			'background_color': Color(255, 255, 255, 64),
			'foreground_color': Color(80, 80, 40),
			'base_color': Color(0, 0, 0, 0),
			'font': '14_black',
			'horizontal_scrollbar': 0,
		},
		'RadioButton': {
			'border_size': 0,
		},
		'Label': {
			'border_size': 0,
			'background_color': Color(40, 40, 40, 0),
			'font': '14_black',
		},
		'Window': {
			'border_size': 1,
			'margins': (10, 10),
			'titlebar_height': 30,
			'font': 'large',
			'base_color': Color(60, 60, 60),
		},
		('Container', 'HBox', 'VBox'): {
			'opaque': 0,
			'border_size': 0,
		},
},

'menu': { #Used in the main menu
		'default': {
			'font': 'headline_light',
		},
		'Label': {
			'background_color': Color(0, 0, 0, 102),
			'font': 'mainmenu',
		},
},

'menu_black': { # style for build menu etc.
		'default': {
			'font': '14_black',
		},
		# NOTE: This is a hack to add padding attributs to boxes of this style
		('Container', 'HBox', 'VBox'): {
		},
		# once more, better not ask why this is necessary (#1607)
		# also seems it won't work if just added to the above.
		'CheckBox': {
		},
},

'resource_bar': {
		'default': {
			'font': 'small_black',
		},
},

'city_info': { # style for city info
		'default': {
			'font': '18',
		},
		'Label': {
			#HACK apply defaults to xml widgets without adaptLayout code
		},
},

'headline': { # style for headlines
		'default': {
			'font': 'headline',
		},
		# NOTE: This is a hack to add padding attributs to boxes of this style
		('Container', 'HBox', 'VBox'): {
		},
},

'book': { # style for book widgets
		'default': {
			'border_size': 0,
			'margins': (0, 0),
			'font': '14_black',
			'foreground_color': Color(80, 80, 40),
		},
		'Label': {
			'font': '14_black',
		},
		'DropDown': {
			'selection_color': Color(255, 255, 255, 200),
			'background_color': Color(255, 255, 255, 128),
			'base_color': Color(0, 0, 0, 0),
			'foreground_color': Color(80, 80, 40),
			'font': '14_black',
		},
		('Slider', 'StepSlider'): {
			'base_color': Color(80, 80, 40, 128),
		},
		'ListBox': {
			'background_color': Color(0, 0, 0, 0),
			'foreground_color': Color(80, 80, 40),
			'selection_color': Color(255, 255, 255, 128),
			'font': '14_black',
		},
		'ScrollArea': {
			'background_color': Color(255, 255, 255, 64),
			'foreground_color': Color(80, 80, 40),
			'base_color': Color(0, 0, 0, 0),
			'font': '14_black',
			'horizontal_scrollbar': 0,
		},
		'HBox': {
			'font': '14_black',
			'foreground_color': Color(80, 80, 40),
			'opaque': 0,
		},
		'TextField': {
			'selection_color': Color(255, 255, 255),
			'background_color': Color(255, 255, 255, 64),
			'base_color': Color(0, 0, 0, 0),
			'foreground_color': Color(80, 80, 40),
			'font': '14_black',
		},
		('Container', 'HBox', 'VBox'): {
#			'background_image': ****,
		},
},

'tooltip': { # style for tooltips
		'default': {
			'font': 'tooltip',
		},
		'Label': {
		},
	},

}
