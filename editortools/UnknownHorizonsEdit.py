# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2010 by the FIFE team
#  http://www.fifengine.de
#  This file is part of FIFE.
#
#  FIFE is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

""" a tool to load unknown-horizons maps etc """

import scripts
import scripts.plugin as plugin

class UnknownHorizonsEdit(plugin.Plugin):
	"""
	"""
	def __init__(self):
		self._enabled = False

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
