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

class SelectionDialog(object):
	"""
	Selection displays a list of options for the user to select from. The result is passed to onSelection.
	list - the list to select from
	onSelection - the function to call when a selection is made. Accepts one argument: an element of the list.
	"""
	def __init__(self, list, onSelection):
		self.list = list
		self._callback = onSelection

		self._widget = pychan.loadXML('gui/selection.xml')

		self._widget.mapEvents({
			'okButton'     : self._selected,
			'cancelButton' : self._widget.hide
		})

		self._widget.distributeInitialData({
			'optionDrop' : list
		})
		self._widget.show()

	def _selected(self):
		selection = self._widget.collectData('optionDrop')
		if selection < 0: return
		self._callback(self.list[selection])
		self._widget.hide()

class ClickSelectionDialog(object):
	"""
	ClickSelection displays a list of options for the user to select from. The result is passed to onSelection.
	Differs from Selection: the selection is made when a list element is clicked, rather than when the box is closed.	
	list - the list to select from
	onSelection - the function to call when a selection is made. Accepts one argument: an element of the list.
	"""
	def __init__(self, list, onSelection):
		self.list = list
		self._callback = onSelection

		self._widget = pychan.loadXML('gui/selection.xml')

		self._widget.mapEvents({
			'okButton'     : self._widget.hide,
			'cancelButton' : self._widget.hide,
			'optionDrop'   : self._selected
		})

		self._widget.distributeInitialData({
			'optionDrop' : list
		})
		self._widget.show()

	def _selected(self):
		selection = self._widget.collectData('optionDrop')
		if selection < 0: return
		self._callback(self.list[selection])
