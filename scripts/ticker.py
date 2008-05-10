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

import threading

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
        self.ticklist = {}
        self.process = 0
        self.add_tick()
        self.cur_tick = self.ticklist[self.process]
        self.tick()

    def tick(self):
        """Performes the tick and starts the next tick"""
        # Add check here if all older ticks have been started by all players
        tick = self.cur_tick
        self.process += 1
        self.add_tick()
        self.cur_tick = self.ticklist[self.process]
        timer = threading.Timer(1.0/self.tps, self.tick)
        timer.start()
        for commandbatch in tick.commandlist:
            print 'Running commandlist of tick:', tick.id
            commandbatch[0](commandbatch[1]) # Execute all commands
        del self.ticklist[self.cur_tick.id]
                
    def add_tick(self, offset=0):
        """Adds a tick to the ticklist
        @var offset: int number ticks ahead the tick is to be placed. offset of 50 will result in a tick that is run after 50 ticks."""
        if (self.process+offset) not in self.ticklist:
            self.ticklist[self.process+offset] = Tick(self.process+offset)
        else:
            pass

    def add_command(self, callback, args=[], tickoffset=0):
        """
        Adds command to the Ticks commandlist.
        @var callback: function that is to be called.
        @var args: list of arguments for the callback function.
        @var tickoffset: int number ticks ahead the command is to be added.
        """
        if (self.process+tickoffset) not in self.ticklist:
            self.add_tick(tickoffset)
        print self.ticklist[self.process+tickoffset]
        self.ticklist[self.process+tickoffset].add_command(callback, args)

    def change_tichrate(self, tps):
        """Changes the engines ticks per second
        @var tps: int ticks per second"""
        self.tps = tps 

class Tick():
    """
    The Tick class represents a single tick and stores all the commends that are to be executed.
    """
    def __init__(self, id):
        """
        @var id: int unique tick id.
        """
        self.id = id
        self.commandlist = [] # List of lists: [ command, args ]

    def add_command(self, callback, args=[]):
        """
        Adds command to the Ticks commandlist.
        @var callback: function that is to be called.
        @var args: list of arguments for the callback function.
        """
        self.commandlist.append([callback, args])
        print 'Added command to tick:', self.id
