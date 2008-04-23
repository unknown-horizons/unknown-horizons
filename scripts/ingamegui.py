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
        self.gui['build1'] = pychan.loadXML('content/gui/build_menu/hud_build.xml')
        self.gui['build2'] = pychan.loadXML('content/gui/build_menu/hud_build_2.xml')
        self.gui['build3'] = pychan.loadXML('content/gui/build_menu/hud_build_3.xml')
        self.gui['build4'] = pychan.loadXML('content/gui/build_menu/hud_build_4.xml')
        self.gui['build5'] = pychan.loadXML('content/gui/build_menu/hud_build_5.xml')
        self.gui['build6'] = pychan.loadXML('content/gui/build_menu/hud_build_6.xml')
        self.active_build = self.gui['build1']
        for num in range(1,7):
            self.gui['build'+str(num)].mapEvents({
                'servicesTab' : pychan.tools.callbackWithArguments(self.build_menu_show, 1),
                'residentsTab' : pychan.tools.callbackWithArguments(self.build_menu_show, 2),
                'companiesTab' : pychan.tools.callbackWithArguments(self.build_menu_show, 3),
                'militaryTab' : pychan.tools.callbackWithArguments(self.build_menu_show, 4),
                'streetsTab' : pychan.tools.callbackWithArguments(self.build_menu_show, 5),
                'specialTab' : pychan.tools.callbackWithArguments(self.build_menu_show, 6)
            })
        self.gui['buildinfo'] = pychan.loadXML('content/gui/hud_buildinfo.xml')
        self.gui['chat'] = pychan.loadXML('content/gui/hud_chat.xml')
        self.gui['cityinfo'] = pychan.loadXML('content/gui/hud_cityinfo.xml')
        self.gui['res'] = pychan.loadXML('content/gui/hud_res.xml')
        self.gui['fertility'] = pychan.loadXML('content/gui/hud_fertility.xml')
        self.gui['ship'] = pychan.loadXML('content/gui/hud_ship.xml')
        self.gui['ship'].mapEvents({
            'foundSettelmentButton' : self._ship_build
        })
        self.gui['main'] = pychan.loadXML('content/gui/hud_main.xml')
        self.toggle_visible('main')        
        self.gui['main'].mapEvents({
            'build' : self.build_toggle,
            'zoomIn' : self.game.zoom_in,
            'zoomOut' : self.game.zoom_out,
            'rotateRight' : self.game.rotate_map_right,
            'rotateLeft' : self.game.rotate_map_left,
            'escButton' : self.game.main.gui.show
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

    def build_menu_show(self, num):
        """Shows the selected build menu
        @var num: int with the menu id
        """
        self.active_build.hide()
        self.active_build = self.gui['build' + str(num)]
        self.active_build.show()

    def build_toggle(self):
        if self.active_build.isVisible():
            self.active_build.hide()
        else:
            self.active_build.show()
