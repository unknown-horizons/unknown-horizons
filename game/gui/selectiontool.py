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

from cursortool import CursorTool
from ..world.units.ship import Ship
from ..command.unit import Move
import time
import fife
import math

class SelectionTool(CursorTool):
    """The Selectiontool is used to select instances on the game screen.
    @var game: the main game Instance
    """
    def __init__(self, game):
        CursorTool.__init__(self,  game.eventmanager)
        self.game = game
        self.last_moved = 0

def select_unit(self):
        """Runs neccesary steps to select a unit."""
        self.game.selected_instance.object.say(str(self.game.selected_instance.health) + '%', 0) # display health over selected ship
        self.game.outline_renderer.addOutlined(self.game.selected_instance.object, 255, 255, 255, 1)
        if self.game.selected_instance.__class__ is Ship:
            self.game.ingame_gui.gui['ship'].show() #show the gui for ships

    def deselect_unit(self):
        """Runs neccasary steps to deselect a unit."""
        if self.game.selected_instance.__class__ is Ship:
            self.game.ingame_gui.toggle_visible('ship') # hide the gui for ships
            self.game.selected_instance.object.say('') #remove status of last selected unit
            self.game.outline_renderer.removeAllOutlines() # FIXME: removeOutlined(self.selected_instance.object) doesn't work

    def mousePressed(self, evt):
        clickpoint = fife.ScreenPoint(evt.getX(), evt.getY())
        cam = self.game.view.cam
        if (evt.getButton() == fife.MouseEvent.LEFT):
            instances = cam.getMatchingInstances(clickpoint, self.game.layers['land'])
            if instances: #check if clicked point is a unit
                selected = instances[0]
                if self.game.selected_instance:
                    if self.game.selected_instance.object.getFifeId() != selected.getFifeId():
                        self.deselect_unit()
                if selected.getFifeId() in self.game.instance_to_unit:
                    self.game.selected_instance = self.game.instance_to_unit[selected.getFifeId()]
                    self.select_unit()
                else:
                    self.game.selected_instance = None
            elif self.game.selected_instance: # remove unit selection
                self.deselect_unit()
                self.game.selected_instance = None

        elif (evt.getButton() == fife.MouseEvent.RIGHT):
            if self.game.selected_instance: # move unit
                if self.game.selected_instance.type == 'ship':
                    target_mapcoord = cam.toMapCoordinates(clickpoint, False)
                    target_mapcoord.z = 0
                    l = fife.Location(self.game.layers['land'])
                    l.setMapCoordinates(target_mapcoord)
                    self.game.manager.execute(Move(self.game.selected_instance.object.getFifeId(), target_mapcoord.x, target_mapcoord.y, 'land'))
        evt.consume()

    def mouseMoved(self, evt):
        # Mouse scrolling
        mousepoint = fife.ScreenPoint(evt.getX(), evt.getY())
        if time.time() > self.last_moved+0.05:  # Make sure the screen doesn't move to rapidly.
            self.last_moved = time.time()
            if mousepoint.x < 50:
                self.game.view.scroll(-1, 0)
            if mousepoint.y < 50:
                self.game.view.scroll(0, -1)
            if mousepoint.x > (self.game.view.cam.getViewPort().right()-50):
                self.game.view.scroll(1, 0)
            if mousepoint.y > (self.game.view.cam.getViewPort().bottom()-50):
                self.game.view.scroll(0, 1)
        evt.consume()

    def mouseWheelMovedUp(self, evt):
        self.game.view.zoom_in()
        evt.consume()

    def mouseWheelMovedDown(self, evt):
        self.game.view.zoom_out()
        evt.consume()

    def __del__(self):
        CursorTool.__del__(self)
