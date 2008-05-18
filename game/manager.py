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

import timer

class SPManager:
    """The manager class takes care of command issuing to the timermanager,sends tick-packets
    over the network, and syncronisation of network games."""

    def __init__(self, **args):
        """Initialize the Singleplayer Manager
        @var **args: args The arguments to be passed to commands
        """
        self.args = args

    def execute(self, command):
        """Executes a command
        @var command: Command the command to be executed
        """
        command(owner = self.args['player'], **self.args)

class MPManager:
    COMMAND_RATE = 1
    def __init__(self, **args):
        """Initialize the Multiplayer Manager
        @var args: arguments The arguments to be passed to commands, must contain timer, player and players
        """
        self.args = args
        self.timer = args['timer']
        self.timer.add_test(this.can_tick)
        self.timer.add_call(this.tick)
        self.commands = []
        self.packets = {}

    def tick(self, tick):
        """Executes a tick
        @var tick: the
        """
        if tick % self.__class__.COMMAND_RATE == 0:
            if self.packets.has_key(tick):
                self.packets[tick] = {}
            self.packets[tick][self.args['player']] = TickPacket(tick, self.commands)
            self.commands = []
            if self.packets.has_key(tick - 2):
                for p in self.args['players'][(tick - 2) % len(self.args['players']):] + self.args['players'][:((tick - 2) % len(self.args['players'])) - 1]:
                    for c in self.packets[tick - 2][p].commands:
                        c(owner = p, **self.args)

    def can_tick(self, tick):
        return timer.TEST_PASS if ((tick % self.__class__.COMMAND_RATE != 0) or (not self.packets.has_key(tick - 2)) or (len(self.packets[tick - 2]) == len(self.args['players']))) else timer.TEST_RETRY_KEEP_NEXT_TICK_TIME

    def execute(self, command):
        """Executes a command
        @var command: Command the command to be executed
        """
        self.commands.append(command)

class TickPacket:
    def __init__(self, tick, commands):
        self.tick = tick
        self.commands = commands
