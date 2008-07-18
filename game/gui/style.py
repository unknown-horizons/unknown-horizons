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

import fife

STYLES= {
	'default': {
		'default' : {
			'border_size': 2,
			'margins': (0,0),
			'base_color' : fife.Color(40,40,40),
			'foreground_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(40,40,40),
			'selection_color' : fife.Color(80,80,80),
			'font' : 'Essays1743-Italic_small'
		},
		'Button' : {
			'border_size': 1,
			'margins' : (10,5)
		},
		'CheckBox' : {
			'border_size': 0,
			'background_color' : fife.Color(0,0,0)
		},
		'RadioButton' : {
			'border_size': 0,
			'background_color' : fife.Color(0,0,0)
		},
		'Label' : {
			'border_size': 0,
			'font' : 'Essays1743-Italic_small'
		},
		'ClickLabel' : {
			'border_size': 0,
			'font' : 'Essays1743-Italic_small'
		},
		'ListBox' : {
			'border_size': 0,
			'font' : 'Essays1743-Italic_small'
		},
		'Window' : {
			'border_size': 1,
			'margins': (10,10),
			'titlebar_height' : 30,
			'font' : 'Essays1743-Italic_large',
			'base_color' : fife.Color(60,60,60)
		},
		'TextBox' : {
			'font' : 'Essays1743-Italic_small'
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
			'base_color' : fife.Color(60,60,60),
			'background_color' : fife.Color(60,60,60)
		},
		'TextField' : {
			'base_color' : fife.Color(60,60,60),
			'background_color' : fife.Color(60,60,60)
		}
	},
	'menu': { #Used in the main menu and game menu
		'default' : {
			'border_size': 0,
			'margins': (0,0),
			'opaque': 0,
			'base_color' : fife.Color(0,0,0),
			'foreground_color' : fife.Color(255,255,255),
			'background_color' : fife.Color(0,0,0),
			'selection_color' : fife.Color(80,80,80),
			'font' : 'Essays1743-Italic_small'
		},
		'Button' : {
			'border_size': 0,
			'margins' : (10,5)
		},
		'Label' : {
			'border_size': 0,
			'font' : 'Essays1743-Italic_small'
		}
	}
}
