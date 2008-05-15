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

class SPManager:
    """The manager class takes care of command issuing to the timermanager,sends tick-packets
    over the network, and syncronisation of network games."""

    def __init__(self, game):
        self.cmdbatchlist =  {}
        self.process = 0
        self.add_batch()
        self.game = game

    def tick(self, id):
        """Performes the tick and starts the next tick
        @var id: tick id"""
        # NOTE: Add check here if all older ticks have been started by all players
        cmdbatch = self.cmdbatchlist[id]
        self.add_batch()
        for commandbatch in cmdbatch.cmdlist:
            print 'Running commandlist of tick:', cmdbatch.id
            commandbatch.__call__(self.game) # Execute all commands
        del self.cmdbatchlist[cmdbatch.id]

    def test(self, id):
        """Used to check if the manager is ready for the next tick."""
        return 0
                
    def add_batch(self):
        """Adds a CmdBatch to the cmdbatchlist"""
        self.cmdbatchlist[self.process] = CmdBatch(self.process)
        self.process += 1

    def add_action(self, callback_class):
        """
        Adds command to the Ticks commandlist.
        @var callback_class: lambda of the function that is to be called with arguments [lambda: foo(2, 3, 4)].
        @var tickoffset: int number ticks ahead the command is to be added.
        """
        self.cmdbatchlist[self.process-1].add_action(callback_class)

class CmdBatch():
    """
    The CmdBatch class stores all the commends that are to be executed on a single game tick.
    """
    def __init__(self, id):
        """
        @var id: int unique tick id.
        """
        self.id = id
        self.cmdlist = [] # List of command classes

    def add_action(self, callback_class):
        """
        Adds command to the CmdBatch's commandlist.
        @var callback_class: class that is to be called.
        """
        self.cmdlist.append(callback_class)
        print 'Added commandclass to tick:', self.id
