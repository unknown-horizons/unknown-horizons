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
import settings
import sys
import os
def _jp(path):
    return os.path.sep.join(path.split('/'))

_paths = (settings.path + 'engine/swigwrappers/python', settings.path + 'engine/extensions')

for p in _paths:
    if p not in sys.path:
        sys.path.append(_jp(p)) 

import fife

# 
# This is the basic OpenAnno stylesheet
# 


STYLES= {
    'default': {
        'default' : {
            'border_size': 2,
            'margins': (0,0),
            'base_color' : fife.Color(40,40,40),
            'foreground_color' : fife.Color(255,255,255),
            'background_color' : fife.Color(40,40,40),
            'font' : 'samanata_small'
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
            'font' : 'samanata_small'
        },
        'ClickLabel' : {
            'border_size': 0,
            'font' : 'samanata_small'
        },
        'ListBox' : {
            'border_size': 0,
            'font' : 'samanata_small'
        },
        'Window' : {
            'border_size': 1,
            'margins': (10,10),
            'titlebar_height' : 30,
            'font' : 'samanata_large'
        },
        'TextBox' : {
            'font' : 'samanata_small'
        },
        ('Container','HBox','VBox') : {
            'border_size': 0,
        }
    },
    'menu': { #Used in the main menu and game menu
        'default' : {
            'border_size': 0,
            'margins': (0,0),
            'base_color' : fife.Color(0,0,0),
            'foreground_color' : fife.Color(255,255,255),
            'background_color' : fife.Color(0,0,0),
            'font' : 'samanata_small'
        },
        'Button' : {
            'border_size': 0,
            'margins' : (10,5)
        },
        'Label' : {
            'border_size': 0,
            'font' : 'samanata_small'
        }
    }
}
