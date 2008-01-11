# ###################################################
# Copyright (C) 2008 The OpenAnno Team
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

from openanno.gamecommand import GameCommand
from openanno.buildrootcommand import BuildRootCommand

class BuildGameCommand(GameCommand):
	"""Game command for creating a building"""
	
	def __init__(self, pos, building, playerid):
		self.pos = pos
		self.building = building
		self.playerid = playerid
	
	def build_rootcommands(self):
		return [BuildRootCommand(self.pos, self.building, self.playerid)]
