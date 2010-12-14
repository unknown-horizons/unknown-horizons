# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2005-2009 by the FIFE team
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

from fife.extensions import pychan
import fife.extensions.pychan.widgets as widgets

class ErrorDialog(object):
	"""
	Shows a dialog with an error message.
	"""
	def __init__(self, message):
		self._widget = pychan.loadXML('gui/error.xml')

		self._widget.mapEvents({
			'okButton'     : self._widget.hide
		})

		self._widget.distributeInitialData({
			'message' : message
		})
		self._widget.show()
		self._widget.adaptLayout() # Necessary to make scrollarea work properly

