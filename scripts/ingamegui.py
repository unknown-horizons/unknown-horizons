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

import pychan
from units.house import House

class IngameGui():
    """Class handling all the ingame gui events."""
    def __init__(self, game):
        self.game = game
        self.status = pychan.loadXML('content/gui/status.xml')
        self.status.show()
        self.main_gui = pychan.loadXML('content/gui/hud_main.xml')
        self.main_gui.show()
        self.build = pychan.loadXML('content/gui/hud_build.xml')
        self.build.show()
        self.buildinfo = pychan.loadXML('content/gui/hud_buildinfo.xml')
        self.buildinfo.show()
        self.chat = pychan.loadXML('content/gui/hud_chat.xml')
        self.chat.show()
        self.cityinfo = pychan.loadXML('content/gui/hud_cityinfo.xml')
        self.cityinfo.show()
        self.res = pychan.loadXML('content/gui/hud_res.xml')
        self.res.show()
        self.fertility = pychan.loadXML('content/gui/hud_fertility.xml')
        self.fertility.show()
        self.ship = pychan.loadXML('content/gui/hud_ship.xml')
        self.ship.mapEvents({
            'build' : self._ship_build
        })


    def status_set(self, label, value):
        """Sets a value on the status bar.
        @var label: str containing the name of the label to be set.
        @var value: value the Label is to be set to.
        """
        foundlabel = self.status.findChild(name=label)
        foundlabel._setText(value)
        foundlabel.resizeToContent()
        self.status.resizeToContent()

    def _ship_build(self):
        """Calls the Games build_object class."""
        self.ship.hide()
        self.game.build_object('2', self.game.layers['units'], House, 0, 0, self.game.get_tiles_in_radius(self.game.layers['land'], 6, self.game.selected_instance.object.getLocation()))

