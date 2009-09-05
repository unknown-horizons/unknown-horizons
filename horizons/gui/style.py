# ###################################################
# Copyright (C) 2009 The Unknown Horizons Team
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

import fife

STYLES= {
	'default': {
		'default' : {
			'border_size': 2,
			'margins': (0, 0),
			'base_color' : fife.Color(40, 40, 40, 0),
			'foreground_color' : fife.Color(255, 255, 255),
			'background_color' : fife.Color(40, 40, 40, 255),
			'selection_color' : fife.Color(80, 80, 80, 255),
			'font' : 'libertine_small'
		},
		'Button' : {
			'border_size': 1,
			'margins' : (10, 5)
		},
		'CheckBox' : {
			'border_size': 0,
			'background_color' : fife.Color(0, 0, 0, 0)
		},
		'RadioButton' : {
			'border_size': 0,
			'background_color' : fife.Color(0, 0, 0, 0)
		},
		'Label' : {
			'border_size': 0,
			'background_color' : fife.Color(40, 40, 40, 0),
			'font' : 'libertine_small'
		},
		'ClickLabel' : {
			'border_size': 0,
			'font' : 'libertine_small'
		},
		'ListBox' : {
			'border_size': 0,
			'font' : 'libertine_small'
		},
		'Window' : {
			'border_size': 1,
			'margins': (10, 10),
			'titlebar_height' : 30,
			'font' : 'libertine_large',
			'base_color' : fife.Color(60, 60, 60)
		},
		'TextBox' : {
			'font' : 'libertine_small'
		},
		('Container','HBox','VBox') : {
			'opaque' : 0,
			'border_size': 0
		},
		('Icon', 'ImageButton', 'DropDown') : {
			'border_size': 0
		},
		'ScrollArea' : {
			'border_size': 0,
			'horizontal_scrollbar' : 1,
			'base_color' : fife.Color(60, 60, 60),
			'background_color' : fife.Color(60, 60, 60)
		},
		#'TextField' : {
		#	'base_color' : fife.Color(60, 60, 60),
		#	'background_color' : fife.Color(0, 0, 0)
		#}
		'Slider' : {
			'base_color' : fife.Color(80,80,40,50),
		},
	},
	'menu': { #Used in the main menu and game menu
		'default' : {
			'border_size': 0,
			'margins': (0, 0),
			'opaque': 0,
			'base_color' : fife.Color(0, 0, 0, 0),
			'foreground_color' : fife.Color(255, 255, 255),
			'background_color' : fife.Color(0, 0, 0, 0),
			'selection_color' : fife.Color(0, 0, 0, 0),
			'font' : 'libertine_mainmenu'
		},
		'Button' : {
			'border_size': 0,
			'margins' : (10, 5)
		},
		'Label' : {
			'border_size': 0,
			'font' : 'libertine_mainmenu'
		}
	},

    'menu_black': { # style for build menu etc.
		'default' : {
			'border_size': 0,
			'margins': (0,0),
			'opaque': 0,
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(0, 0, 0, 0),
			'selection_color' : fife.Color(0,0,0,0),
			'font' : 'libertine_small_black'
		},
		'Button' : {
			'border_size': 0,
			'margins' : (0,0)
		},
		'Label' : {
            		'margins': (0,0),
			'font' : 'libertine_14_black'
		}
	},

    'resource_bar': {
		'default' : {
			'border_size': 0,
			'margins': (0,0),
			'opaque': 0,
			'base_color' : fife.Color(0, 0, 0, 0),
			'foreground_color' : fife.Color(0, 0, 0, 0),
			'background_color' : fife.Color(0, 0, 0, 0),
			'selection_color' : fife.Color(0, 0, 0, 0),
			'font' : 'libertine_small_black'
		},
		'Button' : {
			'border_size': 0,
			'margins' : (0,0)
		},
		'Label' : {
			'alpha':0,
			'font' : 'libertine_small_black'
		}
	},

    'message_text': {
		'default' : {
			'border_size': 0,
			'margins': (0,0),
			'opaque': 0,
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(0, 0, 0, 0),
			'selection_color' : fife.Color(0,0,0,0),
			'font' : 'libertine_small'
		},
		'Button' : {
			'border_size': 0,
			'margins' : (0,0)
		},
		'Label' : {
			'margins': (0,0),
			'font' : 'libertine_small'
		}
	},

    'cityInfo': { # style for city info
		'default' : {
			'border_size': 0,
			'margins': (0,0),
			'opaque': 0,
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(0, 0, 0, 0),
			'selection_color' : fife.Color(0,0,0,0),
			'font' : 'libertine_large'
		},
		'Button' : {
			'font' : 'libertine_18',
			'border_size': 0,
			'margins' : (0,0)
		},
		'Label' : {
			'font' : 'libertine_18'
		}
	},

    'headline': { # style for headlines
		'default' : {
			'border_size': 0,
			'margins': (0,0),
			'opaque': 0,
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(0, 0, 0, 0),
			'selection_color' : fife.Color(0,0,0,0),
			'font' : 'libertine_headline'
		},
		'Button' : {
			'border_size': 0,
			'margins' : (0,0)
		},
		'Label' : {
			'font' : 'libertine_headline'
		}
	},

    'book': { # style for book widgets
	    'default' : {
			'border_size': 0,
			'margins': (0,0),
			'font' : 'libertine_14_black',
			'foreground_color' : fife.Color(80,80,40),
		},
		'Label' : {
			'font' : 'libertine_14_black',
		},
		'CheckBox' : {
			'selection_color' : fife.Color(255,255,255,200),
			'background_color' : fife.Color(255,255,255,128),
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(80,80,40),
		},
		'DropDown' : {
			'selection_color' : fife.Color(255,255,255,200),
			'background_color' : fife.Color(255,255,255,128),
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(80,80,40),
			'font' : 'libertine_14_black',
		},
		'Slider' : {
			'base_color' : fife.Color(80,80,40,128),
		},
		'TextBox' : {
			'font' : 'libertine_14_black',
			'opaque': 0
		},
		'ListBox' : {
			'background_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(80,80,40),
			'selection_color' : fife.Color(255,255,255,128),
			'font' : 'libertine_14_black',
		},
		'ScrollArea' : {
			'background_color' : fife.Color(255,255,255,64),
			'foreground_color' : fife.Color(80,80,40),
			'base_color' : fife.Color(0,0,0,0),
			'font' : 'libertine_14_black',
			'horizontal_scrollbar' : 0,
		},
		'HBox' : {
			'font' : 'libertine_14_black',
			'foreground_color' : fife.Color(80,80,40),
			'opaque': 0
		},
		'TextField' : {
			'selection_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(255,255,255,64),
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(80,80,40),
			'font' : 'libertine_14_black',
		}
	},

	'tooltip': { # style for headlines
		'default' : {
			'border_size': 0,
			'margins': (0,0),
			'opaque': 0,
			'base_color' : fife.Color(0,0,0,0),
			'foreground_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(0, 0, 0, 0),
			'selection_color' : fife.Color(0,0,0,0),
			'font' : 'libertine_headline'
		},
		'Button' : {
			'border_size': 0,
			'margins' : (0,0)
		},
		'Label' : {
			'font' : 'libertine_tooltip'
		}
	},

}
