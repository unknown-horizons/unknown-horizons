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

BROWN = { 64: Color(80, 80, 40,  64),
          96: Color(80, 80, 40,  96),
         128: Color(80, 80, 40, 128),
         192: Color(80, 80, 40, 192),
         255: Color(80, 80, 40, 255),
}

WHITE = { 32: Color(255, 255, 255,  32),
          64: Color(255, 255, 255,  64),
          96: Color(255, 255, 255,  96),
         160: Color(255, 255, 255, 160),
         255: Color(255, 255, 255, 255),
}

NOTHING = Color(0, 0, 0, 0)

STYLES = {
'default': {
		'default': {
			'border_size': 0,
			'margins': (0, 0),
			'selection_color': BROWN[192],
			'background_color': NOTHING,
			'foreground_color': BROWN[255],
			'base_color': NOTHING,
			'font': '14_black',
		},
		'Button': {
			'background_color': WHITE[32],
			'foreground_color': BROWN[192],
			'base_color': BROWN[64],
			'margins': (10, 5),
		},
		'RadioButton': {
			'foreground_color': BROWN[255],
			'background_color': WHITE[96],
		},
		('Slider', 'StepSlider'): {
			'base_color': BROWN[96],
		},
		'CheckBox': {
			'selection_color': WHITE[255],
			'background_color': WHITE[96],
			'foreground_color': BROWN[255],
		},
		'ListBox': {
			'selection_color': WHITE[160],
		},
		'TextField': {
			'selection_color': WHITE[255],
			'background_color': WHITE[64],
			'horizontal_scrollbar': 0,
		},
		'ScrollArea': {
			'selection_color': WHITE[255],
			'background_color': WHITE[64],
			'base_color': BROWN[96],
			'horizontal_scrollbar': 0,
		},
		('Container', 'HBox', 'VBox'): {
		},
		'Label': {
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


'tooltip': { # style for tooltips
		'default': {
			'font': 'tooltip',
		},
		'Label': {
		},
	},

}
