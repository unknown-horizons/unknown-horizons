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

def find_available_languages():
    alternatives = ('po',
                    '/usr/share/locale',
                    '/usr/share/games/locale',
                    '/usr/local/share/locale',
                    '/usr/local/share/games/locale')
    
    import os

    erg = []

    for i in alternatives:
        found = os.walk(i)
        for j in found:
            if 'unknownhorizons.mo' in j[2]:
                splited = j[0].split(os.sep)
                erg.append( (splited[-2], os.sep.join(splited[:-2])))
    
    return erg
  
    
