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

class Settlement():
    """The Settlement class describes a settlement and stores all the neccassary information
    like name, current inhabitants, lists of tiles and houses, etc belonging to the village."""
    def __init__(self, island, name):
        """@var island: Island that this settlement is present on
        @var name: the settlements name
        """
        self.island = island
        self.name = name
        self._inhabitants = 0
        self.tiles = [] # List of tiles belonging to the settlement
        self.buildings = [] # List of all the buildings belonging to the settlement

    def add_inhabitants(self, num):
        """Increases the number of inhabitants by num
        @var num: int number of inhabitants to be added
        """
        self._inhabitants += num

    def rem_inhabitants(self, num):
        """Decreases the number of inhabitants by num
        @var num: int number of inhabitants to be removed
        """
        self._inhabitants -= num
