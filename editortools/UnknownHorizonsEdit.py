# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
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

""" a tool to load unknown-horizons maps etc """

import scripts
import scripts.plugin as plugin
import scripts.editor

import os
import sys
# Allow horizons package to be imported, this is probably not a very good way
# to do this
sys.path.append( os.path.join( os.getcwd(), '..' ) )
from horizons.util import ActionSetLoader
from horizons.util import TileSetLoader
from horizons.util import UHAnimationLoader

class UnknownHorizonsEdit(plugin.Plugin):
	"""
	"""
	def __init__(self):
		self._editor = scripts.editor.getEditor()
		self._enabled = False

		# Load action sets
		path = os.path.abspath(os.path.join('..', 'content', 'gfx'))
		TileSetLoader._find_action_sets(path)
		self._tile_sets = TileSetLoader.get_sets()

		# load graphics into imagepool
		uhloader = UHAnimationLoader(self._editor.engine.getImagePool())
		print uhloader


	def enable(self):
		if self._enabled:
			return

		# Do implemenent

		self._enabled = True

	def disable(self):
		if not self._enabled:
			return

		self._enabled = False

	def isEnabled(self):
		return self._enabled

	def getName(self):
		return "Unknown Horizons Edit"

	#--- These are not so important ---#
	def getAuthor(self):
		return "Unknown Horizons Team"

	def getDescription(self):
		return ""

	def getLicense(self):
		return "GPLv2"

	def getVersion(self):
		return "0.1"
