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
			'margins': (10, 5),
		},
		('Slider', 'StepSlider'): {
			'base_color': Color(80, 80, 40, 128),
		},
		'CheckBox': {
			'selection_color': Color(255, 255, 255),
			'background_color': Color(255, 255, 255, 96),
			'foreground_color': Color(80, 80, 40),
		},
		'ListBox': {
			'background_color': Color(255, 255, 255, 64),
			'selection_color': Color(255, 255, 255, 160),
		},
		'Label': {
		},
		('Container', 'HBox', 'VBox'): {
			'opaque': 0,
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
			'foreground_color': Color(80, 80, 40),
			'font': '14_black',
		},
		'Label': {
		},
		('Slider', 'StepSlider'): {
			'base_color': Color(90, 90, 40, 96),
		},
		'RadioButton': {
			'foreground_color': Color(80, 80, 40),
			'background_color': Color(255, 255, 255, 96),
		},
		'ListBox': {
			'background_color': Color(0, 0, 0, 0),
			'selection_color': Color(255, 255, 255, 160),
		},
		'TextField': {
			'selection_color': Color(255, 255, 255),
			'background_color': Color(255, 255, 255, 64),
			'base_color': Color(0, 0, 0, 0),
			'horizontal_scrollbar': 0,
		},
		'ScrollArea': {
			'selection_color': Color(255, 255, 255),
			'background_color': Color(255, 255, 255, 64),
			'base_color': Color(90, 90, 40, 96),
			'horizontal_scrollbar': 0,
		},
		('Container', 'HBox', 'VBox'): {
			'opaque': 0,
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
