# ###################################################
# Copyright (C) 2008-2017 The Unknown Horizons Team
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

from fife.fifechan import Color

BROWN = {64: Color(80, 80, 40, 64),
         96: Color(80, 80, 40, 96),
         128: Color(80, 80, 40, 128),
         192: Color(80, 80, 40, 192),
         255: Color(80, 80, 40, 255),
}

WHITE = {32: Color(255, 255, 255, 32),
         64: Color(255, 255, 255, 64),
         96: Color(255, 255, 255, 96),
         160: Color(255, 255, 255, 160),
         255: Color(255, 255, 255, 255),
}

NOTHING = Color(0, 0, 0, 0)

STYLES = {
'default': {
		'default': {
			'background_color': NOTHING,
			'base_color': NOTHING,
			'foreground_color': BROWN[255],
			'selection_color': BROWN[192],
			'border_size': 0,
			'margins': (0, 0),
			'font': 'default',
			'vertical_scrollbar': 1,
			'horizontal_scrollbar': 0,
		},
		'Button': {
			'base_color': BROWN[64],
			'foreground_color': BROWN[192],
			'margins': (10, 5),
		},
		#TODO combine the following two after the tuple notation bug is fixed:
		# http://github.com/fifengine/fifengine/issues/656
		'CheckBox': {
			'background_color': WHITE[96],
		},
		'RadioButton': {
			'background_color': WHITE[96],
		},
		'ListBox': {
			'selection_color': WHITE[160],
		},
		'ScrollArea': {
			'selection_color': WHITE[255],
			'background_color': WHITE[64],
			'base_color': BROWN[64],
		},
		#TODO combine the following two after the tuple notation bug is fixed
		'Slider': {
			'base_color': BROWN[96],
		},
		'StepSlider': {
			'base_color': BROWN[96],
		},
		'TextField': {
			'selection_color': BROWN[96],
			'background_color': WHITE[64],
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
			'font': 'resourcebar',
		},
},

'headline': { # style for headlines
		'default': {
			'font': 'headline',
		},
},

'transparent': { # style for transparent widgets
		'default': {
			'background_color': Color(0, 0, 0, 0),
		},
		'ScrollArea': {
			'background_color': Color(0, 0, 0, 0),
		},
},
}
