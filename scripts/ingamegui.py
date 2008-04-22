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
        self.gui = {}
        self.gui['status'] = pychan.loadXML('content/gui/status.xml')
        self.gui['main'] = pychan.loadXML('content/gui/hud_main.xml')
        self.toggle_visible('main')        
        self.gui['main'].mapEvents({
            'build' : self.toggle_build,
            'zoomIn' : self.game.zoom_in,
            'zoomOut' : self.game.zoom_out,
            'rotateRight' : self.game.rotate_map_right,
            'rotateLeft' : self.game.rotate_map_left,
            'escButton' : self.game.main.gui.show
        })
        self.gui['build'] = pychan.loadXML('content/gui/hud_build.xml')
        self.gui['buildinfo'] = pychan.loadXML('content/gui/hud_buildinfo.xml')
        self.gui['chat'] = pychan.loadXML('content/gui/hud_chat.xml')
        self.gui['cityinfo'] = pychan.loadXML('content/gui/hud_cityinfo.xml')
        self.gui['res'] = pychan.loadXML('content/gui/hud_res.xml')
        self.gui['fertility'] = pychan.loadXML('content/gui/hud_fertility.xml')
        self.gui['ship'] = pychan.loadXML('content/gui/hud_ship.xml')
        self.gui['ship'].mapEvents({
            'foundSettelmentButton' : self._ship_build
        })


    def status_set(self, label, value):
        """Sets a value on the status bar.
        @var label: str containing the name of the label to be set.
        @var value: value the Label is to be set to.
        """
        foundlabel = self.gui['status'].findChild(name=label)
        foundlabel._setText(value)
        foundlabel.resizeToContent()
        self.gui['status'].resizeToContent()

    def _ship_build(self):
        """Calls the Games build_object class."""
        self.gui['ship'].hide()
        self.game.selected_instance.object.say('')
        self.game.build_object('2', self.game.layers['units'], House, 0, 0, self.game.get_tiles_in_radius(self.game.layers['land'], 6, self.game.selected_instance.object.getLocation()))

    def toggle_visible(self, guiname):
        """Toggles whether a gui is visible or not.
        @var guiname: str with the guiname.
        """
        if self.gui[guiname].isVisible():
            self.gui[guiname].hide()
        else:
            self.gui[guiname].show()

    def toggle_build(self):
        """Toggles the build menu on and off"""
        self.toggle_visible('build')

    def toggle_(self):
        """Toggles the build menu on and off"""
        self.toggle_visible('build')

