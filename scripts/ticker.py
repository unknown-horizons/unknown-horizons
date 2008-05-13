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

import time

class Ticker():
    """
    The Ticker class manages game-ticks, every tick executes a set of commands in its cache,
    this is espacialy important for multiplayer, to allow syncronous play. 
    Every command the player issues has to pass through the ticker, in order to make it multiplayer
    compatible.
    """
    def __init__(self, tps):
        """@var tps: int times per second the ticker is to tick
        """
        self.tps = tps
        self.itemlist = []  # Stores objects that need to have a tick signaled, these items need to have a tick function, that will be called.
        self.tickid = 0
        self.next_tick = time.time() + 1.0/self.tps

    def check_tick(self):
        """check_tick is called by the engines _pump function to signal a frame idle."""
        if time.time() > self.next_tick:
            self.next_tick += 1.0/self.tps
            self.tick()
            self.check_tick()
   
    def tick(self):
       """Performes the tick, by calling all items tick() function in the itemlist."""
       for item in self.itemlist:
           item.tick(self.tickid)
       self.tickid += 1

    def change_tickrate(self, tps):
        """Changes the engines ticks per second
        @var tps: int ticks per second"""
        self.tps = tps

    def add_tick_item(self, object):
       """Adds an object to the itemlist. 
       @var object: Object that has to have a tick() function, which is called every tick."""
       self.itemlist.append(object)



