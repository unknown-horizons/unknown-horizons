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

from openanno.command import Command

class GameCommand(Command):
	"""Base class for game commands
	Game commands are containers for the metadata needed to
	commence an action.
	Their main purpose is to be serializable so that they
	can be sent over the network, where the server converts
	them to root commands then.
	If the game is running locally, they can be converted to
	root commands in place."""
	
	def __init__(self):
		Command.__init__(self)
		
	def build_rootcommands(self):
		"""Build a series of root commands representing this action"""
		raise Exception("Virtual function!")
	
	# Looks a bit hackish... Does this always work?
	def can_execute(self):
		for rootcommand in self.build_rootcommands():
			if not rootcommand.can_execute():
				return False
		return True
