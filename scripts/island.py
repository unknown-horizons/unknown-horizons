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

class Island(self):
    """The Island class represents an Island by keeping a list of all instances on the map, 
    that belong to the island. The island variable is also set on every instance that belongs
    to an island, making it easy to determine to which island the instance belongs, when
    selected.
    An Island instance is created at map creation, when all tiles are added to the map.
    """
    def __init__(self, id):
        """@var id: int containing the islands unique id
        """
        self._instance_list = [] # Do not edit this list manually, always use the add_tile() and remove_tile() functions.
        self.id = id

    def add_tile(self, tile):
        """Adds a tile to the island's instance_list and sets the tiles island.
        @var tile: fife.instance of the tile that is to be added.
        """
        self._instance_list.append(tile)
        tile.island = self

    def remove_tile(self, tile):
        """Removes a tile from the island's instance_list and removes the tiles island variable.
        @var tile: fife.instance of the tile that is to be removed.
        """
        self._instace_list.remove(tile)
        tile.island = None
